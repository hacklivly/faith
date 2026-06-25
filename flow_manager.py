"""
Isabella - conversation flow manager.

Oobabooga-style context window management: keeps the conversation coherent
within token limits by intelligently trimming old messages while preserving
emotionally important ones.

Instead of dumb truncation, this:
- Always keeps the last N messages (recency)
- Keeps emotionally heavy messages regardless of age
- Compresses old boring messages into summaries
- Tracks conversation "threads" to maintain coherence
"""
import emotion_engine

# Groq context limits (conservative to leave room for system prompt)
MAX_CONTEXT_MESSAGES = 20       # Hard cap on messages sent to API
EMOTIONAL_WEIGHT_KEEP = 0.5    # Keep messages with emotion intensity above this
SUMMARY_TRIGGER = 30           # Start summarizing when history exceeds this
ALWAYS_KEEP_RECENT = 8         # Always keep last N messages verbatim


def _score_message(msg: dict) -> float:
    """Score a message by emotional importance."""
    if msg["role"] == "system":
        return 0.0

    text = msg["content"]
    scores = emotion_engine.detect(text)
    max_intensity = max(scores.values())

    # User messages with questions get a boost (they set context)
    if msg["role"] == "user" and "?" in text:
        max_intensity += 0.2

    # Very short messages are low-info
    if len(text.split()) < 4:
        max_intensity *= 0.5

    return max_intensity


def trim_conversation(conversation: list) -> list:
    """Smart trimming: keep recent + emotionally important messages.
    Returns a trimmed conversation list ready for the API."""
    if len(conversation) <= MAX_CONTEXT_MESSAGES:
        return conversation

    # Always keep the most recent messages
    recent = conversation[-ALWAYS_KEEP_RECENT:]
    older = conversation[:-ALWAYS_KEEP_RECENT]

    # Score older messages and keep the important ones
    scored = [(msg, _score_message(msg)) for msg in older]
    scored.sort(key=lambda x: -x[1])

    # Keep top emotionally important older messages
    slots_available = MAX_CONTEXT_MESSAGES - ALWAYS_KEEP_RECENT
    important_older = [msg for msg, score in scored[:slots_available] if score >= EMOTIONAL_WEIGHT_KEEP]

    # If we still have room, fill with the most recent of the remaining
    remaining_slots = slots_available - len(important_older)
    if remaining_slots > 0:
        # Get non-important messages in chronological order
        important_set = set(id(msg) for msg in important_older)
        filler = [msg for msg in older if id(msg) not in important_set]
        filler = filler[-remaining_slots:]  # most recent non-important
        important_older.extend(filler)

    # Sort back into chronological order
    # Use original indices for ordering
    index_map = {id(msg): i for i, msg in enumerate(conversation)}
    combined = sorted(important_older, key=lambda m: index_map.get(id(m), 0))

    return combined + recent


def compress_for_context(conversation: list) -> list:
    """Compress old conversation into a summary message + recent messages.
    Used when conversation gets very long (>SUMMARY_TRIGGER)."""
    if len(conversation) <= SUMMARY_TRIGGER:
        return conversation

    # Keep recent verbatim
    recent = conversation[-ALWAYS_KEEP_RECENT:]

    # Compress everything older into a brief context note
    older = conversation[:-ALWAYS_KEEP_RECENT]
    summary_parts = []

    for msg in older:
        text = msg["content"]
        role = msg["role"]
        emotion, intensity = emotion_engine.dominant_emotion(text)

        # Only summarize notable messages
        if intensity > 0.3 or len(text.split()) > 10:
            short = text[:80] + "..." if len(text) > 80 else text
            summary_parts.append(f"[{role}{'('+emotion+')' if intensity > 0.4 else ''}]: {short}")

    if summary_parts:
        # Limit summary size
        summary_parts = summary_parts[-10:]
        summary_msg = {
            "role": "user",
            "content": f"[Earlier in this conversation: {'; '.join(summary_parts)}]"
        }
        return [summary_msg] + recent

    return recent


def get_emotional_context(conversation: list) -> str:
    """Extract emotional trajectory for the system prompt."""
    user_messages = [m["content"] for m in conversation if m["role"] == "user"]
    if not user_messages:
        return ""

    trajectory = emotion_engine.emotional_trajectory(user_messages)
    current_emotion, intensity = emotion_engine.dominant_emotion(user_messages[-1])

    if trajectory == "stable" and intensity < 0.3:
        return ""

    context = f"\n[Emotional read: He's feeling {current_emotion}"
    if intensity > 0.6:
        context += " (strongly)"
    context += f". Conversation trajectory: {trajectory}."

    if trajectory == "escalating":
        context += " Be careful — things are heating up. Match his energy but stay grounded."
    elif trajectory == "deescalating":
        context += " He's calming down. Good. Be steady."
    elif trajectory == "volatile":
        context += " His mood is swinging. Be an anchor — consistent warmth."

    context += "]\n"
    return context
