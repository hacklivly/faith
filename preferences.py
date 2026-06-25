"""
Isabella - preferences.

Learns and saves user's favorites from conversation. When he says
"this is my favorite" or "I love this song", she remembers it forever.
"""
import json
import os

import config

PREFS_PATH = os.path.join(config.DATA_DIR, "preferences.json")


def _load() -> dict:
    if os.path.exists(PREFS_PATH):
        with open(PREFS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"music": [], "websites": [], "apps": [], "food": [], "general": []}


def _save(prefs: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(PREFS_PATH, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)


def add_favorite(category: str, item: str) -> str:
    """Add something to favorites. Categories: music, websites, apps, food, general."""
    prefs = _load()
    cat = category.lower()
    if cat not in prefs:
        cat = "general"
    # Don't duplicate
    if item.lower() not in [i.lower() for i in prefs[cat]]:
        prefs[cat].append(item)
        _save(prefs)
    return f"Saved to favorites ({cat}): {item}"


def get_favorites(category: str = None) -> list:
    """Get favorites, optionally filtered by category."""
    prefs = _load()
    if category and category.lower() in prefs:
        return prefs[category.lower()]
    # Return all
    all_favs = []
    for cat, items in prefs.items():
        for item in items:
            all_favs.append(f"[{cat}] {item}")
    return all_favs


def get_random_favorite(category: str = "music") -> str | None:
    """Get a random favorite from a category."""
    import random
    prefs = _load()
    items = prefs.get(category.lower(), [])
    return random.choice(items) if items else None


def detect_favorite(text: str) -> tuple[str, str] | None:
    """Detect if user is expressing a favorite from their message.
    Returns (category, item) or None."""
    lower = text.lower()

    triggers = [
        "my favorite", "my favourite", "i love this", "i love that",
        "this is fire", "this slaps", "best song", "best music",
        "save this", "remember this", "add this to my favorites",
        "ye mera favorite", "mujhe ye pasand", "bahut achha", "mast hai",
    ]

    if not any(t in lower for t in triggers):
        return None

    # Detect category
    if any(w in lower for w in ["song", "music", "track", "artist", "singer", "gaana"]):
        return ("music", text)
    elif any(w in lower for w in ["website", "site", "page", "app"]):
        return ("websites", text)
    elif any(w in lower for w in ["food", "dish", "khana", "recipe"]):
        return ("food", text)
    else:
        return ("general", text)


def get_preferences_for_prompt() -> str:
    """Returns a prompt-friendly summary of user preferences."""
    prefs = _load()
    lines = []
    for cat, items in prefs.items():
        if items:
            lines.append(f"  {cat}: {', '.join(items[-5:])}")
    if not lines:
        return ""
    return "\n[Master's favorites (use to suggest/play things he likes):\n" + "\n".join(lines) + "]\n"
