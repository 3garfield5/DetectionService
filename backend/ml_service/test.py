import cv2

RTSP_URL = "rtsp://localhost:8554/live_stream"

cap = cv2.VideoCapture(RTSP_URL)
print("isOpened:", cap.isOpened())

for i in range(50):
    ret, frame = cap.read()
    print(f"frame {i}: ret={ret}", end="")
    if ret:
        print(f", shape={frame.shape}")
    else:
        print()
cap.release()
