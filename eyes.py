"""
Isabella - the eyes.

Continuous visual awareness. Captures periodically and detects scene changes:
new clothes, going outside, different environment, new people, etc.
"""
import base64
import threading
import time

import cv2
import numpy as np

_last_frame = None
_last_capture_time = 0
_scene_description = ""
_change_detected = False
_change_description = ""
_lock = threading.Lock()

# How often to auto-capture (seconds)
CAPTURE_INTERVAL = 30  # every 30 seconds
# How different frames need to be to count as a "change" (0-1)
CHANGE_THRESHOLD = 0.35


def capture_frame_base64() -> str | None:
    """Capture a single frame from webcam, return as base64 JPEG."""
    cam = cv2.VideoCapture(0)
    ok, frame = cam.read()
    cam.release()
    if not ok:
        return None
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    if not ok:
        return None
    return base64.b64encode(buf).decode("utf-8")


def _frame_difference(frame1, frame2) -> float:
    """Compare two frames. Returns 0.0 (identical) to 1.0 (completely different)."""
    if frame1 is None or frame2 is None:
        return 1.0
    # Resize both to small size for fast comparison
    small1 = cv2.resize(frame1, (64, 64))
    small2 = cv2.resize(frame2, (64, 64))
    # Convert to grayscale
    gray1 = cv2.cvtColor(small1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(small2, cv2.COLOR_BGR2GRAY)
    # Compute structural difference
    diff = cv2.absdiff(gray1, gray2)
    score = np.mean(diff) / 255.0
    return score


def _capture_raw():
    """Capture raw frame (numpy array)."""
    cam = cv2.VideoCapture(0)
    ok, frame = cam.read()
    cam.release()
    return frame if ok else None


def periodic_capture():
    """Called periodically. Captures frame and checks for scene changes."""
    global _last_frame, _last_capture_time, _change_detected, _change_description

    now = time.time()
    if now - _last_capture_time < CAPTURE_INTERVAL:
        return

    _last_capture_time = now
    current_frame = _capture_raw()
    if current_frame is None:
        return

    with _lock:
        if _last_frame is not None:
            diff = _frame_difference(_last_frame, current_frame)
            if diff > CHANGE_THRESHOLD:
                _change_detected = True
                if diff > 0.7:
                    _change_description = "major_change"  # completely different scene (went outside, different room)
                elif diff > 0.5:
                    _change_description = "moderate_change"  # new clothes, moved location
                else:
                    _change_description = "minor_change"  # shifted position, lighting changed
        _last_frame = current_frame


def has_scene_changed() -> tuple[bool, str]:
    """Check if scene changed since last check. Returns (changed, change_level).
    Resets the flag after reading."""
    global _change_detected, _change_description
    with _lock:
        if _change_detected:
            _change_detected = False
            desc = _change_description
            _change_description = ""
            return True, desc
    return False, ""


def get_awareness_frame() -> str | None:
    """Get a fresh frame specifically for awareness/context analysis."""
    return capture_frame_base64()


def start_continuous_capture():
    """Start background thread for periodic captures."""
    def _loop():
        while True:
            try:
                periodic_capture()
            except Exception:
                pass
            time.sleep(10)  # check every 10 seconds if interval passed

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
