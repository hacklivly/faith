"""
Faith - voice style.

Computes vocal parameters (rate, pitch) from mood, time of day, and
response type so her voice carries emotion rather than reading flat.
"""
from datetime import datetime

import timing


def compute(text: str, mood: dict) -> dict:
    """Returns rate and pitch offsets for edge-tts SSML."""
    hour = datetime.now().hour
    valence = mood.get("valence", 0.6)
    energy = mood.get("energy", 0.7)
    response_type = timing.classify_response(text)

    # Base from response type
    rate_pct = 0
    pitch_hz = 0

    if response_type == "excited":
        rate_pct = 15
        pitch_hz = 30
    elif response_type == "emotional":
        rate_pct = -12
        pitch_hz = -20
    elif response_type == "quick_agree":
        rate_pct = 10
        pitch_hz = 10
    elif response_type == "thinking":
        rate_pct = -8
        pitch_hz = -10

    # Mood modifiers
    if energy < 0.3:
        rate_pct -= 10
        pitch_hz -= 15
    elif energy > 0.8:
        rate_pct += 8
        pitch_hz += 10

    if valence < 0.3:
        rate_pct -= 5
        pitch_hz -= 10

    # Circadian drift
    if hour < 9:
        # Morning: slower, lower
        rate_pct -= 8
        pitch_hz -= 20
    elif 22 <= hour or hour < 4:
        # Late night: softer, slower
        rate_pct -= 12
        pitch_hz -= 25

    # Clamp to edge-tts limits
    rate_pct = max(-30, min(30, rate_pct))
    pitch_hz = max(-50, min(50, pitch_hz))

    return {"rate": f"{rate_pct:+d}%", "pitch": f"{pitch_hz:+d}Hz"}
