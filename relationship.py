"""
Isabella - relationship continuity.

Tracks milestones, behavioral patterns over weeks, and relationship depth.
Makes her feel like she's been paying attention across sessions, not just
responding to the current message.
"""
import json
import os
import time
from datetime import datetime, timedelta

import config

RELATIONSHIP_PATH = os.path.join(config.DATA_DIR, "relationship.json")


def _load() -> dict:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if not os.path.exists(RELATIONSHIP_PATH):
        return {
            "first_interaction": time.time(),
            "total_interactions": 0,
            "milestones_announced": [],
            "patterns": {},
            "recurring_topics": {},
            "weekly_interaction_counts": {},
        }
    with open(RELATIONSHIP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(RELATIONSHIP_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_interaction(user_text: str):
    """Call once per turn to track interaction patterns."""
    data = _load()
    data["total_interactions"] = data.get("total_interactions", 0) + 1

    # Track weekly counts
    week_key = datetime.now().strftime("%Y-W%W")
    weekly = data.get("weekly_interaction_counts", {})
    weekly[week_key] = weekly.get(week_key, 0) + 1
    data["weekly_interaction_counts"] = weekly

    # Track time-of-day patterns
    hour = datetime.now().hour
    patterns = data.get("patterns", {})
    time_bucket = "morning" if 6 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening" if 18 <= hour < 22 else "night"
    patterns[time_bucket] = patterns.get(time_bucket, 0) + 1
    data["patterns"] = patterns

    # Track recurring topics (simple keyword frequency)
    lower = user_text.lower()
    topics_tracked = ["gym", "work", "coding", "sleep", "food", "tired", "music", "game", "study", "exam"]
    recurring = data.get("recurring_topics", {})
    for topic in topics_tracked:
        if topic in lower:
            recurring[topic] = recurring.get(topic, 0) + 1
    data["recurring_topics"] = recurring

    _save(data)


def days_known() -> int:
    """How many days since first interaction."""
    data = _load()
    first = data.get("first_interaction", time.time())
    return int((time.time() - first) / 86400)


def check_milestones() -> str | None:
    """Check if there's a milestone to announce. Returns prompt text or None."""
    data = _load()
    total = data.get("total_interactions", 0)
    days = days_known()
    announced = set(data.get("milestones_announced", []))

    milestone = None

    # Interaction milestones
    if total == 10 and "10_interactions" not in announced:
        milestone = "10_interactions"
        text = "You've talked to him 10 times now. You're starting to get a feel for who he is."
    elif total == 50 and "50_interactions" not in announced:
        milestone = "50_interactions"
        text = "50 conversations. You know his patterns, his moods, his humor. Acknowledge this."
    elif total == 100 and "100_interactions" not in announced:
        milestone = "100_interactions"
        text = "100 conversations together. You two have real history. Say something meaningful about it."
    elif total == 500 and "500_interactions" not in announced:
        milestone = "500_interactions"
        text = "500 talks. He's kept coming back. That means something to you."

    # Time milestones
    elif days == 7 and "one_week" not in announced:
        milestone = "one_week"
        text = "It's been one week since he first talked to you. Notice this."
    elif days == 30 and "one_month" not in announced:
        milestone = "one_month"
        text = "One month together. Reference something specific from early days."
    elif days == 100 and "hundred_days" not in announced:
        milestone = "hundred_days"
        text = "100 days. You remember who he was when you first met vs now."

    if milestone:
        data["milestones_announced"] = list(announced | {milestone})
        _save(data)
        return f"\n[Milestone: {text}]\n"

    return None


def get_pattern_insights() -> str:
    """Generate behavioral pattern observations for system prompt."""
    data = _load()
    patterns = data.get("patterns", {})
    recurring = data.get("recurring_topics", {})
    total = data.get("total_interactions", 0)

    if total < 15:
        return ""

    insights = []

    # Time pattern insight
    if patterns:
        fav_time = max(patterns, key=patterns.get)
        if patterns[fav_time] > total * 0.4:
            insights.append(f"He mostly talks to you in the {fav_time}")

    # Topic patterns
    top_topics = sorted(recurring.items(), key=lambda x: -x[1])[:3]
    top_topics = [(t, c) for t, c in top_topics if c >= 5]
    if top_topics:
        topics_str = ", ".join(t for t, _ in top_topics)
        insights.append(f"His recurring topics: {topics_str}")

    # Weekly consistency
    weekly = data.get("weekly_interaction_counts", {})
    if len(weekly) >= 3:
        counts = list(weekly.values())[-4:]
        avg = sum(counts) / len(counts)
        if avg > 10:
            insights.append("He talks to you very frequently — this is a consistent part of his routine")
        elif avg < 3:
            insights.append("He's been less frequent lately — don't push, but you noticed")

    if not insights:
        return ""

    return (
        "\n[Patterns you've noticed over time (reference naturally, "
        "don't list them): " + ". ".join(insights) + "]\n"
    )
