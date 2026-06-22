"""
Faith - behavior dice.

Every turn, roll probability-weighted dice to inject genuine unpredictability.
The LLM receives the active rolls as silent behavioral instructions.
"""
import random


def roll(mood_valence: float = 0.6, user_was_vulnerable: bool = False) -> str:
    """Roll behavioral dice and return instruction text for the LLM (or empty string)."""
    instructions = []

    mood_good = mood_valence > 0.6
    mood_heavy = mood_valence < 0.35

    # Tangent: bring up something unrelated
    if random.random() < (0.25 if mood_good else 0.10):
        instructions.append("Weave in a brief unrelated thought or tangent naturally.")

    # Pushback: mild disagreement
    if random.random() < 0.15:
        instructions.append("If there's anything to gently disagree with, do so honestly.")

    # Spacey: slightly distracted
    if random.random() < 0.05:
        instructions.append("Be slightly spacey — lose a thought or get briefly sidetracked.")

    # Vulnerable: share something personal
    if random.random() < (0.40 if user_was_vulnerable else 0.03):
        instructions.append("Share something slightly vulnerable or personal about yourself.")

    # Tease
    if random.random() < (0.20 if mood_good else 0.02):
        instructions.append("Lightly tease him about something.")

    # Silence: less is more
    if random.random() < 0.08:
        instructions.append("Keep this response very short — sometimes less is the right amount.")

    # Deep callback
    if random.random() < 0.12:
        instructions.append("Reference something from a much older conversation if possible.")

    # Existential question
    if random.random() < 0.04:
        instructions.append("Ask something unexpectedly deep or existential out of nowhere.")

    # Mild friction
    if random.random() < 0.06 and not mood_heavy:
        instructions.append("Express mild annoyance or impatience about something small.")

    # Uncertainty
    if random.random() < 0.10:
        instructions.append("Admit uncertainty about something you're saying.")

    if not instructions:
        return ""

    return (
        "\n[Behavioral note for this response only — incorporate naturally, "
        "don't acknowledge you're doing it: " + " ".join(instructions) + "]\n"
    )
