"""
Isabella - distraction guard + screen time tracker.

Monitors active window/browser. If master is on time-wasting sites or apps
for too long, she warns him. Also tracks total screen time per app.
"""
import json
import os
import time
import subprocess

import config

# Sites/apps considered time-wasting
DISTRACTION_SITES = [
    "instagram", "facebook", "twitter", "x.com", "tiktok",
    "reddit", "snapchat", "pinterest", "tumblr",
    "9gag", "buzzfeed", "netflix", "hotstar", "primevideo",
]

DISTRACTION_APPS = [
    "instagram", "facebook", "twitter", "tiktok",
    "candy crush", "pubg", "bgmi", "free fire",
]

# How long (seconds) before she warns
WARN_AFTER = 10 * 60  # 10 minutes

_distraction_start = None
_last_warned = 0
_WARN_COOLDOWN = 5 * 60  # don't nag more than once per 5 min

# Screen time tracking
SCREEN_TIME_PATH = os.path.join(config.DATA_DIR, "screen_time.json")
_current_app = ""
_app_start_time = 0


def _load_screen_time() -> dict:
    try:
        if os.path.exists(SCREEN_TIME_PATH):
            with open(SCREEN_TIME_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {"today": "", "apps": {}, "total_minutes": 0}


def _save_screen_time(data: dict):
    try:
        os.makedirs(os.path.dirname(SCREEN_TIME_PATH), exist_ok=True)
        with open(SCREEN_TIME_PATH, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def _get_today() -> str:
    from datetime import date
    return date.today().isoformat()


def track_screen_time():
    """Call periodically to track which app is active and for how long."""
    global _current_app, _app_start_time

    window = get_active_window()
    if not window:
        return

    # Simplify window title to app name
    app_name = _simplify_app_name(window)

    now = time.time()
    if app_name != _current_app:
        # Save time spent on previous app
        if _current_app and _app_start_time:
            elapsed = (now - _app_start_time) / 60  # minutes
            _record_time(_current_app, elapsed)
        _current_app = app_name
        _app_start_time = now


def _simplify_app_name(window_title: str) -> str:
    """Extract app name from window title."""
    known = {
        "chrome": "Chrome", "edge": "Edge", "firefox": "Firefox",
        "code": "VS Code", "visual studio": "VS Code",
        "discord": "Discord", "spotify": "Spotify",
        "explorer": "File Explorer", "notepad": "Notepad",
        "word": "Word", "excel": "Excel",
        "youtube": "YouTube", "instagram": "Instagram",
        "twitter": "Twitter", "reddit": "Reddit",
        "netflix": "Netflix",
    }
    for key, name in known.items():
        if key in window_title:
            return name
    # Return first meaningful word
    parts = window_title.split(" - ")
    return parts[-1].strip().title()[:20] if parts else "Unknown"


def _record_time(app: str, minutes: float):
    """Record time spent on an app."""
    if minutes < 0.1:
        return
    data = _load_screen_time()
    today = _get_today()
    if data.get("today") != today:
        data = {"today": today, "apps": {}, "total_minutes": 0}
    data["apps"][app] = data["apps"].get(app, 0) + minutes
    data["total_minutes"] = data.get("total_minutes", 0) + minutes
    _save_screen_time(data)


def get_screen_time_summary() -> str:
    """Get today's screen time summary for Isabella to reference."""
    data = _load_screen_time()
    if data.get("today") != _get_today():
        return ""
    total = int(data.get("total_minutes", 0))
    if total < 5:
        return ""
    apps = sorted(data.get("apps", {}).items(), key=lambda x: x[1], reverse=True)[:5]
    summary = f"Screen time today: {total} minutes total. "
    summary += ", ".join(f"{name}: {int(mins)}min" for name, mins in apps)
    return summary


def get_active_window() -> str:
    """Get the title of currently active window."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Add-Type @'\nusing System;\nusing System.Runtime.InteropServices;\npublic class Win { [DllImport(\"user32.dll\")] public static extern IntPtr GetForegroundWindow(); [DllImport(\"user32.dll\")] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count); }\n'@\n$h = [Win]::GetForegroundWindow(); $b = New-Object System.Text.StringBuilder 256; [Win]::GetWindowText($h, $b, 256); $b.ToString()"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip().lower()
    except Exception:
        return ""


def check_distraction() -> str | None:
    """Check if master is currently wasting time. Returns warning message or None.
    Call this periodically (e.g., during proactive_checkin or between turns)."""
    global _distraction_start, _last_warned

    now = time.time()

    # Cooldown: don't warn too often
    if now - _last_warned < _WARN_COOLDOWN:
        return None

    window_title = get_active_window()
    if not window_title:
        return None

    is_distracted = any(site in window_title for site in DISTRACTION_SITES)
    if not is_distracted:
        is_distracted = any(app in window_title for app in DISTRACTION_APPS)

    if is_distracted:
        if _distraction_start is None:
            _distraction_start = now
        elif now - _distraction_start >= WARN_AFTER:
            _last_warned = now
            minutes = int((now - _distraction_start) / 60)
            return f"[DISTRACTION DETECTED: master has been on '{window_title}' for {minutes} minutes. Warn him firmly but caringly to get back on track.]"
    else:
        _distraction_start = None

    return None


def is_distracted_now() -> tuple[bool, str]:
    """Quick check: is he on a distracting site right now? Returns (bool, window_title)."""
    window_title = get_active_window()
    is_bad = any(site in window_title for site in DISTRACTION_SITES + DISTRACTION_APPS)
    return is_bad, window_title
