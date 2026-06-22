"""
Faith - the hands.

Deterministic actions that don't need an AI call: opening/closing apps,
volume control, system info, clipboard, file management, web browsing.
"""
import os
import platform
import subprocess
import webbrowser


def open_app(path_or_name: str) -> str:
    """Open an application by name or path."""
    try:
        os.startfile(path_or_name)
        return f"Opened {path_or_name}"
    except Exception as e:
        return f"Failed to open {path_or_name}: {e}"


def close_app(process_name: str) -> str:
    """Kill a process by name (e.g. 'chrome', 'notepad')."""
    try:
        name = process_name.strip().lower()
        if not name.endswith(".exe"):
            name += ".exe"
        result = subprocess.run(["taskkill", "/IM", name, "/F"], capture_output=True, text=True)
        if result.returncode == 0:
            return f"Closed {process_name}"
        else:
            return f"Failed to close {process_name}: process not found or access denied."
    except Exception as e:
        return f"Failed to close {process_name}: {e}"


def set_volume(level: int) -> str:
    """Set system volume (0-100) using nircmd if available, else PowerShell."""
    try:
        level = max(0, min(100, level))
        # Use PowerShell to set volume
        ps_cmd = (
            f"$vol = [Math]::Round({level} * 655.35); "
            "(New-Object -ComObject WScript.Shell).SendKeys([char]173); "  # mute toggle reset
            f"$wshShell = New-Object -ComObject WScript.Shell; "
            f"1..50 | ForEach-Object {{ $wshShell.SendKeys([char]174) }}; "  # vol down to 0
            f"1..{level // 2} | ForEach-Object {{ $wshShell.SendKeys([char]175) }}"  # vol up
        )
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=5)
        return f"Volume set to ~{level}%"
    except Exception as e:
        return f"Failed to set volume: {e}"


def get_system_info() -> str:
    """Get basic system information."""
    info = []
    info.append(f"OS: {platform.system()} {platform.release()}")
    info.append(f"Machine: {platform.machine()}")
    info.append(f"Processor: {platform.processor()}")
    # Battery
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "(Get-WmiObject Win32_Battery).EstimatedChargeRemaining"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            info.append(f"Battery: {result.stdout.strip()}%")
    except Exception:
        pass
    return " | ".join(info)


def get_clipboard() -> str:
    """Read clipboard text content."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Failed to read clipboard: {e}"


def set_clipboard(text: str) -> str:
    """Set clipboard content."""
    try:
        escaped_text = text.replace("'", "''")
        subprocess.run(
            ["powershell", "-Command", f"Set-Clipboard -Value '{escaped_text}'"],
            capture_output=True, timeout=5, check=True
        )
        return "Copied to clipboard"
    except Exception as e:
        return f"Failed to set clipboard: {e}"


def create_text_file(path: str, content: str = "") -> str:
    """Create a text file at the given path."""
    try:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Created {path}"
    except Exception as e:
        return f"Failed to create file: {e}"


def open_website(url: str) -> str:
    """Open a URL in the default browser."""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened {url}"
    except Exception as e:
        return f"Failed to open website: {e}"


def web_search(query: str) -> str:
    """Search Google for a query."""
    try:
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return f"Searching for: {query}"
    except Exception as e:
        return f"Failed to execute search: {e}"


def list_running_apps() -> str:
    """List notable running processes."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object -Property Name,MainWindowTitle | Format-Table -AutoSize"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() or "No windowed apps found"
    except Exception as e:
        return f"Failed to list running apps: {e}"


def shutdown_pc(delay_seconds: int = 60) -> str:
    """Schedule a system shutdown."""
    try:
        subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)], capture_output=True)
        return f"PC will shut down in {delay_seconds} seconds"
    except Exception as e:
        return f"Failed to schedule shutdown: {e}"


def cancel_shutdown() -> str:
    """Cancel a scheduled shutdown."""
    try:
        subprocess.run(["shutdown", "/a"], capture_output=True)
        return "Shutdown cancelled"
    except Exception as e:
        return f"Failed to cancel shutdown: {e}"
