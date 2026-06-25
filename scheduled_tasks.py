'''Isabella - scheduled tasks. Night cleanup, file organization, backups.'''

import os
import shutil
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

DOWNLOADS = Path.home() / "Downloads"
TEMP_DIRS = [Path(os.environ.get("TEMP", "")), Path("C:/Windows/Temp")]

CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".odt", ".csv"],
    "Music": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".h", ".json", ".xml", ".yml", ".yaml"],
}

SCHEDULE = [
    {"name": "night_cleanup", "hour": 2, "minute": 0, "daily": True},
    {"name": "organize_downloads", "hour": 9, "minute": 0, "weekly": True, "day": 6},  # Sunday
]

_running = False
_thread = None


def night_cleanup() -> str:
    """Clean temp files and browser caches."""
    cleaned = 0
    errors = 0
    for tmp in TEMP_DIRS:
        if not tmp.exists():
            continue
        for item in tmp.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    cleaned += 1
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    cleaned += 1
            except Exception:
                errors += 1

    # Browser cache paths
    cache_paths = [
        Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Cache",
        Path.home() / "AppData/Local/Microsoft/Edge/User Data/Default/Cache",
    ]
    for cache in cache_paths:
        if cache.exists():
            try:
                shutil.rmtree(cache, ignore_errors=True)
                cleaned += 1
            except Exception:
                errors += 1

    return f"Cleanup done: {cleaned} items removed, {errors} errors"


def organize_downloads() -> str:
    """Sort Downloads folder files into subfolders by type."""
    if not DOWNLOADS.exists():
        return "Downloads folder not found"

    moved = 0
    for file in DOWNLOADS.iterdir():
        if not file.is_file():
            continue
        ext = file.suffix.lower()
        dest_folder = "Other"
        for category, extensions in CATEGORIES.items():
            if ext in extensions:
                dest_folder = category
                break
        dest = DOWNLOADS / dest_folder
        dest.mkdir(exist_ok=True)
        try:
            shutil.move(str(file), str(dest / file.name))
            moved += 1
        except Exception:
            pass

    return f"Organized {moved} files in Downloads"


def weekly_backup(src: str, dst: str) -> str:
    """Copy src folder to dst as backup."""
    src_path = Path(src)
    dst_path = Path(dst) / f"backup_{datetime.now().strftime('%Y%m%d')}"
    if not src_path.exists():
        return f"Source not found: {src}"
    try:
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        return f"Backed up {src} -> {dst_path}"
    except Exception as e:
        return f"Backup failed: {e}"


def get_next_tasks() -> str:
    """Return upcoming scheduled tasks."""
    now = datetime.now()
    lines = []
    for task in SCHEDULE:
        target = now.replace(hour=task["hour"], minute=task["minute"], second=0)
        if target <= now:
            target += timedelta(days=1)
        if task.get("weekly"):
            while target.weekday() != task["day"]:
                target += timedelta(days=1)
        lines.append(f"{task['name']}: {target.strftime('%A %H:%M')}")
    return "\n".join(lines) if lines else "No tasks scheduled"


def run_task(name: str) -> str:
    """Manually trigger a task by name."""
    tasks = {
        "night_cleanup": night_cleanup,
        "cleanup": night_cleanup,
        "organize_downloads": organize_downloads,
        "organize": organize_downloads,
    }
    func = tasks.get(name.lower().replace(" ", "_"))
    if func:
        return func()
    return f"Unknown task: {name}. Available: {', '.join(tasks.keys())}"


def _check_schedule():
    """Background loop that checks if any task should run."""
    global _running
    while _running:
        now = datetime.now()
        for task in SCHEDULE:
            if now.hour == task["hour"] and now.minute == task["minute"]:
                if task.get("weekly") and now.weekday() != task["day"]:
                    continue
                run_task(task["name"])
        time.sleep(60)


def start_scheduler():
    """Start background scheduler thread."""
    global _running, _thread
    if _running:
        return
    _running = True
    _thread = threading.Thread(target=_check_schedule, daemon=True)
    _thread.start()


def stop_scheduler():
    """Stop background scheduler."""
    global _running
    _running = False


if __name__ == "__main__":
    print("Scheduled tasks:")
    print(get_next_tasks())
    print("\nRunning cleanup...")
    print(night_cleanup())
