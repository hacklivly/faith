"""Isabella - Routine Tracker. Learn daily patterns, predict needs."""
import json
import os
import time
from datetime import datetime

import config

ROUTINE_PATH = os.path.join(config.DATA_DIR, "routine.json")

def _load() -> dict:
    if os.path.exists(ROUTINE_PATH):
        with open(ROUTINE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"events": [], "patterns": {}}

def _save(data: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(ROUTINE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def record_event(event_type: str):
    """Record an event: wake, sleep, eat, work_start, work_end, break, interaction."""
    data = _load()
    now = datetime.now()
    entry = {"type": event_type, "time": now.strftime("%H:%M"), "day": now.strftime("%A"), "ts": time.time()}
    data["events"].append(entry)
    # Keep last 200 events
    data["events"] = data["events"][-200:]
    # Update pattern averages
    _update_patterns(data, event_type, now)
    _save(data)

def _update_patterns(data: dict, event_type: str, now: datetime):
    patterns = data.get("patterns", {})
    if event_type not in patterns:
        patterns[event_type] = {"times": [], "avg_hour": 0}
    hour_min = now.hour + now.minute / 60.0
    patterns[event_type]["times"].append(hour_min)
    patterns[event_type]["times"] = patterns[event_type]["times"][-30:]
    patterns[event_type]["avg_hour"] = sum(patterns[event_type]["times"]) / len(patterns[event_type]["times"])
    data["patterns"] = patterns

def get_predictions() -> dict:
    """Predict what user likely needs based on time + history."""
    data = _load()
    patterns = data.get("patterns", {})
    now = datetime.now()
    hour = now.hour + now.minute / 60.0
    predictions = {}

    for event_type, info in patterns.items():
        avg = info.get("avg_hour", 12)
        diff = abs(hour - avg)
        if diff < 1:
            predictions[event_type] = "now"
        elif hour > avg - 0.5 and hour < avg + 2:
            predictions[event_type] = "soon"

    # Common sense predictions
    last_eat = _last_event_hours_ago(data, "eat")
    if last_eat and last_eat > 4:
        predictions["should_eat"] = True

    last_break = _last_event_hours_ago(data, "break")
    if last_break and last_break > 2:
        predictions["needs_break"] = True

    return predictions

def _last_event_hours_ago(data: dict, event_type: str) -> float | None:
    events = [e for e in data.get("events", []) if e["type"] == event_type]
    if not events:
        return None
    last_ts = events[-1]["ts"]
    return (time.time() - last_ts) / 3600

def get_routine_summary() -> str:
    """Returns prompt context about user's routine."""
    data = _load()
    patterns = data.get("patterns", {})
    predictions = get_predictions()
    if not patterns and not predictions:
        return ""

    lines = ["\n[Master's routine patterns:"]
    for event_type, info in patterns.items():
        avg = info.get("avg_hour", 0)
        h, m = int(avg), int((avg % 1) * 60)
        lines.append(f"  {event_type}: usually around {h:02d}:{m:02d}")

    if predictions:
        lines.append(" Predictions now:")
        if predictions.get("should_eat"):
            lines.append("  - He hasn't eaten in 4+ hours. Remind him.")
        if predictions.get("needs_break"):
            lines.append("  - No break in 2+ hours. Suggest one.")

    lines.append("]\n")
    return "\n".join(lines)
