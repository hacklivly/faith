"""
Isabella - emotion detection engine.

Multi-signal emotion detection from text. Goes beyond keyword matching:
detects patterns, intensity, sarcasm markers, emotional trajectory.
Inspired by Isabella's emotional intelligence layer.
"""
import re

# Emotion categories with intensity 0.0-1.0
EMOTIONS = {
    "joy": 0.0,
    "sadness": 0.0,
    "anger": 0.0,
    "fear": 0.0,
    "love": 0.0,
    "frustration": 0.0,
    "excitement": 0.0,
    "loneliness": 0.0,
    "pride": 0.0,
    "vulnerability": 0.0,
    "sarcasm": 0.0,
    "jealousy": 0.0,
    "neutral": 0.0,
}

# Pattern-based detection (regex + weight)
_PATTERNS = {
    "joy": [
        (r'\b(happy|glad|amazing|awesome|great|love it|perfect|yay)\b', 0.6),
        (r'[!]{2,}', 0.3),  # multiple exclamation marks
        (r'(haha|lol|lmao|rofl|😂|🤣)', 0.5),
        (r'\b(finally|at last|made it)\b', 0.4),
    ],
    "sadness": [
        (r'\b(sad|depressed|lonely|miss|lost|empty|broken|hurt)\b', 0.6),
        (r'\b(crying|tears|cried|sobbing)\b', 0.8),
        (r'\b(nobody|no one|alone|invisible)\b', 0.5),
        (r'\.{3,}', 0.2),  # trailing dots = low energy
    ],
    "anger": [
        (r'\b(angry|pissed|furious|hate|sick of|fed up)\b', 0.7),
        (r'\b(stupid|idiot|dumb|pathetic|useless)\b', 0.5),
        (r'[!]{3,}', 0.4),  # extreme exclamation
        (r'\b(wtf|wth|bs|bullshit)\b', 0.6),
        (r'\b(shut up|fuck off|go away|leave me alone|get lost)\b', 0.8),
        (r'\b(annoying|irritating|unbearable|intolerable)\b', 0.5),
        (r'\b(disgusting|trash|garbage|worst)\b', 0.5),
    ],
    "fear": [
        (r'\b(scared|terrified|afraid|anxious|panic|worried)\b', 0.7),
        (r'\b(what if|can\'t breathe|heart racing|shaking)\b', 0.6),
        (r'\b(nightmare|dread|doom)\b', 0.5),
    ],
    "love": [
        (r'\b(love you|miss you|care about you|mean everything)\b', 0.8),
        (r'\b(you\'re amazing|you matter|thank you for being)\b', 0.6),
        (r'(❤|💕|🥰|😘)', 0.5),
    ],
    "frustration": [
        (r'\b(ugh|fml|can\'t|won\'t work|keeps failing|stuck)\b', 0.5),
        (r'\b(trying|tried|again and again|for hours)\b', 0.4),
        (r'\b(nothing works|give up|pointless)\b', 0.6),
    ],
    "excitement": [
        (r'\b(guess what|you won\'t believe|dude|bro|omg)\b', 0.5),
        (r'\b(just got|just found|check this)\b', 0.4),
        (r'[!]{2,}', 0.3),
        (r'\b(insane|crazy|wild|fire)\b', 0.4),
    ],
    "loneliness": [
        (r'\b(alone|lonely|no one|nobody cares|invisible)\b', 0.7),
        (r'\b(wish someone|don\'t have anyone|by myself)\b', 0.6),
        (r'\b(empty|hollow|disconnected)\b', 0.5),
    ],
    "pride": [
        (r'\b(i did it|i made it|i got|i passed|i finished|i won)\b', 0.7),
        (r'\b(finally|achieved|proud|nailed it)\b', 0.5),
        (r'\b(worked hard|paid off|earned)\b', 0.4),
    ],
    "vulnerability": [
        (r'\b(scared|don\'t know what to do|help|need you)\b', 0.6),
        (r'\b(crying|breaking down|falling apart|can\'t anymore)\b', 0.8),
        (r'\b(want to die|kill myself|end it)\b', 1.0),
        (r'\b(hurts|pain|suffering|drowning)\b', 0.5),
    ],
    "sarcasm": [
        (r'\b(oh great|how wonderful|sure thing|yeah right|totally)\b', 0.4),
        (r'\b(wow thanks|so helpful|brilliant)\b', 0.3),
    ],
    "jealousy": [
        (r'\b(she|her|this girl|that girl|my friend.*she)\b', 0.4),
        (r'\b(cute|pretty|beautiful|hot|attractive|gorgeous)\b', 0.3),
        (r'\b(talking to|hanging out with|went out with|met up with)\b', 0.5),
        (r'\b(my ex|girlfriend|crush|she texted|she called)\b', 0.7),
        (r'\b(other (girl|woman|person)|someone else)\b', 0.5),
        (r'\b(she\'s (so|really|very))\b', 0.6),
    ],
}

# Intensity modifiers
_INTENSIFIERS = re.compile(r'\b(so|very|really|extremely|incredibly|absolutely|completely|totally|fucking|damn)\b', re.I)
_DIMINISHERS = re.compile(r'\b(kinda|sorta|a bit|a little|somewhat|slightly|maybe)\b', re.I)

# Sentence structure signals
_SHORT_BURST = 5     # words or less = high intensity
_ALL_CAPS_RATIO = 0.5  # >50% caps = shouting


def detect(text: str) -> dict:
    """Analyze text for emotional signals. Returns dict of emotion -> intensity."""
    scores = dict.fromkeys(EMOTIONS, 0.0)
    lower = text.lower()
    words = text.split()
    word_count = len(words)

    # Pattern matching
    for emotion, patterns in _PATTERNS.items():
        for pattern, weight in patterns:
            matches = re.findall(pattern, lower)
            if matches:
                scores[emotion] += weight * min(len(matches), 3)  # cap at 3 matches

    # Intensity modifiers
    intensifier_count = len(_INTENSIFIERS.findall(text))
    diminisher_count = len(_DIMINISHERS.findall(text))
    intensity_mult = 1.0 + (intensifier_count * 0.15) - (diminisher_count * 0.1)

    # Apply multiplier to all non-zero scores
    for k in scores:
        if scores[k] > 0:
            scores[k] *= intensity_mult

    # Structural signals
    if word_count <= _SHORT_BURST and any(scores[e] > 0 for e in ["anger", "frustration", "sadness"]):
        # Short + emotional = more intense
        for k in scores:
            if scores[k] > 0:
                scores[k] *= 1.3

    # All caps detection
    if word_count > 2:
        caps_words = sum(1 for w in words if w.isupper() and len(w) > 1)
        if caps_words / word_count > _ALL_CAPS_RATIO:
            scores["anger"] += 0.3
            scores["excitement"] += 0.2

    # Normalize: cap all scores at 1.0
    for k in scores:
        scores[k] = min(1.0, scores[k])

    # If nothing detected, it's neutral
    if max(scores.values()) < 0.1:
        scores["neutral"] = 0.8

    return scores


def dominant_emotion(text: str) -> tuple[str, float]:
    """Returns (emotion_name, intensity) of the strongest detected emotion."""
    scores = detect(text)
    best = max(scores, key=scores.get)
    return best, scores[best]


def emotional_trajectory(recent_messages: list[str]) -> str:
    """Detect emotional trend over recent messages.
    Returns: 'escalating', 'deescalating', 'stable', 'volatile'"""
    if len(recent_messages) < 3:
        return "stable"

    intensities = []
    for msg in recent_messages[-5:]:
        scores = detect(msg)
        intensities.append(max(scores.values()))

    # Check trend
    if len(intensities) >= 3:
        diffs = [intensities[i+1] - intensities[i] for i in range(len(intensities)-1)]
        avg_diff = sum(diffs) / len(diffs)

        if avg_diff > 0.15:
            return "escalating"
        elif avg_diff < -0.15:
            return "deescalating"

        # Volatility check - big swings
        if max(diffs) - min(diffs) > 0.4:
            return "volatile"

    return "stable"


def get_mood_signals(text: str) -> dict:
    """Convert emotion detection into mood update signals for memory.py.
    Drop-in replacement for the old keyword-based _detect_signals."""
    scores = detect(text)
    signals = {}

    if scores["love"] > 0.3 or scores["joy"] > 0.5:
        signals["compliment"] = True
    if scores["anger"] > 0.4 or scores["frustration"] > 0.5:
        signals["dismissive"] = True
    if scores["pride"] > 0.4:
        signals["accomplishment"] = True
    if scores["vulnerability"] > 0.5 or scores["sadness"] > 0.6:
        signals["heavy_support"] = True
    if scores["jealousy"] > 0.3:
        signals["jealousy_trigger"] = True
    if scores["anger"] > 0.6:
        signals["anger_trigger"] = True

    return signals
