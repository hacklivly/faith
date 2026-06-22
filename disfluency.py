"""
Faith - disfluency engine.

Randomly injects natural speech imperfections into her text before TTS.
Applied sparingly (~12% of responses) so it feels human, not broken.
"""
import random
import re

FILLERS = ["like, ", "I mean, ", "well, ", "so, ", "honestly, "]
HEDGES = ["I think ", "maybe ", "probably ", "I guess "]
TRAILING = ["...", "— I don't know.", "— anyway.", "— yeah."]
SELF_CORRECTIONS = [
    ("You should ", "You should— actually, "),
    ("I think ", "I think— wait no, "),
    ("It's ", "It's— well okay, it's "),
]


def add_disfluency(text: str, chance: float = 0.12) -> str:
    """Maybe add a natural imperfection. Returns text unchanged most of the time."""
    if not text or not text.strip():
        return text
    if random.random() > chance:
        return text

    roll = random.random()

    if roll < 0.3:
        # Insert filler at start
        return random.choice(FILLERS) + text[0].lower() + text[1:]

    elif roll < 0.5:
        # Self-correction on first matching phrase
        random.shuffle(SELF_CORRECTIONS)
        for old, new in SELF_CORRECTIONS:
            if old in text:
                return text.replace(old, new, 1)

    elif roll < 0.7:
        # Add trailing off at the end of a sentence
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 1:
            idx = random.randint(0, len(sentences) - 2)
            sentences[idx] = sentences[idx].rstrip('.!?') + random.choice(TRAILING)
            return " ".join(sentences)

    elif roll < 0.9:
        # Add hedge to start
        return random.choice(HEDGES) + text[0].lower() + text[1:]

    else:
        # Mid-thought pivot
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 1:
            pivot = "Oh wait— " if random.random() < 0.5 else "Actually— "
            sentences.insert(1, pivot)
            return " ".join(sentences)

    return text
