'''Isabella - automation triggers. Watches system events and notifies.'''

import os
import time
import threading
import subprocess
import psutil

_stop = threading.Event()


def _get_wifi_ssid():
    try:
        out = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if 'SSID' in line and 'BSSID' not in line:
                return line.split(':', 1)[1].strip()
    except Exception:
        pass
    return None


def _get_drives():
    return {p.mountpoint for p in psutil.disk_partitions()}


def _watch_battery(callback):
    was_charging = None
    alerted_low = False
    while not _stop.is_set():
        bat = psutil.sensors_battery()
        if bat:
            if bat.power_plugged and was_charging is False:
                callback('battery_charging', 'Charging now, master.')
                alerted_low = False
            if not bat.power_plugged and bat.percent < 20 and not alerted_low:
                callback('battery_low', f'Master, battery is at {bat.percent}%. Should I enable power saver?')
                alerted_low = True
            if bat.percent >= 20:
                alerted_low = False
            was_charging = bat.power_plugged
        _stop.wait(30)


def _watch_usb(callback):
    prev = _get_drives()
    while not _stop.is_set():
        curr = _get_drives()
        for d in curr - prev:
            callback('usb_connected', 'A USB drive was connected.')
        prev = curr
        _stop.wait(5)


def _watch_downloads(callback):
    path = os.path.join(os.path.expanduser('~'), 'Downloads')
    prev = set(os.listdir(path)) if os.path.isdir(path) else set()
    while not _stop.is_set():
        _stop.wait(3)
        if not os.path.isdir(path):
            continue
        curr = set(os.listdir(path))
        for f in curr - prev:
            callback('download_complete', f'A new file appeared in Downloads: {f}')
        prev = curr


def _watch_wifi(callback):
    prev = _get_wifi_ssid()
    while not _stop.is_set():
        _stop.wait(10)
        curr = _get_wifi_ssid()
        if curr and curr != prev:
            callback('wifi_changed', f'WiFi changed to {curr}')
        prev = curr


def _detect_boot(callback):
    boot_time = psutil.boot_time()
    if time.time() - boot_time < 120:
        callback('startup', 'System just booted. Good morning, master.')


def start_all_watchers(callback):
    _stop.clear()
    _detect_boot(callback)
    for fn in (_watch_battery, _watch_usb, _watch_downloads, _watch_wifi):
        t = threading.Thread(target=fn, args=(callback,), daemon=True)
        t.start()


def stop_all_watchers():
    _stop.set()
