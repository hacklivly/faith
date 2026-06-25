"""Isabella - Deep Thoughts. Generates fresh fascinating thoughts using LLM."""
import random

import brain

TOPICS = [
    "galaxies, black holes, or the scale of the universe",
    "mathematics — infinity, paradoxes, or beautiful equations",
    "how the human brain works — neurons, consciousness, memory, or dreams",
    "quantum physics — entanglement, wave collapse, or time dilation",
    "evolution, DNA, or how life emerged from nothing",
    "the nature of time — why it moves forward, relativity, or time perception",
    "stars — how they're born, die, or become neutron stars and black holes",
    "human psychology — why we think the way we do, biases, or decision-making",
    "the deep ocean — what lives there, pressure, or unexplored darkness",
    "artificial intelligence — consciousness, thinking machines, or the singularity",
    "dimensions — what a 4th spatial dimension would look like",
    "entropy — why everything falls apart, heat death of the universe",
    "light — photons experiencing zero time, the speed limit of reality",
    "the human body — how it repairs itself, immune system battles, or aging",
    "music and math — why certain frequencies feel emotional",
]


def get_random_thought() -> str:
    """Generate a fresh thought using LLM on a random topic."""
    topic = random.choice(TOPICS)
    prompt = (
        "Generate ONE short fascinating fact or thought about: " + topic + ". "
        "Make it 1-2 sentences max. Sound like a curious girl sharing something she just thought of. "
        "Start with 'master...' or 'hmm...' or 'did you know...'. Be genuinely fascinated. "
        "No emojis. No stage directions. Just the thought."
    )
    try:
        thought = brain.get_reply(prompt, [])
        return thought.strip()
    except Exception:
        # Fallback static thoughts
        fallback = [
            "master... if you could fall into a black hole, time would stretch so much you'd see the entire future of the universe.",
            "hmm... your brain makes decisions 7 seconds before you're aware of them. are you really choosing?",
            "did you know... there are more possible chess games than atoms in the observable universe?",
        ]
        return random.choice(fallback)


def get_thought_prompt() -> str:
    """Return a system prompt injection for sharing a thought naturally."""
    topic = random.choice(TOPICS)
    return (
        f"\n[You just thought of something fascinating about {topic}. "
        f"Share it with master as your own thought — 1-2 sentences. Sound genuinely curious and fascinated. "
        f"Start naturally with 'master...' or 'hmm...' or 'you know what I was thinking...']\n"
    )
