"""
Isabella - disfluency & vocal expression engine.

Injects natural speech imperfections to make her sound human, not scripted.
Max 2 modifications per response to avoid cluttering.
"""
import random
import re

# ═══ FILLERS ═══
FILLERS_START = [
    "hmm... ", "well... ", "so, ", "look, ", "right, ", "uh, ", "umm... ",
    "ah, ", "wait— ", "oh right, ", "hold on, ", "you know what, ", "actually, ",
    "listen, ", "okay so, ", "let me think... ", "mm, ",
]
FILLERS_MID = [
    " hmm, ", " um, ", " like, ", " I mean, ", " you know, ",
    " basically, ", " actually, ", " right, ", " wait, ",
]

HEDGES = ["maybe ", "I think ", "probably ", "perhaps ", "I guess ", "supposedly "]

TRAILING = [
    "...", "— never mind.", "— anyway.", "— forget it.", "— whatever.",
    "— actually no.", "— you know what, forget I said that.",
    "— hmm, where was I?", "— wait, what was I saying?",
]

# ═══ SELF-CORRECTIONS ═══
SELF_CORRECTIONS = [
    ("You should ", "You should— wait, "),
    ("I think ", "I think— no actually, "),
    ("It's ", "It's— I mean, "),
    ("That's ", "That's— hmm, "),
    ("Maybe ", "Maybe— no, definitely "),
    ("I was going to ", "I was going to— actually, "),
    ("The thing is ", "The thing is— wait no, "),
    ("I feel like ", "I feel like— or wait, "),
    ("Probably ", "Probably— no, "),
    ("You could ", "You could— hmm, or maybe "),
]

# ═══ VOCAL EXPRESSIONS (no asterisks) ═══
SOFT_LAUGHS = ["heh", "pfft", "hehe", "heh heh", "pff"]
BREATHS = ["...", "hmm...", "mm.", "..."]

# ═══ WORD ELONGATION (casual emphasis) ═══
ELONGATABLE = {
    "so": "sooo", "no": "nooo", "yes": "yesss", "hmm": "hmmmm",
    "oh": "ohhh", "well": "welll", "wait": "waait", "please": "pleease",
    "really": "reallyyy", "fine": "fiiine", "okay": "okaaay",
    "what": "whaat", "why": "whyyy", "stop": "stooop",
}

# ═══ ABANDONED THOUGHTS ═══
ABANDONED = [
    "— actually, never mind.",
    "— no, forget it.",
    "— ... you know what, it's nothing.",
    "— hmm. lost my train of thought.",
    "— wait. what was I saying?",
]


def add_disfluency(text: str, chance: float = 0.22) -> str:
    """Add natural speech imperfection. ~22% of responses get one modification."""
    if not text or len(text) < 10:
        return text
    if random.random() > chance:
        return text

    roll = random.random()

    if roll < 0.18:
        return random.choice(FILLERS_START) + text[0].lower() + text[1:]

    elif roll < 0.30:
        random.shuffle(SELF_CORRECTIONS)
        for old, new in SELF_CORRECTIONS:
            if old in text:
                return text.replace(old, new, 1)

    elif roll < 0.42:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 1:
            idx = random.randint(0, len(sentences) - 2)
            sentences[idx] = sentences[idx].rstrip('.!?') + random.choice(TRAILING)
            return " ".join(sentences)

    elif roll < 0.52:
        return random.choice(HEDGES) + text[0].lower() + text[1:]

    elif roll < 0.62:
        words = text.split()
        if len(words) > 6:
            pos = random.randint(3, len(words) - 3)
            words.insert(pos, random.choice(FILLERS_MID).strip())
            return " ".join(words)

    elif roll < 0.72:
        # Word elongation
        words = text.split()
        for i, w in enumerate(words):
            if w.lower().rstrip(".,!?") in ELONGATABLE:
                clean = w.lower().rstrip(".,!?")
                punct = w[len(clean):]
                words[i] = ELONGATABLE[clean] + punct
                return " ".join(words)

    elif roll < 0.82:
        # Soft laugh prefix
        if len(text) < 120:
            return random.choice(SOFT_LAUGHS) + "... " + text

    elif roll < 0.90:
        # Repeat first word (warm stutter)
        words = text.split()
        if len(words) > 3 and len(words[0]) > 2:
            words[0] = words[0] + "— " + words[0].lower()
            return " ".join(words)

    else:
        # Abandoned thought (insert in middle of multi-sentence)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 2:
            idx = random.randint(1, len(sentences) - 2)
            sentences[idx] = sentences[idx].rstrip('.!?') + random.choice(ABANDONED)
            return " ".join(sentences)

    return text


def add_laugh(text: str, chance: float = 0.07) -> str:
    """Sometimes add a small laugh."""
    if random.random() > chance or len(text) < 8:
        return text
    laugh = random.choice(SOFT_LAUGHS)
    if random.random() < 0.6:
        return laugh + "... " + text
    return text.rstrip('.!') + "... " + laugh


def add_thinking_pause(text: str, chance: float = 0.08) -> str:
    """Add a thinking pause at start."""
    if random.random() > chance or len(text) < 30:
        return text
    pause = random.choice(["hmm... ", "mm... ", "... ", "let me think... ", "one sec... "])
    return pause + text[0].lower() + text[1:]


def humanize(text: str) -> str:
    """Apply at most 2 humanization layers to avoid over-cluttering."""
    mods = 0
    if mods < 2 and random.random() < 0.22:
        text = add_disfluency(text, chance=1.0)
        mods += 1
    if mods < 2 and random.random() < 0.07:
        text = add_laugh(text, chance=1.0)
        mods += 1
    if mods < 2 and random.random() < 0.08:
        text = add_thinking_pause(text, chance=1.0)
        mods += 1
    return text
