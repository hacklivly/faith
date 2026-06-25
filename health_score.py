"""Isabella - Health Score. Track screen time, breaks, sleep → daily score."""
import json
import os
import time
from datetime import datetime

import config

HEALTH_PATH = os.path.join(config.DATA_DIR, "health.json")

def _load() -> dict:
    if os.path.exists(HEALTH_PATH):
        with open(HEALTH_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"today": _today(), "screen_start": time.time(), "breaks": 0,
            "last_break": time.time(), "sleep_hour": None, "wake_hour": None,
            "meals": 0, "water": 0, "score_history": []}

def _save(data: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(HEALTH_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def _reset_if_new_day(data: dict) -> dict:
    if data.get("today") != _today():
        old_score = calculate_score(data)
        history = data.get("score_history", [])
        history.append({"date": data.get("today", ""), "score": old_score})
        history = history[-30:]
        data = {"today": _today(), "screen_start": time.time(), "breaks": 0,
                "last_break": time.time(), "sleep_hour": None, "wake_hour": None,
                "meals": 0, "water": 0, "score_history": history}
    return data

def record_break():
    data = _reset_if_new_day(_load())
    data["breaks"] = data.get("breaks", 0) + 1
    data["last_break"] = time.time()
    _save(data)

def record_meal():
    data = _reset_if_new_day(_load())
    data["meals"] = data.get("meals", 0) + 1
    _save(data)

def record_water():
    data = _reset_if_new_day(_load())
    data["water"] = data.get("water", 0) + 1
    _save(data)

def record_sleep(hour: int):
    data = _reset_if_new_day(_load())
    data["sleep_hour"] = hour
    _save(data)

def record_wake(hour: int):
    data = _reset_if_new_day(_load())
    data["wake_hour"] = hour
    _save(data)

def calculate_score(data: dict = None) -> int:
    """Calculate health score 0-10."""
    if data is None:
        data = _reset_if_new_day(_load())
    score = 5  # baseline

    # Breaks (good: 3+, bad: 0)
    breaks = data.get("breaks", 0)
    if breaks >= 3: score += 1
    elif breaks == 0: score -= 1

    # Meals (good: 2-3, bad: 0-1)
    meals = data.get("meals", 0)
    if meals >= 2: score += 1
    elif meals == 0: score -= 2

    # Sleep time (good: before midnight, bad: after 2am)
    sleep = data.get("sleep_hour")
    if sleep is not None:
        if sleep <= 23: score += 1
        elif sleep >= 2 and sleep <= 5: score -= 2

    # Screen time (hours since start)
    screen_hrs = (time.time() - data.get("screen_start", time.time())) / 3600
    if screen_hrs > 8: score -= 2
    elif screen_hrs > 5: score -= 1

    # Time since last break
    last_break_hrs = (time.time() - data.get("last_break", time.time())) / 3600
    if last_break_hrs > 3: score -= 1

    return max(0, min(10, score))

def get_health_summary() -> str:
    """For prompt injection."""
    data = _reset_if_new_day(_load())
    _save(data)
    sc = calculate_score(data)
    screen_hrs = (time.time() - data.get("screen_start", time.time())) / 3600
    last_break_hrs = (time.time() - data.get("last_break", time.time())) / 3600

    alerts = []
    if last_break_hrs > 2:
        alerts.append(f"no break in {last_break_hrs:.0f}hr")
    if data.get("meals", 0) == 0 and datetime.now().hour > 13:
        alerts.append("hasn't eaten today")
    if screen_hrs > 5:
        alerts.append(f"screen time: {screen_hrs:.0f}hr")

    if not alerts:
        return ""
    return f"\n[Health: {sc}/10. Concerns: {', '.join(alerts)}. Remind him gently.]\n"
