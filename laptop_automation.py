'''Isabella - laptop automation. System monitoring, auto-optimization, cleanup.'''

import os
import shutil
import threading
import time
import psutil

HEAVY_APPS = ['chrome.exe', 'teams.exe', 'discord.exe', 'steam.exe']


def get_system_status():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    bat = psutil.sensors_battery()
    bat_str = f"{bat.percent}% {'charging' if bat.power_plugged else 'on battery'}" if bat else "no battery"
    return f"CPU at {cpu}%, RAM at {ram}%, battery {bat_str}."


def get_detailed_status():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('C:/')
    bat = psutil.sensors_battery()
    net = psutil.net_io_counters()

    lines = [
        f"CPU usage is {cpu}%.",
        f"RAM: {ram.used // (1024**3)} of {ram.total // (1024**3)} GB used, {ram.percent}%.",
        f"Disk C: {disk.used // (1024**3)} of {disk.total // (1024**3)} GB used, {disk.percent}%.",
        f"Network: {net.bytes_sent // (1024**2)} MB sent, {net.bytes_recv // (1024**2)} MB received.",
    ]
    if bat:
        lines.append(f"Battery at {bat.percent}%, {'plugged in' if bat.power_plugged else 'not charging'}.")
    return " ".join(lines)


def get_battery_alert():
    bat = psutil.sensors_battery()
    if not bat or bat.power_plugged:
        return None
    if bat.percent <= 10:
        return f"Critical! Battery is at {bat.percent}%. Plug in immediately."
    if bat.percent <= 20:
        return f"Battery is low at {bat.percent}%. You should plug in soon."
    return None


def _kill_heavy_apps():
    killed = []
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in HEAVY_APPS:
                proc.kill()
                killed.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return killed


def auto_optimize():
    ram = psutil.virtual_memory().percent
    bat = psutil.sensors_battery()
    low_bat = bat and not bat.power_plugged and bat.percent < 20
    stressed = ram > 85 or low_bat

    if not stressed:
        return "System is running fine, no optimization needed."

    killed = _kill_heavy_apps()
    cleaned = clean_temp_files()
    reason = "high RAM usage" if ram > 85 else "low battery"

    if killed:
        apps = ", ".join(set(killed))
        return f"Optimized for {reason}. Closed {apps}. {cleaned}"
    return f"Optimized for {reason}. No heavy apps to close. {cleaned}"


def clean_temp_files():
    freed = 0
    paths = [
        os.environ.get('TEMP', ''),
        os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache'),
        os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache'),
    ]
    for folder in paths:
        if not folder or not os.path.isdir(folder):
            continue
        for entry in os.scandir(folder):
            try:
                if entry.is_file():
                    freed += entry.stat().st_size
                    os.remove(entry.path)
                elif entry.is_dir():
                    size = sum(f.stat().st_size for f in os.scandir(entry.path) if f.is_file())
                    freed += size
                    shutil.rmtree(entry.path, ignore_errors=True)
            except (PermissionError, OSError):
                pass

    mb = freed / (1024 * 1024)
    return f"Cleaned {mb:.0f} MB of temporary files."


def get_top_processes(n=5):
    procs = []
    for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
        try:
            procs.append((p.info['name'], p.info['cpu_percent'] or 0, p.info['memory_percent'] or 0))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x[1] + x[2], reverse=True)
    top = procs[:n]
    lines = [f"{name} using {cpu:.0f}% CPU and {mem:.1f}% RAM" for name, cpu, mem in top]
    return "Top processes: " + ", ".join(lines) + "."


def monitor_loop(callback):
    def _loop():
        while True:
            alert = get_battery_alert()
            if alert:
                callback(alert)

            ram = psutil.virtual_memory().percent
            if ram > 85:
                callback(f"RAM is at {ram:.0f}%. I'm going to optimize things.")
                result = auto_optimize()
                callback(result)

            time.sleep(60)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


if __name__ == '__main__':
    print(get_system_status())
    print(get_detailed_status())
    print(get_top_processes())
