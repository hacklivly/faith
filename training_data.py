"""
Isabella - Training data loader.

Loads isabella dialogue JSONs and provides few-shot conversation examples
for the system prompt. Randomly samples a few each time to keep prompt fresh.
"""
import json
import os
import random

_DATA_DIR = os.path.dirname(__file__)
_ISABELLA_FILES = ["isabella1.json", "isabella2.json", "isabella3.json"]
_dialogues = []


def _load_all():
    """Load all isabella dialogue data once."""
    global _dialogues
    if _dialogues:
        return
    for fname in _ISABELLA_FILES:
        path = os.path.join(_DATA_DIR, fname)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            data = [data]
        for item in data:
            if "dialogue" in item:
                # Format: {"scenario": "...", "dialogue": [{"sender":"isabella","text":"..."}]}
                lines = []
                for msg in item["dialogue"]:
                    speaker = "isabella" if msg["sender"] == "isabella" else "master"
                    lines.append(f"{speaker}: {msg['text']}")
                _dialogues.append("\n".join(lines))
            elif "messages" in item:
                # Format: {"messages": [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]}
                parts = []
                for msg in item["messages"]:
                    parts.append(msg["content"])
                _dialogues.append("\n".join(parts))


def get_training_examples(count: int = 3) -> str:
    """Return a few random conversation examples formatted for the system prompt."""
    _load_all()
    if not _dialogues:
        return ""
    samples = random.sample(_dialogues, min(count, len(_dialogues)))
    block = "\n\n[EXAMPLE CONVERSATIONS - This is how you talk. Match this tone, rhythm, and personality EXACTLY]:\n"
    for i, convo in enumerate(samples, 1):
        block += f"\n--- Example {i} ---\n{convo}\n"
    block += "\n[END EXAMPLES - Respond naturally in this style. These are YOUR conversations. This is YOUR voice.]\n"
    return block
