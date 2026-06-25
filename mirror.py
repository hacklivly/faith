"""
Isabella - linguistic mirroring.

Tracks the user's speech patterns over time and gradually adopts them.
Mirrors slowly (over days, not instantly) to feel natural, not creepy.
"""
import json
import os

import config

MIRROR_PATH = os.path.join(config.DATA_DIR, "mirror.json")

KNOWN_SLANG = [
    "fire", "lowkey", "highkey", "no cap", "fr", "ngl", "wild", "based", "bet", "bruh", "vibe",
    "sus", "mid", "ratio", "slay", "tea", "valid", "cope", "rent free", "ick", "ate",
    "period", "real", "fax", "deadass", "lit", "goated", "cringe", "bussin", "cap",
    "w", "l", "yeet", "rizz", "gyat", "ong", "bro", "dawg", "twin", "gang",
    "sigma", "chad", "skibidi", "aura", "drip", "slaps", "hits different",
]


def _load() -> dict:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if not os.path.exists(MIRROR_PATH):
        return {"slang_counts": {}, "avg_length": [], "messages_analyzed": 0}
    with open(MIRROR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict):
    with open(MIRROR_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def analyze(message: str):
    """Track patterns from a user message."""
    data = _load()
    words = message.split()
    data["messages_analyzed"] += 1
    data["avg_length"].append(len(words))
    # Keep only last 100 measurements
    data["avg_length"] = data["avg_length"][-100:]

    for term in KNOWN_SLANG:
        if term in message.lower():
            data["slang_counts"][term] = data["slang_counts"].get(term, 0) + 1

    _save(data)


def get_style_instruction() -> str:
    """Return a style instruction for the LLM based on adopted patterns."""
    data = _load()
    if data["messages_analyzed"] < 10:
        return ""

    instructions = []

    # Adopt slang heard 4+ times
    adopted = [term for term, count in data["slang_counts"].items() if count >= 4]
    if adopted:
        instructions.append(f"You've picked up some of his language: occasionally use words like {', '.join(adopted[:3])}.")

    # Match sentence length tendency
    if data["avg_length"]:
        avg = sum(data["avg_length"]) / len(data["avg_length"])
        if avg < 8:
            instructions.append("He uses short messages — keep yours short too, mostly under 10 words per sentence.")
        elif avg > 20:
            instructions.append("He tends toward longer messages — you can be a bit more expansive too.")

    if not instructions:
        return ""

    return "\n[Linguistic mirroring: " + " ".join(instructions) + "]\n"
