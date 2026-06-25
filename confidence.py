"""Isabella - Confidence Scoring. Rate certainty before answering."""

# Keywords that suggest high/low confidence situations
LOW_CONFIDENCE_TRIGGERS = [
    "exact date", "specific number", "how many exactly",
    "what year", "who invented", "scientific name",
    "stock price", "weather", "news today",
    "latest version", "current score",
]

HIGH_CONFIDENCE_TRIGGERS = [
    "how are you", "what do you think", "tell me about",
    "open", "play", "close", "volume", "search",
    "remind me", "set timer", "screenshot",
]

def score(user_text: str, reply: str = "") -> float:
    """Score confidence 0.0-1.0. Low = should ask clarification or hedge."""
    lower = user_text.lower()
    score = 0.7  # default

    # Low confidence: factual questions that might be wrong
    for trigger in LOW_CONFIDENCE_TRIGGERS:
        if trigger in lower:
            score -= 0.2

    # High confidence: opinion/action requests
    for trigger in HIGH_CONFIDENCE_TRIGGERS:
        if trigger in lower:
            score += 0.15

    # Very short user input = ambiguous
    if len(user_text.split()) < 3:
        score -= 0.1

    # If reply contains hedging language, already expressing uncertainty
    if reply:
        hedges = ["maybe", "shayad", "I think", "probably", "not sure"]
        if any(h in reply.lower() for h in hedges):
            score -= 0.1

    return max(0.0, min(1.0, score))

def should_ask_clarification(user_text: str) -> str | None:
    """If confidence is very low, return a clarification question. Else None."""
    s = score(user_text)
    if s < 0.4:
        lower = user_text.lower()
        if len(user_text.split()) < 3:
            return "master, could you explain a bit more? I didn't quite understand."
        return None
    return None
