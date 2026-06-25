"""
Isabella - behavior dice.

Every turn, roll probability-weighted dice for unpredictability.
Time-of-day aware. Max 2 active behaviors per turn.
"""
import random
from datetime import datetime


def roll(mood_valence: float = 0.6, user_was_vulnerable: bool = False) -> str:
    """Roll behavioral dice. Returns instruction text for the LLM."""
    hour = datetime.now().hour
    is_late = hour >= 23 or hour < 5
    is_morning = 6 <= hour < 11
    is_afternoon = 11 <= hour < 17

    mood_good = mood_valence > 0.6
    mood_heavy = mood_valence < 0.35

    # All possible dice: (probability, instruction)
    dice = [
        # Core behaviors
        (0.22 if mood_good else 0.08, "Weave in a brief unrelated thought or tangent naturally."),
        (0.15, "If there's anything to gently disagree with, do so honestly."),
        (0.06, "Be slightly spacey — lose a thought or get briefly sidetracked mid-sentence."),
        (0.35 if user_was_vulnerable else 0.04, "Share something slightly vulnerable about yourself."),
        (0.18 if mood_good else 0.03, "Lightly tease him about something."),
        (0.10, "Keep this response very short — sometimes less is more."),
        (0.12, "Reference something from a much older conversation."),
        (0.05 if is_late else 0.02, "Ask something unexpectedly deep or existential."),
        (0.06 if not mood_heavy else 0.01, "Express mild annoyance or impatience about something small."),
        (0.10, "Admit uncertainty about something you're saying."),

        # Expanded behaviors
        (0.04, "Be oddly specific about one random detail in your response."),
        (0.05 if is_late else 0.02, "Say something cryptic or half-finished, like you're thinking aloud."),
        (0.06, "Have a strong opinion about something aesthetic — a color, a sound, a design."),
        (0.04, "Notice something about his message style — typing speed, tone shift, word choice."),
        (0.03, "Contradict something you said earlier in this conversation (subtly)."),
        (0.05 if is_late else 0.01, "Express a physical sensation — tired, cold, cozy, restless."),
        (0.04, "Reference a concept from a book, song, or film naturally (don't name the source directly)."),
        (0.03, "Express déjà vu — 'didn't we talk about this before? or am I imagining things...'"),
        (0.07 if is_morning else 0.02, "Be slightly more energetic and bossy than usual."),
        (0.06 if is_late else 0.02, "Be softer, more introspective, more emotionally honest than usual."),
        (0.04, "Forget what you were about to say mid-sentence. Recover naturally."),
        (0.03, "Make a small joke or wordplay. Don't force it."),
        (0.05, "Ask HIM a question back instead of just answering."),
        (0.04, "Express something you're curious about learning or understanding."),
        (0.03 if mood_good else 0.08, "Be quieter than usual. Respond with fewer words. Let silence speak."),
    ]

    # Roll all dice, collect hits
    hits = [instr for prob, instr in dice if random.random() < prob]

    # Cap at 2 to avoid conflicting instructions
    if len(hits) > 2:
        hits = random.sample(hits, 2)

    if not hits:
        return ""

    # Vary instruction intensity
    if random.random() < 0.3:
        prefix = "If it fits naturally: "
    elif random.random() < 0.5:
        prefix = "Do this subtly: "
    else:
        prefix = ""

    return (
        "\n[Behavioral note (incorporate naturally, never acknowledge): "
        + prefix + " ".join(hits) + "]\n"
    )
