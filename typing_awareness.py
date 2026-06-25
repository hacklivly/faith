"""Isabella - Typing Awareness. Detect when user is working, stay quiet."""
import ctypes
import ctypes.wintypes
import time

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.wintypes.UINT), ("dwTime", ctypes.wintypes.DWORD)]

def get_idle_seconds() -> float:
    """Returns seconds since last keyboard/mouse input."""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0

def is_user_typing() -> bool:
    """True if user had keyboard/mouse activity in last 5 seconds."""
    return get_idle_seconds() < 5.0

def should_stay_quiet() -> bool:
    """True if user is actively working (input in last 30 seconds). Don't interrupt."""
    return get_idle_seconds() < 30.0
