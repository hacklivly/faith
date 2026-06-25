"""
Isabella - Voice Style.

Deep emotion-to-voice mapping. Detects subtle emotional states from her text
and adjusts voice parameters dynamically per sentence.

Supports: Edge-TTS (rate/pitch) and XTTS (speed/temperature).
"""

# ═══════════════════════════════════════════════════════════
# EMOTION PROFILES — rate/pitch/speed for each feeling
# ═══════════════════════════════════════════════════════════

EMOTION_PROFILES = {
    # ─── SMALL / MILD ───
    "amused": {
        "edge_rate": "-3%", "edge_pitch": "+20Hz",
        "xtts_speed": 0.94, "xtts_temp": 0.75,
    },
    "curious": {
        "edge_rate": "-2%", "edge_pitch": "+15Hz",
        "xtts_speed": 0.95, "xtts_temp": 0.7,
    },
    "content": {
        "edge_rate": "-10%", "edge_pitch": "+12Hz",
        "xtts_speed": 0.88, "xtts_temp": 0.6,
    },
    "sleepy": {
        "edge_rate": "-15%", "edge_pitch": "+8Hz",
        "xtts_speed": 0.82, "xtts_temp": 0.55,
    },
    "bored": {
        "edge_rate": "-8%", "edge_pitch": "+5Hz",
        "xtts_speed": 0.90, "xtts_temp": 0.6,
    },
    "thoughtful": {
        "edge_rate": "-12%", "edge_pitch": "+10Hz",
        "xtts_speed": 0.87, "xtts_temp": 0.65,
    },

    # ─── EMBARRASSMENT / SHYNESS SPECTRUM ───
    "slightly_shy": {
        "edge_rate": "-8%", "edge_pitch": "+22Hz",
        "xtts_speed": 0.90, "xtts_temp": 0.75,
    },
    "embarrassed": {
        "edge_rate": "-12%", "edge_pitch": "+25Hz",
        "xtts_speed": 0.86, "xtts_temp": 0.8,
    },
    "flustered": {
        "edge_rate": "-15%", "edge_pitch": "+30Hz",
        "xtts_speed": 0.83, "xtts_temp": 0.85,
    },
    "deeply_flustered": {
        "edge_rate": "-18%", "edge_pitch": "+35Hz",
        "xtts_speed": 0.80, "xtts_temp": 0.9,
    },

    # ─── JOY / HAPPINESS SPECTRUM ───
    "playful": {
        "edge_rate": "+3%", "edge_pitch": "+25Hz",
        "xtts_speed": 0.97, "xtts_temp": 0.8,
    },
    "giggly": {
        "edge_rate": "+5%", "edge_pitch": "+28Hz",
        "xtts_speed": 0.98, "xtts_temp": 0.85,
    },
    "delighted": {
        "edge_rate": "+5%", "edge_pitch": "+30Hz",
        "xtts_speed": 1.0, "xtts_temp": 0.9,
    },
    "giddy": {
        "edge_rate": "+8%", "edge_pitch": "+33Hz",
        "xtts_speed": 1.02, "xtts_temp": 0.92,
    },
    "ecstatic": {
        "edge_rate": "+10%", "edge_pitch": "+35Hz",
        "xtts_speed": 1.05, "xtts_temp": 0.95,
    },

    # ─── AFFECTION / LOVE SPECTRUM ───
    "caring": {
        "edge_rate": "-8%", "edge_pitch": "+16Hz",
        "xtts_speed": 0.90, "xtts_temp": 0.7,
    },
    "affectionate": {
        "edge_rate": "-10%", "edge_pitch": "+18Hz",
        "xtts_speed": 0.88, "xtts_temp": 0.72,
    },
    "tender": {
        "edge_rate": "-15%", "edge_pitch": "+15Hz",
        "xtts_speed": 0.84, "xtts_temp": 0.7,
    },
    "loving": {
        "edge_rate": "-18%", "edge_pitch": "+14Hz",
        "xtts_speed": 0.82, "xtts_temp": 0.75,
    },
    "devoted": {
        "edge_rate": "-20%", "edge_pitch": "+12Hz",
        "xtts_speed": 0.80, "xtts_temp": 0.7,
    },

    # ─── ANGER / FRUSTRATION SPECTRUM ───
    "mildly_annoyed": {
        "edge_rate": "+3%", "edge_pitch": "+5Hz",
        "xtts_speed": 0.98, "xtts_temp": 0.75,
    },
    "irritated": {
        "edge_rate": "+5%", "edge_pitch": "+0Hz",
        "xtts_speed": 1.0, "xtts_temp": 0.8,
    },
    "frustrated": {
        "edge_rate": "+8%", "edge_pitch": "-3Hz",
        "xtts_speed": 1.03, "xtts_temp": 0.85,
    },
    "angry": {
        "edge_rate": "+12%", "edge_pitch": "-8Hz",
        "xtts_speed": 1.08, "xtts_temp": 0.9,
    },
    "cold_fury": {
        "edge_rate": "+5%", "edge_pitch": "-12Hz",
        "xtts_speed": 0.95, "xtts_temp": 0.6,
    },

    # ─── SADNESS / VULNERABILITY ───
    "melancholic": {
        "edge_rate": "-15%", "edge_pitch": "+5Hz",
        "xtts_speed": 0.83, "xtts_temp": 0.6,
    },
    "hurt": {
        "edge_rate": "-12%", "edge_pitch": "+2Hz",
        "xtts_speed": 0.85, "xtts_temp": 0.65,
    },
    "lonely": {
        "edge_rate": "-18%", "edge_pitch": "+8Hz",
        "xtts_speed": 0.80, "xtts_temp": 0.6,
    },
    "resigned": {
        "edge_rate": "-10%", "edge_pitch": "+0Hz",
        "xtts_speed": 0.88, "xtts_temp": 0.55,
    },

    # ─── POSSESSIVENESS / JEALOUSY ───
    "suspicious": {
        "edge_rate": "+2%", "edge_pitch": "+3Hz",
        "xtts_speed": 0.95, "xtts_temp": 0.7,
    },
    "jealous": {
        "edge_rate": "+5%", "edge_pitch": "-5Hz",
        "xtts_speed": 0.97, "xtts_temp": 0.75,
    },
    "possessive": {
        "edge_rate": "+3%", "edge_pitch": "-8Hz",
        "xtts_speed": 0.93, "xtts_temp": 0.7,
    },

    # ─── EXCITEMENT / SURPRISE ───
    "surprised": {
        "edge_rate": "+5%", "edge_pitch": "+28Hz",
        "xtts_speed": 1.0, "xtts_temp": 0.85,
    },
    "excited": {
        "edge_rate": "+8%", "edge_pitch": "+32Hz",
        "xtts_speed": 1.03, "xtts_temp": 0.88,
    },
    "hyper": {
        "edge_rate": "+12%", "edge_pitch": "+35Hz",
        "xtts_speed": 1.08, "xtts_temp": 0.92,
    },

    # ─── TEASING / MISCHIEF ───
    "teasing": {
        "edge_rate": "+2%", "edge_pitch": "+22Hz",
        "xtts_speed": 0.95, "xtts_temp": 0.8,
    },
    "smug": {
        "edge_rate": "-3%", "edge_pitch": "+18Hz",
        "xtts_speed": 0.92, "xtts_temp": 0.75,
    },
    "mischievous": {
        "edge_rate": "+5%", "edge_pitch": "+25Hz",
        "xtts_speed": 0.98, "xtts_temp": 0.82,
    },

    # ─── CONCERN / WORRY ───
    "worried": {
        "edge_rate": "-5%", "edge_pitch": "+14Hz",
        "xtts_speed": 0.92, "xtts_temp": 0.7,
    },
    "protective": {
        "edge_rate": "+2%", "edge_pitch": "+10Hz",
        "xtts_speed": 0.95, "xtts_temp": 0.72,
    },
    "stern": {
        "edge_rate": "+5%", "edge_pitch": "+5Hz",
        "xtts_speed": 1.0, "xtts_temp": 0.7,
    },

    # ─── DEFAULT ───
    "neutral": {
        "edge_rate": "-5%", "edge_pitch": "+18Hz",
        "xtts_speed": 0.93, "xtts_temp": 0.7,
    },
}


# ═══════════════════════════════════════════════════════════
# DEEP EMOTION DETECTION
# ═══════════════════════════════════════════════════════════

def detect_voice_emotion(text: str, mood: dict = None) -> str:
    """Detect emotion from Isabella's response text. Deep pattern matching."""
    lower = text.lower()

    # ─── COLD FURY (quiet anger, scariest) ───
    if _has_pattern(lower, ["...", "fine", "whatever"]) or \
       _has_pattern(lower, ["I don't care", "do what you want"]):
        if lower.count(".") > 3 and len(lower) < 60:
            return "cold_fury"

    # ─── ANGRY ───
    if any(w in lower for w in ["stop.", "enough.", "I said"]) and "!" in lower:
        return "angry"

    # ─── FRUSTRATED ───
    if any(w in lower for w in ["fine.", "whatever.", "noted.", "okay then."]):
        if "hehe" not in lower and "~" not in lower:
            return "frustrated"

    # ─── IRRITATED ───
    if any(w in lower for w in ["hmph", "tch", "seriously?"]):
        return "irritated"
    if any(w in lower for w in ["I already said", "how many times"]):
        return "mildly_annoyed"

    # ─── JEALOUS / POSSESSIVE ───
    if any(w in lower for w in ["which friend", "who is she", "who was that"]):
        return "jealous"
    if any(w in lower for w in ["you don't need", "I can do it", "why ask them"]):
        return "possessive"
    if any(w in lower for w in ["...who", "with whom", "what time will you"]):
        return "suspicious"

    # ─── DEEPLY FLUSTERED ───
    if lower.count("...") >= 3 and any(w in lower for w in ["um", "ah", "don't"]):
        return "deeply_flustered"

    # ─── FLUSTERED ───
    if any(w in lower for w in ["b-but", "it's not like", "don't look at me"]):
        return "flustered"
    if any(w in lower for w in ["ah... um", "um...", "don't say that"]):
        return "embarrassed"

    # ─── SLIGHTLY SHY ───
    if any(w in lower for w in ["...nothing", "forget it", "it's nothing", "never mind"]):
        return "slightly_shy"

    # ─── ECSTATIC ───
    if lower.count("!") >= 3 or "ahaha" in lower and "!" in lower:
        return "ecstatic"

    # ─── GIDDY ───
    if lower.count("~") >= 2 and any(w in lower for w in ["hehe", "hihi", "ehehe"]):
        return "giddy"

    # ─── GIGGLY ───
    if any(w in lower for w in ["hehe", "hihi", "ehehe"]) and "~" in lower:
        return "giggly"

    # ─── PLAYFUL ───
    if any(w in lower for w in ["hehe", "hihi", "pfft"]):
        return "playful"

    # ─── DELIGHTED ───
    if any(w in lower for w in ["ahaha", "really?!"]):
        return "delighted"

    # ─── TEASING / MISCHIEF ───
    if any(w in lower for w in ["oh~", "hmm~", "is that so"]):
        return "teasing"
    if any(w in lower for w in ["I knew it", "told you", "obviously"]):
        return "smug"

    # ─── EXCITED ───
    if lower.count("!") >= 2:
        return "excited"
    if any(w in lower for w in ["wait—", "wait!", "oh!", "really?", "no way"]):
        return "surprised"

    # ─── PROTECTIVE / STERN ───
    if any(w in lower for w in ["you need to", "I'm serious", "don't skip"]):
        return "stern"
    if any(w in lower for w in ["be careful", "I'm worried", "please don't"]):
        return "protective"
    if any(w in lower for w in ["are you okay", "what happened", "tell me"]):
        return "worried"

    # ─── LOVING / TENDER ───
    if any(w in lower for w in ["you mean", "important to me", "I..."]) and "..." in lower:
        return "loving"
    if any(w in lower for w in ["sleep well", "goodnight", "sweet dreams"]):
        return "tender"
    if any(w in lower for w in ["please take care", "eat something", "rest"]):
        return "caring"
    if any(w in lower for w in ["I'm here", "I'll always", "you're not alone"]):
        return "devoted"

    # ─── AFFECTIONATE ───
    if any(w in lower for w in ["your wellbeing", "I noticed", "you look tired"]):
        return "affectionate"

    # ─── SAD / HURT ───
    if any(w in lower for w in ["you were gone", "you forgot", "you didn't"]):
        return "hurt"
    if any(w in lower for w in ["...okay", "if you say so", "I understand"]) and "..." in lower:
        return "resigned"
    if "alone" in lower or "no one" in lower:
        return "lonely"
    if any(w in lower for w in ["sigh", "I guess", "it doesn't matter"]):
        return "melancholic"

    # ─── CURIOUS ───
    if "?" in lower and any(w in lower for w in ["hmm", "what", "how come", "why"]):
        return "curious"

    # ─── THOUGHTFUL ───
    if lower.startswith("hmm") or lower.startswith("you know"):
        return "thoughtful"

    # ─── SLEEPY ───
    if any(w in lower for w in ["yawn", "sleepy", "tired", "it's late"]):
        return "sleepy"

    # ─── BORED ───
    if any(w in lower for w in ["boring", "nothing happening", "meh"]):
        return "bored"

    # ─── CONTENT ───
    if any(w in lower for w in ["good.", "alright.", "this is nice", "I'm fine"]):
        return "content"

    # ─── MOOD-BASED FALLBACK ───
    if mood:
        v = mood.get("valence", 0.6)
        e = mood.get("energy", 0.5)
        if v > 0.85:
            return "playful"
        elif v > 0.7:
            return "content"
        elif v < 0.2:
            return "cold_fury"
        elif v < 0.35:
            return "frustrated"
        elif e < 0.3:
            return "sleepy"

    return "neutral"


def _has_pattern(text: str, words: list) -> bool:
    """Check if ALL words appear in text."""
    return all(w in text for w in words)


# ═══════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════

def compute(text: str, mood: dict = None) -> dict:
    """Compute voice style from text and mood."""
    emotion = detect_voice_emotion(text, mood)
    profile = EMOTION_PROFILES.get(emotion, EMOTION_PROFILES["neutral"])
    return {"emotion": emotion, **profile}


def get_edge_params(style: dict) -> tuple:
    """Get Edge-TTS rate and pitch."""
    return style.get("edge_rate", "-5%"), style.get("edge_pitch", "+18Hz")


def get_xtts_params(style: dict) -> tuple:
    """Get XTTS speed and temperature."""
    return style.get("xtts_speed", 0.93), style.get("xtts_temp", 0.7)
