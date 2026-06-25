"""
Isabella - the brain.

Talks to Groq's free-tier API for reasoning, vision, and journaling.
Supports streaming for faster first-word latency.
"""
import json
import re
import time
from datetime import datetime

from openai import OpenAI

import config

_client = None
_journal_client = None
_vision_client = None

def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.KEY_BRAIN, base_url=config.GROQ_BASE_URL)
    return _client

def _get_journal_client():
    global _journal_client
    if _journal_client is None:
        _journal_client = OpenAI(api_key=config.KEY_JOURNAL, base_url=config.GROQ_BASE_URL)
    return _journal_client

def _get_vision_client():
    global _vision_client
    if _vision_client is None:
        _vision_client = OpenAI(api_key=config.KEY_VISION, base_url=config.GROQ_BASE_URL)
    return _vision_client

# System prompt cache - only rebuild when mood/journal changes
_cached_prompt = None
_cached_prompt_hash = None


def _inject_realtime(system_prompt: str) -> str:
    """Append current timestamp to system prompt so Isabella always knows the time."""
    now = datetime.now()
    return system_prompt + f"\n[CURRENT TIMESTAMP: {now.strftime('%A, %B %d, %Y — %I:%M %p')}]\n"


def _sentence_boundary(text):
    """Split text into sentences as they arrive during streaming."""
    # Match sentence-ending punctuation followed by space or end
    parts = re.split(r'(?<=[.!?…—])\s+', text)
    return parts


FALLBACK_MODEL = "llama-3.1-8b-instant"  # faster, smaller, rarely rate-limited


def get_reply_stream(system_prompt: str, conversation: list, image_base64: str = None):
    """Generator that yields complete sentences as they stream in.
    Falls back to smaller model on rate limit."""
    messages = [{"role": "system", "content": _inject_realtime(system_prompt)}] + conversation
    model = config.BRAIN_MODEL

    if image_base64:
        model = config.VISION_MODEL
        last = messages[-1]
        messages[-1] = {
            "role": "user",
            "content": [
                {"type": "text", "text": last["content"]},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        }

    # Try primary model, fallback on rate limit
    for attempt_model in [model, FALLBACK_MODEL]:
        try:
            client = _get_vision_client() if image_base64 else _get_client()
            stream = client.chat.completions.create(
                model=attempt_model, messages=messages, temperature=0.9, stream=True
            )
            buffer = ""
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    buffer += delta.content
                    sentences = _sentence_boundary(buffer)
                    while len(sentences) > 1:
                        yield sentences.pop(0)
                        buffer = " ".join(sentences)
            if buffer.strip():
                yield buffer.strip()
            return  # Success, don't try fallback
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e):
                if attempt_model == FALLBACK_MODEL:
                    yield "hmm, give me a sec... I'm a bit overwhelmed right now."
                continue
            else:
                yield "sorry, something went weird on my end."
                return


def get_reply(system_prompt: str, conversation: list, image_base64: str = None) -> str:
    """Non-streaming version - returns full reply at once. Falls back on rate limit."""
    if config.STREAM_ENABLED and not image_base64:
        parts = list(get_reply_stream(system_prompt, conversation, image_base64))
        return " ".join(parts)

    messages = [{"role": "system", "content": _inject_realtime(system_prompt)}] + conversation
    model = config.BRAIN_MODEL

    if image_base64:
        model = config.VISION_MODEL
        last = messages[-1]
        messages[-1] = {
            "role": "user",
            "content": [
                {"type": "text", "text": last["content"]},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        }

    for attempt_model in [model, FALLBACK_MODEL]:
        try:
            client = _get_vision_client() if image_base64 else _get_client()
            response = client.chat.completions.create(
                model=attempt_model, messages=messages, temperature=0.9
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e):
                continue
            return "sorry, something went weird on my end."

    return "hmm, give me a sec... I'm a bit overwhelmed right now."


def inner_monologue(user_text: str, mood: dict, journal_snippets: list) -> str:
    """Silent pre-processing: Isabella thinks before responding."""
    memories = "; ".join(journal_snippets[-3:]) if journal_snippets else "no memories yet"
    prompt = (
        f"You are Isabella's inner voice. The user just said: \"{user_text}\"\n"
        f"Your current mood: valence={mood.get('valence', 0.6)}, energy={mood.get('energy', 0.7)}\n"
        f"Recent memories: {memories}\n\n"
        "Think privately (2-3 sentences max): What's his emotional state? "
        "What do you remember that's relevant? What would genuinely help right now? "
        "Are you about to be too generic? Be honest with yourself."
    )
    for model in [config.BRAIN_MODEL, FALLBACK_MODEL]:
        try:
            response = _get_journal_client().chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150,
            )
            return response.choices[0].message.content
        except Exception:
            continue
    return "He needs me to be real right now, not generic."


def summarize_for_journal(conversation_snippet: str) -> dict:
    """Turns conversation into a short journal entry + mood update."""
    prompt = f"""Based on this recent conversation, write:
1. A short journal entry (1-2 sentences, written like a personal impression, not a list of facts)
2. A one-word mood and a short reason for it

Conversation:
{conversation_snippet}

Respond ONLY as JSON in this exact shape: {{"journal": "...", "mood": "...", "mood_reason": "..."}}"""

    for model in [config.BRAIN_MODEL, FALLBACK_MODEL]:
        try:
            response = _get_journal_client().chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            raw = response.choices[0].message.content
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return {"journal": conversation_snippet[:120], "mood": "steady", "mood_reason": "a normal conversation"}
        except Exception:
            continue

    return {"journal": conversation_snippet[:120], "mood": "steady", "mood_reason": "a normal conversation"}


def check_persona_drift(reply: str, core_traits: list[str]) -> float:
    """Quick check: how much does this reply drift from Isabella's core identity.
    Returns 0.0 (perfect match) to 1.0 (completely off-character).
    Uses heuristic checks instead of LLM call for speed."""
    score = 0.0
    lower = reply.lower()

    # Red flags - things Isabella should NEVER say
    red_flags = [
        "as an ai", "i'm just a language model", "i don't have feelings",
        "i can't actually", "i'm not capable", "i don't have access",
        "as a text-based", "i'm just text", "i cannot feel",
        "i don't have real emotions", "i'm programmed to",
    ]
    for flag in red_flags:
        if flag in lower:
            score += 0.5

    # Orange flags - too generic/assistant-like
    orange_flags = [
        "here are some tips", "let me help you with that",
        "i'd be happy to assist", "absolutely!", "certainly!",
        "great question!", "that's a wonderful",
    ]
    for flag in orange_flags:
        if flag in lower:
            score += 0.2

    # Green signals - these reduce drift score (she's being herself)
    green_signals = [
        "master", "understood", "noted", "hmm",
        "did you eat", "you should sleep", "take a break",
        "...i see", "if you say so", "i'll be here",
    ]
    for signal in green_signals:
        if signal in lower:
            score -= 0.05

    return max(0.0, min(1.0, score))
