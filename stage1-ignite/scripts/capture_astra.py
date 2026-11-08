"""Capture one frame from the Orbbec Astra Pro HD RGB stream on RDK X5.

Usage:
    python3 capture_astra.py [output.jpg]
"""
import sys

import cv2

DEVICE = "/dev/video0"
WIDTH, HEIGHT = 1280, 720
WARMUP_FRAMES = 10  # let auto-exposure settle

out_path = sys.argv[1] if len(sys.argv) > 1 else "camera_test.jpg"

cap = cv2.VideoCapture(DEVICE, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

for _ in range(WARMUP_FRAMES):
    cap.read()

ok, frame = cap.read()
print("capture ok:", ok, "size:", frame.shape if ok else None)
if ok:
    cv2.imwrite(out_path, frame)
    print("saved:", out_path)
cap.release()
sys.exit(0 if ok else 1)
