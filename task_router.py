"""
Faith - task router.

Detects actionable commands from conversation and executes them via hands.py.
Uses the LLM to parse intent, then maps to deterministic functions.
"""
import json

import brain
import hands

AVAILABLE_ACTIONS = {
    "open_app": hands.open_app,
    "close_app": hands.close_app,
    "open_website": hands.open_website,
    "web_search": hands.web_search,
    "create_file": hands.create_text_file,
    "set_volume": hands.set_volume,
    "system_info": hands.get_system_info,
    "clipboard_read": hands.get_clipboard,
    "clipboard_write": hands.set_clipboard,
    "list_apps": hands.list_running_apps,
    "shutdown": hands.shutdown_pc,
    "cancel_shutdown": hands.cancel_shutdown,
}

ROUTING_PROMPT = '''Analyze this message and determine if it contains an actionable computer command.
If YES, respond ONLY with JSON like: {"action": "<action_name>", "args": {"param": "value"}}
If NO action is needed, respond ONLY with: {"action": null}

Available actions and their parameters:
- open_app: args = {"path_or_name": "app name or path"}
- close_app: args = {"process_name": "process to kill"}
- open_website: args = {"url": "website url"}
- web_search: args = {"query": "search terms"}
- create_file: args = {"path": "file path", "content": "text content"}
- set_volume: args = {"level": 50}
- system_info: args = {}
- clipboard_read: args = {}
- clipboard_write: args = {"text": "content"}
- list_apps: args = {}
- shutdown: args = {"delay_seconds": 60}
- cancel_shutdown: args = {}

User message: "'''


def route(user_text: str) -> str | None:
    """Check if the user's message contains a task to execute.
    Returns a result string if an action was taken, None otherwise."""
    from openai import OpenAI
    import config

    client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)

    response = client.chat.completions.create(
        model=config.BRAIN_MODEL,
        messages=[{"role": "user", "content": ROUTING_PROMPT + user_text + '"'}],
        temperature=0.1,
        max_tokens=150,
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Try to extract JSON from the response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                parsed = json.loads(raw[start:end])
            except (json.JSONDecodeError, TypeError):
                return None
        else:
            return None

    action_name = parsed.get("action")
    if not action_name or action_name not in AVAILABLE_ACTIONS:
        return None

    args = parsed.get("args", {})
    func = AVAILABLE_ACTIONS[action_name]

    try:
        result = func(**args)
        return result
    except Exception as e:
        return f"Failed to execute {action_name}: {e}"
