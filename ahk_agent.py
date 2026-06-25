"""
Isabella - AutoHotkey agent.

Precise window management, keyboard/mouse control, and system automation
via AutoHotkey scripts. Requires AutoHotkey v2 installed at default path.
"""
import os
import subprocess
import tempfile
import time

# AutoHotkey v2 path — portable install in project, or system install
AHK_PATH = os.path.join(os.path.dirname(__file__), "tools", "ahk", "AutoHotkey64.exe")
if not os.path.exists(AHK_PATH):
    AHK_PATH = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"
if not os.path.exists(AHK_PATH):
    AHK_PATH = r"C:\Program Files\AutoHotkey\AutoHotkey.exe"


def _run_ahk(script: str, timeout: int = 10) -> str:
    """Write and execute an AHK script, return output."""
    if not os.path.exists(AHK_PATH):
        return "AutoHotkey not installed. Install from https://www.autohotkey.com"

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".ahk", delete=False, encoding="utf-8")
    tmp.write(script)
    tmp.close()
    try:
        result = subprocess.run(
            [AHK_PATH, tmp.name],
            capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout.strip()
        return output if output else "Done"
    except subprocess.TimeoutExpired:
        return "Script timed out"
    except Exception as e:
        return f"Failed: {e}"
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# WINDOW MANAGEMENT
# ═══════════════════════════════════════════════════════════

def focus_window(title: str) -> str:
    """Bring a window to front by partial title match."""
    return _run_ahk(f'SetTitleMatchMode 2\nWinActivate "{title}"')


def minimize_window(title: str = "") -> str:
    """Minimize a window (current if no title)."""
    if title:
        return _run_ahk(f'SetTitleMatchMode 2\nWinMinimize "{title}"')
    return _run_ahk('WinMinimize "A"')


def maximize_window(title: str = "") -> str:
    """Maximize a window."""
    if title:
        return _run_ahk(f'SetTitleMatchMode 2\nWinMaximize "{title}"')
    return _run_ahk('WinMaximize "A"')


def close_window(title: str) -> str:
    """Close a window by title."""
    return _run_ahk(f'SetTitleMatchMode 2\nWinClose "{title}"')


def snap_window(direction: str) -> str:
    """Snap active window: left, right, up (maximize), down (minimize)."""
    key_map = {"left": "Left", "right": "Right", "up": "Up", "down": "Down"}
    key = key_map.get(direction.lower(), "Left")
    return _run_ahk(f'Send "#{{' + key + '}}"')


def move_window(x: int, y: int, width: int = 0, height: int = 0) -> str:
    """Move/resize active window."""
    if width and height:
        return _run_ahk(f'WinMove {x}, {y}, {width}, {height}, "A"')
    return _run_ahk(f'WinMove {x}, {y},,, "A"')


def list_windows() -> str:
    """List all visible windows."""
    script = """
DetectHiddenWindows false
list := ""
for hwnd in WinGetList() {
    title := WinGetTitle(hwnd)
    if (title != "")
        list .= title "`n"
}
FileOpen("*", "w").Write(list)
"""
    return _run_ahk(script)


def get_active_window() -> str:
    """Get title of active window."""
    return _run_ahk('FileOpen("*", "w").Write(WinGetTitle("A"))')


# ═══════════════════════════════════════════════════════════
# KEYBOARD
# ═══════════════════════════════════════════════════════════

def send_keys(keys: str) -> str:
    """Send keystrokes. Uses AHK syntax: ^c = Ctrl+C, !f4 = Alt+F4, #{} = Win."""
    return _run_ahk(f'Send "{keys}"')


def send_text(text: str) -> str:
    """Type text literally (no special key interpretation)."""
    escaped = text.replace('"', '`"').replace("\n", "`n")
    return _run_ahk(f'SendText "{escaped}"')


def hotkey(combo: str) -> str:
    """Send a hotkey combo like 'ctrl+shift+s', 'alt+f4', 'win+d'."""
    # Convert human-readable to AHK format
    parts = [p.strip().lower() for p in combo.split("+")]
    ahk_keys = []
    for p in parts:
        if p in ("ctrl", "control"):
            ahk_keys.append("^")
        elif p in ("alt",):
            ahk_keys.append("!")
        elif p in ("shift",):
            ahk_keys.append("+")
        elif p in ("win", "windows", "super"):
            ahk_keys.append("#")
        else:
            ahk_keys.append("{" + p + "}")
    return _run_ahk(f'Send "{"".join(ahk_keys)}"')


# ═══════════════════════════════════════════════════════════
# MOUSE
# ═══════════════════════════════════════════════════════════

def mouse_click(x: int, y: int, button: str = "left") -> str:
    """Click at exact screen coordinates."""
    return _run_ahk(f'Click {x}, {y}, "{button}"')


def mouse_move(x: int, y: int) -> str:
    """Move mouse to coordinates."""
    return _run_ahk(f"MouseMove {x}, {y}")


def mouse_drag(x1: int, y1: int, x2: int, y2: int) -> str:
    """Drag from one point to another."""
    return _run_ahk(f"MouseClickDrag \"Left\", {x1}, {y1}, {x2}, {y2}")


def mouse_scroll(clicks: int = 3, direction: str = "down") -> str:
    """Scroll mouse wheel."""
    d = "WheelDown" if direction == "down" else "WheelUp"
    return _run_ahk(f'Send "{{' + d + f' {clicks}}}"')


def get_mouse_pos() -> str:
    """Get current mouse position."""
    script = """
MouseGetPos &xpos, &ypos
FileOpen("*", "w").Write(xpos "," ypos)
"""
    return _run_ahk(script)


# ═══════════════════════════════════════════════════════════
# SYSTEM SHORTCUTS
# ═══════════════════════════════════════════════════════════

def show_desktop() -> str:
    """Win+D to show desktop."""
    return _run_ahk('Send "#d"')


def task_view() -> str:
    """Win+Tab for task view."""
    return _run_ahk('Send "#Tab"')


def open_start_menu() -> str:
    """Open start menu."""
    return _run_ahk('Send "{LWin}"')


def open_run_dialog() -> str:
    """Win+R run dialog."""
    return _run_ahk('Send "#r"')


def open_file_explorer() -> str:
    """Win+E file explorer."""
    return _run_ahk('Send "#e"')


def clipboard_history() -> str:
    """Win+V clipboard history."""
    return _run_ahk('Send "#v"')


def emoji_picker() -> str:
    """Win+. emoji picker."""
    return _run_ahk('Send "#."')


def screen_snip() -> str:
    """Win+Shift+S screen snip."""
    return _run_ahk('Send "#+s"')


def switch_virtual_desktop(direction: str = "right") -> str:
    """Switch virtual desktop left/right."""
    key = "Right" if direction == "right" else "Left"
    return _run_ahk(f'Send "#^{{' + key + '}}"')


# ═══════════════════════════════════════════════════════════
# ADVANCED AUTOMATION
# ═══════════════════════════════════════════════════════════

def run_script(script: str) -> str:
    """Run arbitrary AHK v2 script. For complex multi-step automation."""
    return _run_ahk(script, timeout=30)


def wait_for_window(title: str, timeout: int = 10) -> str:
    """Wait for a window to appear."""
    return _run_ahk(f'SetTitleMatchMode 2\nWinWait "{title}",, {timeout}')


def pixel_color(x: int, y: int) -> str:
    """Get color of pixel at screen coordinates."""
    script = f"""
color := PixelGetColor({x}, {y})
FileOpen("*", "w").Write(color)
"""
    return _run_ahk(script)
