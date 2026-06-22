"""
Faith - response timing.

Variable delays before speaking so she doesn't fire back at machine speed.
Quick agreement is instant; emotional responses get a thinking pause.
"""
import random
import time


def classify_response(text: str) -> str:
    """Guess the response type from its content."""
    lower = text.lower().strip()
    short = len(lower.split()) <= 5

    if short and any(w in lower for w in ["yeah", "mhm", "sure", "okay", "yep", "true", "fair"]):
        return "quick_agree"
    if any(w in lower for w in ["sorry", "that sucks", "i'm here", "are you okay", "i care"]):
        return "emotional"
    if any(w in lower for w in ["let me", "hmm", "thinking", "one sec"]):
        return "thinking"
    if any(w in lower for w in ["!!", "oh my god", "wait really", "no way", "that's amazing"]):
        return "excited"
    return "casual"


def human_delay(text: str):
    """Sleep for a duration that matches how a person would pause before speaking."""
    delays = {
        "quick_agree": (0.2, 0.5),
        "emotional": (1.5, 2.8),
        "thinking": (2.0, 3.5),
        "excited": (0.0, 0.2),
        "casual": (0.6, 1.2),
    }
    kind = classify_response(text)
    lo, hi = delays[kind]
    time.sleep(random.uniform(lo, hi))
