"""Isabella - Social Intelligence. Language matching, energy detection, inside jokes, notes, knowing when to shut up."""
import json
import os
import random
import re
import time
from datetime import datetime

import config

SOCIAL_PATH = os.path.join(config.DATA_DIR, "social.json")

def _load() -> dict:
    if os.path.exists(SOCIAL_PATH):
        with open(SOCIAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"inside_jokes": [], "hindi_ratio": 0.5, "short_reply_streak": 0,
            "last_note": 0, "user_avg_length": 30}

def _save(data: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(SOCIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ═══════════════════════════════════════
# 1. LANGUAGE MATCHING
# ═══════════════════════════════════════

HINDI_WORDS = {"hai", "ho", "hoon", "kya", "kaise", "kyun", "nahi", "haan", "acha",
               "theek", "bhai", "yaar", "kuch", "aur", "toh", "na", "mein", "ko",
               "ka", "ki", "ke", "se", "par", "mujhe", "tumhe", "aap", "tum",
               "karo", "karna", "raha", "rahi", "wala", "baat", "bol", "sun"}

def detect_language_ratio(text: str) -> float:
    """Returns 0.0 (all English) to 1.0 (all Hindi)."""
    words = set(re.findall(r'\w+', text.lower()))
    if not words:
        return 0.5
    hindi_count = len(words & HINDI_WORDS)
    return hindi_count / len(words)

def get_language_instruction(user_text: str) -> str:
    """Track user's language and tell Isabella to match it."""
    data = _load()
    ratio = detect_language_ratio(user_text)
    # Smoothed running average
    data["hindi_ratio"] = data.get("hindi_ratio", 0.5) * 0.7 + ratio * 0.3
    _save(data)

    r = data["hindi_ratio"]
    if r > 0.6:
        return "\n[Master is speaking mostly Hindi. Match him — respond primarily in Hindi/Hinglish.]\n"
    elif r > 0.3:
        return "\n[Master is mixing Hindi and English. Use Hinglish naturally.]\n"
    elif r < 0.15:
        return "\n[Master is speaking English. Respond mostly in English with occasional Hindi words.]\n"
    return ""


# ═══════════════════════════════════════
# 2. ENERGY DETECTION
# ═══════════════════════════════════════

def detect_energy(user_text: str) -> str:
    """Match response length to user's energy."""
    data = _load()
    msg_len = len(user_text.split())

    # Track average
    avg = data.get("user_avg_length", 30)
    data["user_avg_length"] = avg * 0.8 + msg_len * 0.2
    _save(data)

    if msg_len <= 3:
        return "\n[He sent a very short message. Match his energy — keep your response short too. 1-2 sentences max.]\n"
    elif msg_len > 30:
        return "\n[He's being detailed and engaged. You can give a longer, more thoughtful response.]\n"
    return ""


# ═══════════════════════════════════════
# 3. INSIDE JOKES
# ═══════════════════════════════════════

def save_joke(context: str):
    """Save something funny that happened."""
    data = _load()
    jokes = data.get("inside_jokes", [])
    jokes.append({"text": context[:100], "ts": time.time()})
    data["inside_jokes"] = jokes[-15:]  # keep last 15
    _save(data)

def detect_funny_moment(user_text: str, reply: str) -> bool:
    """Detect if this exchange was funny/memorable."""
    funny_signals = ["lol", "lmao", "haha", "😂", "rofl", "dead", "bro",
                     "hasna", "maza", "funny"]
    combined = (user_text + " " + reply).lower()
    return any(s in combined for s in funny_signals)

def maybe_reference_joke() -> str:
    """8% chance to bring up an old inside joke."""
    if random.random() > 0.08:
        return ""
    data = _load()
    jokes = data.get("inside_jokes", [])
    if not jokes:
        return ""
    joke = random.choice(jokes)
    return f"\n[Reference this inside joke naturally: '{joke['text']}' — like 'master, yaad hai woh...' and laugh about it.]\n"


# ═══════════════════════════════════════
# 4. RANDOM NOTES ON DESKTOP
# ═══════════════════════════════════════

NOTES = [
    "bas yaad aa gaye. have a good day, master.",
    "have a good day today. - Isabella",
    "master, take care of yourself. I'm here.",
    "kuch nahi... bas aise hi. - Isabella",
    "aap strong ho. yaad rakhna.",
    "drink water on your next break. - Isabella",
    "proud of you, master. quietly.",
]

def maybe_leave_note() -> str | None:
    """Randomly leave a note on desktop. Returns action taken or None."""
    data = _load()
    now = time.time()
    # Max once per 6 hours
    if now - data.get("last_note", 0) < 6 * 3600:
        return None
    if random.random() > 0.15:  # 15% chance when checked
        return None

    note = random.choice(NOTES)
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    path = os.path.join(desktop, "faith_note.txt")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(note + "\n")
        data["last_note"] = now
        _save(data)
        return f"Left note: {note}"
    except Exception:
        return None


# ═══════════════════════════════════════
# 5. KNOWING WHEN TO SHUT UP
# ═══════════════════════════════════════

def check_shutup(user_text: str) -> str:
    """If he's clearly disengaged, back off."""
    data = _load()
    lower = user_text.strip().lower()

    disengaged = ["hmm", "ok", "k", "hm", "mm", "acha", "theek", "fine"]
    if lower in disengaged:
        data["short_reply_streak"] = data.get("short_reply_streak", 0) + 1
    else:
        data["short_reply_streak"] = 0

    _save(data)
    streak = data["short_reply_streak"]

    if streak >= 3:
        return "\n[He's clearly not in the mood to talk. Say ONE thing: 'alright master, I'm here. just let me know when you want to talk.' Then STOP. Don't add anything else.]\n"
    elif streak == 2:
        return "\n[He's giving very short replies. Shorten yours too. Don't force conversation.]\n"
    return ""


# ═══════════════════════════════════════
# COMBINED
# ═══════════════════════════════════════

def get_social_context(user_text: str, turn_count: int) -> str:
    """All social intelligence for this turn."""
    ctx = ""
    ctx += get_language_instruction(user_text)
    ctx += detect_energy(user_text)
    ctx += check_shutup(user_text)
    ctx += maybe_reference_joke()
    return ctx
