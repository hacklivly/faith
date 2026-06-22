"""
Faith - the eyes.

Grabs a single webcam frame on demand rather than streaming continuously -
she looks when there's a reason to, not all the time.
"""
import base64

import cv2


def capture_frame_base64():
    cam = cv2.VideoCapture(0)
    ok, frame = cam.read()
    cam.release()
    if not ok:
        return None
    ok, buf = cv2.imencode(".jpg", frame)
    if not ok:
        return None
    return base64.b64encode(buf).decode("utf-8")
