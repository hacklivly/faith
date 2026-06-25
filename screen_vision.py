"""
Isabella - screen vision.

Captures desktop screenshot on demand (not continuously) and encodes it
for sending to Groq vision alongside the webcam frame.
"""
import base64
import io

import pyautogui


def capture_screen_base64(quality: int = 50) -> str | None:
    """Take a screenshot, compress to JPEG, return base64 string."""
    try:
        screenshot = pyautogui.screenshot()
        # Resize to save bandwidth — half resolution is plenty for context
        screenshot = screenshot.resize((screenshot.width // 2, screenshot.height // 2))
        buf = io.BytesIO()
        screenshot.save(buf, format="JPEG", quality=quality)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return None
