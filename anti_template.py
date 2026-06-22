"""
Faith - anti-template system.

Prevents her from falling into repetitive opening patterns.
Tracks recent openers and forces variety.
"""
import difflib

_recent_openings: list[str] = []
MAX_HISTORY = 20


def _first_words(text: str, n: int = 5) -> str:
    return " ".join(text.split()[:n]).lower()


def _classify(text: str) -> str:
    t = text.strip().lower()
    if t.endswith("?"):
        return "question"
    if any(t.startswith(w) for w in ["i ", "i'", "i'm", "i've"]):
        return "self"
    if any(t.startswith(w) for w in ["you ", "your", "you'"]):
        return "you"
    if any(t.startswith(w) for w in ["oh", "wait", "okay", "so", "hm"]):
        return "reactive"
    return "statement"


def is_repetitive(text: str) -> bool:
    """Returns True if this response is too similar to recent ones."""
    opening = _first_words(text)
    kind = _classify(text)

    # Check structural repetition in last 3
    recent_kinds = [_classify(o) for o in _recent_openings[-3:]]
    if recent_kinds.count(kind) >= 2:
        return True

    # Check textual similarity to last 10
    for prev in _recent_openings[-10:]:
        ratio = difflib.SequenceMatcher(None, opening, _first_words(prev)).ratio()
        if ratio > 0.7:
            return True

    return False


def record(text: str):
    """Record this response as used."""
    _recent_openings.append(text)
    if len(_recent_openings) > MAX_HISTORY:
        _recent_openings.pop(0)
