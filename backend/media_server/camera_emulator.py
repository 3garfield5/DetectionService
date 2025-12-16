# backend/media_server/camera_emulator.py
import subprocess
import sys
from pathlib import Path

VIDEO = Path(__file__).with_name("test.mp4")
RTSP_URL = "rtsp://localhost:8554/live_stream"

if not VIDEO.exists():
    print(f"[ERR] Видео {VIDEO} не найдено", file=sys.stderr)
    sys.exit(1)

cmd = [
    "ffmpeg",
    "-re",                 # играть с реальным FPS
    "-stream_loop", "-1",  # крутить по кругу
    "-i", str(VIDEO),

    # кодек и формат потока
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-pix_fmt", "yuv420p",
    "-tune", "zerolatency",

    # только ошибки, чтобы не заливать консоль ворнингами
    "-loglevel", "error",

    # RTSP по TCP (меньше потерь пакетов)
    "-f", "rtsp",
    "-rtsp_transport", "tcp",
    RTSP_URL,
]

print("[INFO] Запускаю эмулятор камеры:")
print("      ", " ".join(cmd))

proc = subprocess.Popen(cmd)

try:
    proc.wait()
except KeyboardInterrupt:
    print("[INFO] Останавливаю эмулятор...")
    proc.terminate()
    proc.wait()
