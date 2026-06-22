"""
Faith - memory.

A journal of impressions rather than a transcript database, plus a mood
that persists and drifts across sessions instead of resetting every time
you open the app. Recall is recency-weighted on purpose: mostly recent
entries, occasionally an older one, the way people actually remember things.
"""
import json
import os
import random
import time

import config


def _ensure_data_dir():
    os.makedirs(config.DATA_DIR, exist_ok=True)


def load_journal() -> list:
    _ensure_data_dir()
    if not os.path.exists(config.JOURNAL_PATH):
        return []
    with open(config.JOURNAL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_journal(entries: list):
    _ensure_data_dir()
    with open(config.JOURNAL_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def add_journal_entry(text: str):
    entries = load_journal()
    entries.append({"text": text, "timestamp": time.time()})
    save_journal(entries)


def recent_journal_texts(n_recent: int = 6, n_random_older: int = 2) -> list:
    """Recall memories with strong anti-forgetting bias.
    
    Always includes recent entries + random older ones so she naturally
    references old conversations. More older memories = less forgetting.
    """
    entries = load_journal()
    if not entries:
        return []
    
    # Always show recent
    recent = entries[-n_recent:]
    older = entries[:-n_recent]
    
    # Pull MORE random older memories — this is the anti-forgetting mechanism
    # Scale older sample size with journal length so she remembers more as time passes
    older_sample_size = min(max(n_random_older, len(older) // 4), 8)
    sampled_older = random.sample(older, min(older_sample_size, len(older))) if older else []
    
    combined = sorted(sampled_older + recent, key=lambda e: e["timestamp"])
    return [e["text"] for e in combined]


def load_mood() -> dict:
    _ensure_data_dir()
    if not os.path.exists(config.MOOD_PATH):
        return {
            "valence": 0.6, "energy": 0.7, "openness": 0.8,
            "affection": 0.5, "emotional_labor": 1.0,
            "trust_level": 20, "streak_days": 0, "last_interaction": None,
            "reason": "still getting to know him"
        }
    with open(config.MOOD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_mood(mood: dict):
    _ensure_data_dir()
    mood["updated"] = time.time()
    with open(config.MOOD_PATH, "w", encoding="utf-8") as f:
        json.dump(mood, f, indent=2)


def update_mood(signals: dict):
    """Update mood based on conversation signals.
    signals can contain: compliment, dismissive, accomplishment, heavy_support, absence_hours
    """
    mood = load_mood()

    # Track streak
    now = time.time()
    last = mood.get("last_interaction")
    if last:
        hours_since = (now - last) / 3600
        if hours_since > 48:
            mood["streak_days"] = 0
            mood["valence"] = max(0.2, mood["valence"] - 0.15)
            mood["reason"] = "he's been gone a while"
        elif hours_since > 20:
            mood["streak_days"] += 1
    mood["last_interaction"] = now

    # Apply signals
    if signals.get("compliment"):
        mood["affection"] = min(1.0, mood["affection"] + 0.05)
        mood["valence"] = min(1.0, mood["valence"] + 0.1)
    if signals.get("dismissive"):
        mood["valence"] = max(0.0, mood["valence"] - 0.1)
        mood["energy"] = max(0.1, mood["energy"] - 0.15)
        mood["reason"] = "he snapped a bit"
    if signals.get("accomplishment"):
        mood["valence"] = min(1.0, mood["valence"] + 0.15)
        mood["energy"] = min(1.0, mood["energy"] + 0.1)
        mood["reason"] = "he did something great"
    if signals.get("heavy_support"):
        mood["emotional_labor"] = max(0.0, mood["emotional_labor"] - 0.25)
        mood["reason"] = "that conversation was heavy"

    # Natural energy decay toward 0.5 over time
    mood["energy"] += (0.5 - mood["energy"]) * 0.05
    # Emotional labor recharges slowly
    mood["emotional_labor"] = min(1.0, mood["emotional_labor"] + 0.03)
    # Trust grows slowly with each interaction, decays with long absence
    mood["trust_level"] = min(100, mood.get("trust_level", 20) + 0.3)

    save_mood(mood)
