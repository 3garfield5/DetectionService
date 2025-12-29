import os
import subprocess
import sys
from pathlib import Path

VIDEO = Path(__file__).with_name("test.mp4")

RTSP_URL = os.getenv("RTSP_URL")

# ====== настройки качества ======
SCALE_W = int(os.getenv("EMULATOR_SCALE_W", "1280"))   # 1920/1280/960/640
FPS = int(os.getenv("EMULATOR_FPS", "15"))             # 25/15/10

# битрейт видео (H.264)
BITRATE = os.getenv("EMULATOR_BITRATE", "1500k")       # 2500k/1500k/900k
MAXRATE = os.getenv("EMULATOR_MAXRATE", BITRATE)
BUFSIZE = os.getenv("EMULATOR_BUFSIZE", "3000k")       
GOP = int(os.getenv("EMULATOR_GOP", str(FPS * 2)))      # keyframe каждые ~2 сек
# ===============================================

if not VIDEO.exists():
    print(f"[ERR] Видео {VIDEO} не найдено", file=sys.stderr)
    sys.exit(1)

vf = f"scale={SCALE_W}:-2,fps={FPS}"

cmd = [
    "ffmpeg",
    "-re",
    "-stream_loop", "-1",
    "-i", str(VIDEO),

    # фильтры: масштаб + FPS
    "-vf", vf,

    # H264 настройки
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-tune", "zerolatency",
    "-pix_fmt", "yuv420p",

    # bitrate control
    "-b:v", BITRATE,
    "-maxrate", MAXRATE,
    "-bufsize", BUFSIZE,

    # GOP / keyframes (помогает стабильности)
    "-g", str(GOP),
    "-keyint_min", str(GOP),
    "-sc_threshold", "0",

    "-loglevel", "error",

    "-f", "rtsp",
    "-rtsp_transport", "tcp",
    RTSP_URL,
]

print("[INFO] Запускаю эмулятор камеры:")
print("       ", " ".join(cmd))

proc = subprocess.Popen(cmd)

try:
    proc.wait()
except KeyboardInterrupt:
    print("[INFO] Останавливаю эмулятор...")
    proc.terminate()
    proc.wait()
