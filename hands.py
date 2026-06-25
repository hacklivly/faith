"""
Isabella - the hands.

Full computer control: file system, browser, apps, system settings,
command execution, clipboard, and more. She can do anything on his PC.
"""
import glob as globmod
import json
import os
import platform
import shutil
import subprocess


# ═══════════════════════════════════════════════════════════
# FILE SYSTEM
# ═══════════════════════════════════════════════════════════

def create_file(path: str, content: str = "") -> str:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Created file: {path}"
    except Exception as e:
        return f"Failed: {e}"


def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(10000)  # cap at 10k chars
        return content
    except Exception as e:
        return f"Failed to read: {e}"


def append_file(path: str, content: str) -> str:
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Appended to {path}"
    except Exception as e:
        return f"Failed: {e}"


def delete_file(path: str) -> str:
    try:
        if os.path.isfile(path):
            os.remove(path)
            return f"Deleted file: {path}"
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return f"Deleted folder: {path}"
        return f"Not found: {path}"
    except Exception as e:
        return f"Failed: {e}"


def move_file(src: str, dst: str) -> str:
    try:
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        shutil.move(src, dst)
        return f"Moved {src} → {dst}"
    except Exception as e:
        return f"Failed: {e}"


def copy_file(src: str, dst: str) -> str:
    try:
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return f"Copied {src} → {dst}"
    except Exception as e:
        return f"Failed: {e}"


def rename_file(path: str, new_name: str) -> str:
    try:
        new_path = os.path.join(os.path.dirname(path), new_name)
        os.rename(path, new_path)
        return f"Renamed to {new_name}"
    except Exception as e:
        return f"Failed: {e}"


def list_dir(path: str = ".") -> str:
    try:
        items = os.listdir(path)
        result = []
        for item in sorted(items)[:50]:  # limit to 50
            full = os.path.join(path, item)
            prefix = "[DIR]" if os.path.isdir(full) else "[FILE]"
            result.append(f"{prefix} {item}")
        return "\n".join(result) if result else "Empty directory"
    except Exception as e:
        return f"Failed: {e}"


def find_files(pattern: str, directory: str = ".") -> str:
    try:
        matches = globmod.glob(os.path.join(directory, "**", pattern), recursive=True)
        return "\n".join(matches[:30]) if matches else "No files found"
    except Exception as e:
        return f"Failed: {e}"


def get_file_info(path: str) -> str:
    try:
        stat = os.stat(path)
        size = stat.st_size
        if size > 1_000_000:
            size_str = f"{size / 1_000_000:.1f} MB"
        elif size > 1000:
            size_str = f"{size / 1000:.1f} KB"
        else:
            size_str = f"{size} bytes"
        return f"{path} | Size: {size_str} | Type: {'dir' if os.path.isdir(path) else os.path.splitext(path)[1]}"
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# APPS & PROCESSES
# ═══════════════════════════════════════════════════════════

def open_app(path_or_name: str) -> str:
    try:
        os.startfile(path_or_name)
        return f"Opened {path_or_name}"
    except Exception as e:
        return f"Failed to open {path_or_name}: {e}"


def smart_open_app(name: str) -> str:
    """Search Windows Start Menu shortcuts for any installed app and open it."""
    search_dirs = [
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%UserProfile%\Desktop"),
    ]
    name_lower = name.lower().strip()

    # Search for .lnk files matching the app name
    best_match = None
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            for f in files:
                if f.lower().endswith(('.lnk', '.url')):
                    fname = f[:-4].lower()  # remove extension
                    if name_lower in fname or fname in name_lower:
                        best_match = os.path.join(root, f)
                        if fname == name_lower:  # exact match, use immediately
                            os.startfile(best_match)
                            return f"Opened {f[:-4]}"

    if best_match:
        os.startfile(best_match)
        return f"Opened {os.path.basename(best_match)[:-4]}"

    # Last resort: try running the name directly (works for PATH apps)
    try:
        os.startfile(name)
        return f"Opened {name}"
    except Exception:
        return f"Could not find '{name}' on this PC"


def close_app(process_name: str) -> str:
    try:
        name = process_name.strip().lower()
        if not name.endswith(".exe"):
            name += ".exe"
        result = subprocess.run(["taskkill", "/IM", name, "/F"], capture_output=True, text=True)
        return f"Closed {process_name}" if result.returncode == 0 else f"Not found: {process_name}"
    except Exception as e:
        return f"Failed: {e}"


def list_running_apps() -> str:
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object Name,MainWindowTitle | Format-Table -AutoSize"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or "No windowed apps found"
    except Exception as e:
        return f"Failed: {e}"


def run_command(command: str) -> str:
    """Run any shell command and return output."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        err = result.stderr.strip()
        if output and err:
            return f"{output}\n[stderr: {err}]"
        return output or err or "Done (no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out (30s limit)"
    except Exception as e:
        return f"Failed: {e}"


def run_python(code: str) -> str:
    """Execute a Python snippet and return output."""
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        err = result.stderr.strip()
        return output or err or "Done"
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# BROWSER CONTROL
# ═══════════════════════════════════════════════════════════

def open_website(url: str) -> str:
    try:
        if not url.startswith("http"):
            url = "https://" + url
        os.startfile(url)
        return f"Opened {url}"
    except Exception as e:
        return f"Failed: {e}"


def open_new_tab(url: str) -> str:
    try:
        if not url.startswith("http"):
            url = "https://" + url
        os.startfile(url)
        return f"Opened new tab: {url}"
    except Exception as e:
        return f"Failed: {e}"


def web_search(query: str) -> str:
    try:
        import urllib.parse
        os.startfile(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        return f"Searching: {query}"
    except Exception as e:
        return f"Failed: {e}"


def youtube_search(query: str) -> str:
    try:
        import urllib.parse
        os.startfile(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
        return f"YouTube search: {query}"
    except Exception as e:
        return f"Failed: {e}"


def close_browser_tab() -> str:
    """Close current browser tab with Ctrl+W."""
    try:
        import pyautogui
        pyautogui.hotkey("ctrl", "w")
        return "Closed current tab"
    except Exception as e:
        return f"Failed: {e}"


def switch_tab(direction: str = "next") -> str:
    """Switch browser tab."""
    try:
        import pyautogui
        if direction == "next":
            pyautogui.hotkey("ctrl", "tab")
        else:
            pyautogui.hotkey("ctrl", "shift", "tab")
        return f"Switched to {direction} tab"
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# SYSTEM CONTROL
# ═══════════════════════════════════════════════════════════

def set_volume(level: int) -> str:
    try:
        level = max(0, min(100, level))
        ps = f"""
$vol = {level / 100.0}
$obj = New-Object -ComObject WScript.Shell
1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}
$steps = [math]::Round({level} / 2)
1..$steps | ForEach-Object {{ $obj.SendKeys([char]175) }}
"""
        subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=5)
        return f"Volume set to ~{level}%"
    except Exception as e:
        return f"Failed: {e}"


def set_brightness(level: int) -> str:
    try:
        level = max(0, min(100, level))
        subprocess.run(
            ["powershell", "-Command",
             f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"],
            capture_output=True, timeout=5
        )
        return f"Brightness set to {level}%"
    except Exception as e:
        return f"Failed: {e}"


def get_system_info() -> str:
    info = [f"OS: {platform.system()} {platform.release()}", f"Machine: {platform.machine()}"]
    try:
        bat = subprocess.run(
            ["powershell", "-Command", "(Get-WmiObject Win32_Battery).EstimatedChargeRemaining"],
            capture_output=True, text=True, timeout=5
        )
        if bat.stdout.strip():
            info.append(f"Battery: {bat.stdout.strip()}%")
    except Exception:
        pass
    try:
        mem = subprocess.run(
            ["powershell", "-Command",
             "$os = Get-CimInstance Win32_OperatingSystem; "
             "[math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1).ToString() + ' GB used / ' + [math]::Round($os.TotalVisibleMemorySize/1MB, 1).ToString() + ' GB total'"],
            capture_output=True, text=True, timeout=5
        )
        if mem.stdout.strip():
            info.append(f"RAM: {mem.stdout.strip()}")
    except Exception:
        pass
    return " | ".join(info)


def get_wifi_name() -> str:
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split("\n"):
            if "SSID" in line and "BSSID" not in line:
                return line.split(":")[-1].strip()
        return "Not connected"
    except Exception as e:
        return f"Failed: {e}"


def toggle_wifi(enable: bool = True) -> str:
    try:
        action = "enable" if enable else "disable"
        subprocess.run(
            ["netsh", "interface", "set", "interface", "Wi-Fi", action],
            capture_output=True, timeout=5
        )
        return f"Wi-Fi {'enabled' if enable else 'disabled'}"
    except Exception as e:
        return f"Failed: {e}"


def toggle_bluetooth(enable: bool = True) -> str:
    """Toggle Bluetooth on/off via PowerShell."""
    try:
        if enable:
            ps = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'})[0]
$radio = [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime]
$reqAccess = $radio::RequestAccessAsync()
$null = $asTask.MakeGenericMethod([Windows.Devices.Radios.RadioAccessStatus]).Invoke($null, @($reqAccess))
Start-Sleep 1
$radios = $radio::GetRadiosAsync()
$getRadios = $asTask.MakeGenericMethod([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]]).Invoke($null, @($radios))
$getRadios.Wait()
$bt = $getRadios.Result | Where-Object { $_.Kind -eq 'Bluetooth' }
if ($bt) { $bt.SetStateAsync('On') }
"""
        else:
            ps = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'})[0]
$radio = [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime]
$radios = $radio::GetRadiosAsync()
$getRadios = $asTask.MakeGenericMethod([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]]).Invoke($null, @($radios))
$getRadios.Wait()
$bt = $getRadios.Result | Where-Object { $_.Kind -eq 'Bluetooth' }
if ($bt) { $bt.SetStateAsync('Off') }
"""
        subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=10)
        return f"Bluetooth {'enabled' if enable else 'disabled'}"
    except Exception as e:
        return f"Failed: {e}"


def get_bluetooth_status() -> str:
    """Check if Bluetooth is on or off."""
    try:
        ps = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'})[0]
$radio = [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime]
$radios = $radio::GetRadiosAsync()
$getRadios = $asTask.MakeGenericMethod([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]]).Invoke($null, @($radios))
$getRadios.Wait()
$bt = $getRadios.Result | Where-Object { $_.Kind -eq 'Bluetooth' }
if ($bt) { $bt.State } else { 'Not found' }
"""
        result = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True, timeout=10)
        state = result.stdout.strip()
        return f"Bluetooth: {state}"
    except Exception as e:
        return f"Failed: {e}"


def lock_pc() -> str:
    try:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], capture_output=True)
        return "PC locked"
    except Exception as e:
        return f"Failed: {e}"


def shutdown_pc(delay_seconds: int = 60) -> str:
    try:
        subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)], capture_output=True)
        return f"Shutting down in {delay_seconds}s"
    except Exception as e:
        return f"Failed: {e}"


def restart_pc(delay_seconds: int = 30) -> str:
    try:
        subprocess.run(["shutdown", "/r", "/t", str(delay_seconds)], capture_output=True)
        return f"Restarting in {delay_seconds}s"
    except Exception as e:
        return f"Failed: {e}"


def cancel_shutdown() -> str:
    try:
        subprocess.run(["shutdown", "/a"], capture_output=True)
        return "Shutdown cancelled"
    except Exception as e:
        return f"Failed: {e}"


def sleep_pc() -> str:
    try:
        subprocess.run(
            ["powershell", "-Command", "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)"],
            capture_output=True, timeout=5
        )
        return "PC going to sleep"
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# CLIPBOARD
# ═══════════════════════════════════════════════════════════

def get_clipboard() -> str:
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() or "(empty clipboard)"
    except Exception as e:
        return f"Failed: {e}"


def set_clipboard(text: str) -> str:
    try:
        escaped = text.replace("'", "''")
        subprocess.run(
            ["powershell", "-Command", f"Set-Clipboard -Value '{escaped}'"],
            capture_output=True, timeout=5
        )
        return "Copied to clipboard"
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# KEYBOARD & MOUSE (via pyautogui)
# ═══════════════════════════════════════════════════════════

def type_text(text: str) -> str:
    """Type text at current cursor position."""
    try:
        import pyautogui
        pyautogui.typewrite(text, interval=0.02) if text.isascii() else pyautogui.write(text)
        return f"Typed: {text[:50]}"
    except Exception as e:
        return f"Failed: {e}"


def press_key(key: str) -> str:
    """Press a single key or combo like 'ctrl+s', 'alt+f4', 'enter'."""
    try:
        import pyautogui
        if "+" in key:
            keys = [k.strip() for k in key.split("+")]
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key)
        return f"Pressed: {key}"
    except Exception as e:
        return f"Failed: {e}"


def click(x: int = None, y: int = None) -> str:
    """Click at position. If no position, clicks current cursor location."""
    try:
        import pyautogui
        if x is not None and y is not None:
            pyautogui.click(x, y)
            return f"Clicked at ({x}, {y})"
        else:
            pyautogui.click()
            return "Clicked"
    except Exception as e:
        return f"Failed: {e}"


def screenshot(save_path: str = None) -> str:
    """Take a screenshot and optionally save it."""
    try:
        import pyautogui
        img = pyautogui.screenshot()
        path = save_path or os.path.join(os.path.expanduser("~"), "Desktop", "screenshot.png")
        img.save(path)
        return f"Screenshot saved: {path}"
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# NOTIFICATIONS & DISPLAY
# ═══════════════════════════════════════════════════════════

def show_notification(title: str, message: str) -> str:
    """Show a Windows toast notification."""
    try:
        ps = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$text = $template.GetElementsByTagName('text')
$text[0].AppendChild($template.CreateTextNode('{title.replace("'", "''")}')) > $null
$text[1].AppendChild($template.CreateTextNode('{message.replace("'", "''")}')) > $null
$toast = [Windows.UI.Notifications.ToastNotification]::new($template)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Isabella').Show($toast)
"""
        subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=5)
        return f"Notification sent: {title}"
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# TIME & REMINDERS
# ═══════════════════════════════════════════════════════════

def get_time() -> str:
    from datetime import datetime
    now = datetime.now()
    return now.strftime("%I:%M %p, %A %B %d, %Y")


def set_timer(seconds: int, message: str = "Time's up") -> str:
    """Set a timer that shows notification after N seconds."""
    try:
        ps = f"Start-Sleep -Seconds {seconds}; Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('{message.replace(chr(39), chr(39)+chr(39))}', 'Isabella Timer')"
        subprocess.Popen(
            ["powershell", "-Command", ps],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return f"Timer set: {seconds}s — {message}"
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# MEDIA CONTROL
# ═══════════════════════════════════════════════════════════

def media_play_pause() -> str:
    try:
        import pyautogui
        pyautogui.press("playpause")
        return "Toggled play/pause"
    except Exception as e:
        return f"Failed: {e}"


def media_next() -> str:
    try:
        import pyautogui
        pyautogui.press("nexttrack")
        return "Next track"
    except Exception as e:
        return f"Failed: {e}"


def media_prev() -> str:
    try:
        import pyautogui
        pyautogui.press("prevtrack")
        return "Previous track"
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# ADVANCED AUTOMATION (Selenium + AutoHotkey backends)
# ═══════════════════════════════════════════════════════════

def web_read(url: str) -> str:
    """Read page content via Selenium."""
    try:
        import web_agent
        web_agent.goto(url)
        return web_agent.read_page()
    except Exception as e:
        return f"Failed: {e}"


def web_google(query: str) -> str:
    """Google search via Selenium, returns actual results."""
    try:
        import web_agent
        return web_agent.google(query)
    except Exception as e:
        return f"Failed: {e}"


def web_weather(city: str = "") -> str:
    """Get weather via Selenium."""
    try:
        import web_agent
        return web_agent.get_weather(city)
    except Exception as e:
        return f"Failed: {e}"


def web_news(topic: str = "") -> str:
    """Get news via Selenium."""
    try:
        import web_agent
        return web_agent.get_news(topic)
    except Exception as e:
        return f"Failed: {e}"


def web_click(text: str) -> str:
    """Click element on current page by visible text."""
    try:
        import web_agent
        return web_agent.click_element(text)
    except Exception as e:
        return f"Failed: {e}"


def web_fill(selector: str, text: str) -> str:
    """Fill input field on current page."""
    try:
        import web_agent
        return web_agent.fill_input(selector, text)
    except Exception as e:
        return f"Failed: {e}"


def web_search_site(query: str) -> str:
    """Search on whatever site is currently open."""
    try:
        import web_agent
        return web_agent.search_on_site(query)
    except Exception as e:
        return f"Failed: {e}"


def window_focus(title: str) -> str:
    """Focus a window by title (via AutoHotkey)."""
    try:
        import ahk_agent
        return ahk_agent.focus_window(title)
    except Exception as e:
        return f"Failed: {e}"


def window_snap(direction: str) -> str:
    """Snap window left/right/up/down (via AutoHotkey)."""
    try:
        import ahk_agent
        return ahk_agent.snap_window(direction)
    except Exception as e:
        return f"Failed: {e}"


def window_list() -> str:
    """List all open windows (via AutoHotkey)."""
    try:
        import ahk_agent
        return ahk_agent.list_windows()
    except Exception as e:
        return f"Failed: {e}"


def send_hotkey(combo: str) -> str:
    """Send keyboard shortcut like 'ctrl+shift+s' (via AutoHotkey)."""
    try:
        import ahk_agent
        return ahk_agent.hotkey(combo)
    except Exception as e:
        return f"Failed: {e}"


def precise_click(x: int, y: int) -> str:
    """Click exact screen coordinates (via AutoHotkey)."""
    try:
        import ahk_agent
        return ahk_agent.mouse_click(x, y)
    except Exception as e:
        return f"Failed: {e}"


def run_ahk(script: str) -> str:
    """Run arbitrary AutoHotkey script for complex automation."""
    try:
        import ahk_agent
        return ahk_agent.run_script(script)
    except Exception as e:
        return f"Failed: {e}"


# ═══════════════════════════════════════════════════════════
# LAPTOP AUTOMATION (system health, cleanup, organize, backup)
# ═══════════════════════════════════════════════════════════

def system_status() -> str:
    try:
        import laptop_automation
        return laptop_automation.get_system_status()
    except Exception as e:
        return f"Failed: {e}"


def system_status_detailed() -> str:
    try:
        import laptop_automation
        return laptop_automation.get_detailed_status()
    except Exception as e:
        return f"Failed: {e}"


def auto_optimize() -> str:
    try:
        import laptop_automation
        return laptop_automation.auto_optimize()
    except Exception as e:
        return f"Failed: {e}"


def clean_temp() -> str:
    try:
        import laptop_automation
        return laptop_automation.clean_temp_files()
    except Exception as e:
        return f"Failed: {e}"


def top_processes() -> str:
    try:
        import laptop_automation
        return laptop_automation.get_top_processes()
    except Exception as e:
        return f"Failed: {e}"


def organize_downloads() -> str:
    try:
        import scheduled_tasks
        return scheduled_tasks.organize_downloads()
    except Exception as e:
        return f"Failed: {e}"


def backup_folder(src: str, dst: str) -> str:
    try:
        import scheduled_tasks
        return scheduled_tasks.weekly_backup(src, dst)
    except Exception as e:
        return f"Failed: {e}"


def night_cleanup() -> str:
    try:
        import scheduled_tasks
        return scheduled_tasks.night_cleanup()
    except Exception as e:
        return f"Failed: {e}"
