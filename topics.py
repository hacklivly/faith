"""
Isabella - topic tracking.

Maintains a graph of open conversational threads so she can bring things
back up days later, the way a person who's been thinking about you would.
"""
import json
import os
import time

import config

TOPICS_PATH = os.path.join(config.DATA_DIR, "topics.json")


def _load() -> list:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if not os.path.exists(TOPICS_PATH):
        return []
    with open(TOPICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(topics: list):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(topics, f, indent=2)


def add_topic(topic: str, emotional_weight: float = 0.5):
    """Store a new open thread to potentially bring back later."""
    topics = _load()
    topics.append({
        "topic": topic,
        "added": time.time(),
        "emotional_weight": emotional_weight,
        "resurfaced": False,
    })
    # Keep max 30 topics
    if len(topics) > 30:
        topics = topics[-30:]
    _save(topics)


def get_resurfaceable(min_age_hours: float = None) -> list[dict]:
    """Get topics old enough to bring back and not yet resurfaced."""
    if min_age_hours is None:
        min_age_hours = config.TOPIC_RESURFACE_HOURS
    topics = _load()
    now = time.time()
    return [
        t for t in topics
        if not t["resurfaced"] and (now - t["added"]) > min_age_hours * 3600
    ]


def mark_resurfaced(topic_text: str):
    """Mark a topic as already brought back up."""
    topics = _load()
    for t in topics:
        if t["topic"] == topic_text:
            t["resurfaced"] = True
    _save(topics)


def topics_for_prompt() -> str:
    """Get unresurfaced topics as context for the system prompt."""
    ready = get_resurfaceable()
    if not ready:
        return ""
    lines = [t["topic"] for t in sorted(ready, key=lambda x: -x["emotional_weight"])[:3]]
    return (
        "\nOpen threads from past conversations you could bring back up naturally "
        "(only if it fits the moment — don't force it):\n"
        + "\n".join(f"- {l}" for l in lines)
        + "\n"
    )
