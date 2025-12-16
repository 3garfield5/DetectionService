# ml_service/yolo_stream.py
import time
import base64
from datetime import datetime, timezone

import cv2
import numpy as np
import requests
from ultralytics import YOLO

# ==== НАСТРОЙКИ ====

RTSP_URL = "rtsp://localhost:8554/live_stream?tcp"
BACKEND_URL = "http://127.0.0.1:8000/internal/events"
MODEL_PATH = "yolo11n.pt"

PERSON_CLASS = 0

LEFT_OBJECT_CLASSES = set([x for x in range(80) if x not in [0, 2, 3, 4, 5, 6, 7]])

MAX_COORD_DIST = 40

APPEAR_WINDOW = 12
MIN_INITIAL_IOU = 0.05
LEFT_SECONDS = 4

OBJ_CONF_THR = 0.4
MIN_OBJ_AREA_FRAC = 0.0005
MAX_OBJ_AREA_FRAC = 0.2

TARGET_FPS = 10
BRIGHTEN = False

# =====================

def frame_to_base64(frame, quality=60):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    ok, buffer = cv2.imencode(".jpg", frame, encode_param)
    if not ok:
        raise RuntimeError("Не удалось закодировать кадр в JPEG")
    return base64.b64encode(buffer).decode("utf-8")

def send_event(frame: np.ndarray, bbox, owner_id=None, object_id=None):
    x1, y1, x2, y2 = bbox
    timestamp = datetime.now(timezone.utc).isoformat()

    payload = {
        "timestamp": timestamp,
        "owner_id": int(owner_id) if owner_id is not None else None,
        "object_id": int(object_id) if object_id is not None else None,
        "bbox": [float(x1), float(y1), float(x2), float(y2)],
        "frame_snapshot_base64": frame_to_base64(frame),
    }

    try:
        resp = requests.post(BACKEND_URL, json=payload, timeout=5)
        resp.raise_for_status()
        print("[OK] Event sent:", resp.json())
    except Exception as e:
        print("[ERR] Failed to send event:", e)


def bbox_center(xyxy):
    x1, y1, x2, y2 = xyxy
    return (0.5 * (x1 + x2), 0.5 * (y1 + y2))


def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    inter = max(0, xB - xA) * max(0, yB - yA)
    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    union = areaA + areaB - inter
    return inter / union if union > 0 else 0


def brighten_frame(frame, factor=1.35):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(float)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
    hsv = hsv.astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


class TrackedObject:
    def __init__(self, tid, bbox, class_id, frame_idx):
        self.tid = tid
        self.bbox = bbox
        self.class_id = class_id

        self.appeared_frame = frame_idx
        self.last_seen_frame = frame_idx

        self.owner_id = None
        self.last_owner_frame = None

        self.last_person_near_frame = None

        self.flagged_left = False


def run_on_stream(
    stream_url: str,
    model_path: str = MODEL_PATH,
    target_fps: int = TARGET_FPS,
    brighten: bool = BRIGHTEN,
):
    print(f"[INFO] Loading YOLO model: {model_path}")
    model = YOLO(model_path)

    print(f"[INFO] Connecting to stream: {stream_url}")
    cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("[ERR] Не удалось открыть поток")
        return

    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    if orig_fps and orig_fps > 0 and target_fps:
        ratio = orig_fps / target_fps
    else:
        ratio = 1
    frame_step = max(1, int(ratio))

    tracked_objects: dict = {}
    frame_idx = 0
    start_time = time.time()

    track_classes = list(LEFT_OBJECT_CLASSES | {PERSON_CLASS})

    threshold_frames = int(LEFT_SECONDS * target_fps)

    while True:
        ret = cap.grab()
        if not ret:
            print("[WARN] Кадр не прочитан, ждём...")
            time.sleep(0.05)
            continue

        if frame_idx % frame_step != 0:
            frame_idx += 1
            continue

        ret, frame = cap.retrieve()
        if not ret:
            print("[WARN] Не удалось получить кадр после grab()")
            time.sleep(0.05)
            frame_idx += 1
            continue

        if brighten:
            frame = brighten_frame(frame, factor=1.4)

        frame_h, frame_w = frame.shape[:2]
        frame_area = frame_h * frame_w

        results = model.track(
            frame,
            persist=True,
            tracker="botsort.yaml",
            verbose=False,
            conf=OBJ_CONF_THR,
            classes=track_classes,
        )

        if not results:
            frame_idx += 1
            continue

        result = results[0]
        rboxes = getattr(result, "boxes", None)
        if rboxes is None:
            frame_idx += 1
            continue

        xyxy_t = getattr(rboxes, "xyxy", None)
        cls_t = getattr(rboxes, "cls", None)
        ids_t = getattr(rboxes, "id", None)
        conf_t = getattr(rboxes, "conf", None)

        if xyxy_t is None or cls_t is None:
            frame_idx += 1
            continue

        xyxy_np = xyxy_t.cpu().numpy().astype(float)
        cls_np = cls_t.cpu().numpy().astype(int)

        if conf_t is not None:
            conf_np = conf_t.cpu().numpy().astype(float)
        else:
            conf_np = np.ones(len(xyxy_np), dtype=float)

        if ids_t is not None:
            ids_np = ids_t.cpu().numpy()
            ids_np = [-1 if v is None else int(v) for v in ids_np]
        else:
            ids_np = [-1] * len(xyxy_np)

        persons = []
        objects = []

        for i in range(len(xyxy_np)):
            xy = tuple(xyxy_np[i].tolist())
            class_id = cls_np[i]
            tid = ids_np[i]
            conf = float(conf_np[i])

            if conf < OBJ_CONF_THR:
                continue

            box_area = (xy[2] - xy[0]) * (xy[3] - xy[1])
            area_frac = box_area / frame_area

            if class_id == PERSON_CLASS:
                persons.append({"tid": tid, "bbox": xy, "center": bbox_center(xy)})
            elif class_id in LEFT_OBJECT_CLASSES:
                if not (MIN_OBJ_AREA_FRAC <= area_frac <= MAX_OBJ_AREA_FRAC):
                    continue
                objects.append({"tid": tid, "bbox": xy, "class": class_id})

        def find_existing_object(bbox, class_id):
            c = bbox_center(bbox)
            best_tid = None
            best_dist = 10**9
            for tid_, obj in tracked_objects.items():
                if obj.class_id != class_id:
                    continue
                prev_c = bbox_center(obj.bbox)
                d = np.linalg.norm(np.array(c) - np.array(prev_c))
                if d < MAX_COORD_DIST and d < best_dist:
                    best_dist = d
                    best_tid = tid_
            return best_tid

        now = frame_idx

        # обновляем/создаём объекты
        for obj in objects:
            raw_tid = obj["tid"]
            bbox = obj["bbox"]
            class_id = obj["class"]

            if raw_tid != -1 and raw_tid in tracked_objects:
                tobj = tracked_objects[raw_tid]
                tobj.bbox = bbox
                tobj.last_seen_frame = now
                continue

            match_tid = find_existing_object(bbox, class_id)
            if match_tid is not None:
                tobj = tracked_objects[match_tid]
                tobj.bbox = bbox
                tobj.last_seen_frame = now
                continue

            new_tid = raw_tid if raw_tid != -1 else f"ghost_{now}_{hash(bbox)}"
            tracked_objects[new_tid] = TrackedObject(new_tid, bbox, class_id, now)

        # обновляем last_person_near_frame
        for p in persons:
            for tid_, obj in tracked_objects.items():
                if obj.flagged_left:
                    continue
                i = iou(p["bbox"], obj.bbox)
                if i > 0.05:
                    obj.last_person_near_frame = now

        # обновляем owner_id и last_owner_frame
        for tid_, obj in tracked_objects.items():
            if obj.flagged_left:
                continue

            best_iou = 0.0
            best_person_id = None
            for p in persons:
                i = iou(p["bbox"], obj.bbox)
                if i > best_iou:
                    best_iou = i
                    best_person_id = p["tid"]

            if obj.owner_id is None:
                if best_iou > MIN_INITIAL_IOU and abs(obj.appeared_frame - now) <= APPEAR_WINDOW:
                    # владелец — конкретный трек персоны (int), если есть
                    obj.owner_id = best_person_id if best_person_id != -1 else None
                    obj.last_owner_frame = now

                elif obj.last_person_near_frame is not None:
                    if now - obj.last_person_near_frame <= APPEAR_WINDOW:
                        # неизвестный владелец, но явно был рядом человек недавно
                        obj.owner_id = -1  # спец-значение "unknown"
                        obj.last_owner_frame = now
            else:
                if best_iou > 0.05:
                    obj.last_owner_frame = now

        current_time = time.time()

        left_events = []

        for tid_, obj in list(tracked_objects.items()):
            if obj.flagged_left:
                continue
            if obj.owner_id is None:
                continue
            if obj.last_owner_frame is None:
                continue

            no_owner_for = now - obj.last_owner_frame
            not_seen_for = now - obj.last_seen_frame

            if no_owner_for > threshold_frames and not_seen_for <= threshold_frames:
                obj.flagged_left = True
                left_events.append(obj)

            if not_seen_for > 5 * threshold_frames:
                del tracked_objects[tid_]

        # отправляем события сразу
        if left_events:
            rendered = frame.copy()
            for obj in left_events:
                x1, y1, x2, y2 = map(int, obj.bbox)
                cv2.rectangle(rendered, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(
                    rendered,
                    f"LEFT {obj.class_id}",
                    (x1, max(0, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 255),
                    2,
                )

                print(
                    f"[LEFT] t={current_time - start_time:.1f}s "
                    f"frame={now} tid={obj.tid} class={obj.class_id}"
                )

                send_event(
                    frame=rendered,
                    bbox=obj.bbox,
                    owner_id=obj.owner_id,
                    object_id=obj.class_id,
                )

        frame_idx += 1

    cap.release()


def main():
    run_on_stream(RTSP_URL, MODEL_PATH, TARGET_FPS, BRIGHTEN)


if __name__ == "__main__":
    main()
