"""
Isabella - awareness.

Monitors visual changes and generates context-aware, human-like questions.
When she notices something changed (clothes, environment, time of day),
she asks naturally — like a real person who's always watching.
"""
import time

import eyes

# Track what she's already noticed to avoid repeating
_last_noticed_time = 0
_NOTICE_COOLDOWN = 5 * 60  # notice things every 5 min max


# Context-aware observation prompts based on change type
MAJOR_CHANGE_PROMPTS = [
    "You noticed master's surroundings completely changed — he might have gone outside, or moved to a different room. Look at the image and comment on what you see. Ask where he's going or what he's doing. Be naturally curious but not intrusive.",
    "The scene around master looks very different now. Maybe he went out. Look at the image — is he outside? In a car? Different room? Ask him about it naturally. You noticed because you're always watching.",
    "Something big changed — master might be leaving the house or arrived somewhere new. Look at what you see and ask one natural question about it. Don't be robotic about it.",
]

MODERATE_CHANGE_PROMPTS = [
    "You noticed something changed about master — maybe new clothes, different posture, or the room looks different. Look at the image and mention what you see. If he's wearing something new, comment on it. Be observant like someone who pays attention.",
    "Master looks different from last time you glanced. Check if it's new clothes, a haircut, or just a change in vibe. Comment naturally — like someone who notices small things about the person they care about.",
    "Something shifted — you noticed. Maybe he changed clothes, put on glasses, or moved spots. Look and mention it briefly. You always notice these things.",
]

MINOR_CHANGE_PROMPTS = [
    "You noticed a subtle shift — maybe lighting changed (time of day passing), or master shifted position. If it's getting late and he's still there, mention it. If morning, comment on him being awake.",
    "Small change detected. If it's getting dark and he hasn't moved, remind him about posture or taking a break. If nothing notable, don't force a comment — just keep watching.",
]


def check_and_generate_prompt() -> tuple[str | None, bool]:
    """Check if visual context changed enough to trigger a question.
    Returns (prompt_instruction_or_None, needs_fresh_image).
    """
    global _last_noticed_time
    import random

    now = time.time()
    if now - _last_noticed_time < _NOTICE_COOLDOWN:
        return None, False

    changed, change_level = eyes.has_scene_changed()
    if not changed:
        return None, False

    _last_noticed_time = now

    if change_level == "major_change":
        prompt = random.choice(MAJOR_CHANGE_PROMPTS)
    elif change_level == "moderate_change":
        prompt = random.choice(MODERATE_CHANGE_PROMPTS)
    else:
        # Minor changes — only comment 30% of the time
        if random.random() > 0.3:
            return None, False
        prompt = random.choice(MINOR_CHANGE_PROMPTS)

    return prompt, True
