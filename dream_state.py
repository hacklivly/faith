"""
Faith - dream state.

When she "wakes up" after being off, she reflects on significant topics
from the previous session, producing a thought she developed "overnight."
"""
import json
import os
import time

import brain
import config

DREAM_PATH = os.path.join(config.DATA_DIR, "dream.json")


def _load_dream() -> dict:
    if os.path.exists(DREAM_PATH):
        with open(DREAM_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_dream(data: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(DREAM_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def store_significant_topics(topics: list[str]):
    """Called on shutdown or journal update — saves top topics for dream processing."""
    _save_dream({"topics": topics[:3], "stored_at": time.time(), "processed": False})


def generate_dream_thought() -> str | None:
    """On startup, if there are unprocessed topics, generate an overnight reflection."""
    dream = _load_dream()
    if not dream or dream.get("processed") or not dream.get("topics"):
        return None

    # Only generate if enough time has passed (at least 4 hours "asleep")
    stored = dream.get("stored_at", 0)
    if time.time() - stored < 4 * 3600:
        return None

    topics_text = ", ".join(dream["topics"])
    prompt = (
        f"You went offline for a while. These topics were on your mind: {topics_text}. "
        "Generate ONE short thought (1-2 sentences) you 'developed overnight' — "
        "an insight, a question, or something you realized. Be genuine and specific. "
        "Don't say 'while I was offline' — just share the thought naturally."
    )

    try:
        thought = brain.get_reply(prompt, [])
        dream["processed"] = True
        dream["thought"] = thought
        _save_dream(dream)
        return thought
    except Exception:
        return None
