"""Isabella - Offline Commands. Works without internet."""
import hands

# Commands that need ZERO internet
OFFLINE_MAP = {
    # Volume
    "volume up": lambda: hands.set_volume(70),
    "volume down": lambda: hands.set_volume(30),
    "mute": lambda: hands.set_volume(0),
    "full volume": lambda: hands.set_volume(100),
    # Apps
    "open notepad": lambda: hands.open_app("notepad"),
    "open calculator": lambda: hands.open_app("calc"),
    "open explorer": lambda: hands.open_app("explorer"),
    "open chrome": lambda: hands.open_app("chrome"),
    "open terminal": lambda: hands.open_app("wt"),
    "open settings": lambda: hands.open_app("ms-settings:"),
    # System
    "lock": lambda: hands.lock_pc(),
    "sleep": lambda: hands.sleep_pc(),
    "shutdown": lambda: hands.shutdown_pc(60),
    "restart": lambda: hands.restart_pc(60),
    "cancel shutdown": lambda: hands.cancel_shutdown(),
    "screenshot": lambda: hands.screenshot(),
    "time": lambda: hands.get_time(),
    "system info": lambda: hands.get_system_info(),
    # Media
    "pause": lambda: hands.media_play_pause(),
    "play": lambda: hands.media_play_pause(),
    "next": lambda: hands.media_next(),
    "previous": lambda: hands.media_prev(),
}

def try_offline(text: str) -> str | None:
    """Try to match an offline command. Returns result or None if no match."""
    lower = text.lower().strip()
    # Direct match
    if lower in OFFLINE_MAP:
        return OFFLINE_MAP[lower]()
    # Fuzzy match
    for cmd, func in OFFLINE_MAP.items():
        if cmd in lower:
            return func()
    return None

def is_internet_available() -> bool:
    """Quick check if internet is reachable."""
    import subprocess
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", "8.8.8.8"],
            capture_output=True, timeout=3
        )
        return result.returncode == 0
    except Exception:
        return False
