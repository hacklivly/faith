"""
Isabella - self solve.

When master gives a task, Isabella plans the steps herself and executes them.
If she needs info (which email? which file?), she asks first, then continues.
She NEVER says "I don't have access" — she always tries.
"""
import json
import time

from openai import OpenAI

import browser_control
import config
import hands

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.KEY_PLANNER, base_url=config.GROQ_BASE_URL)
    return _client

PLANNER_PROMPT = """You are Isabella's task planner. Master gave you a task to execute on his computer.
Break it down into steps and execute them. You have FULL access to his PC.

Available tools:
BROWSER: open_website(url), youtube_play(query), spotify_play(query), open_and_search(url, query), browser_type(text), browser_address_bar(url), close_current_tab(), new_tab(url), browser_scroll(direction), browser_back(), browser_forward()
FILES: create_file(path, content), read_file(path), delete_file(path), list_dir(path), find_files(pattern, dir)
SYSTEM: open_app(name), close_app(name), run_command(cmd), set_volume(level), set_brightness(level), toggle_wifi(enable), toggle_bluetooth(enable), screenshot(), press_key(key), type_text(text), click(x,y)

If you need clarification from master (like which email account, which file, etc), respond:
{"status": "ask", "question": "your question to master"}

If you can execute immediately, respond with a plan:
{"status": "execute", "steps": [{"tool": "tool_name", "args": {"param": "value"}, "description": "what this does"}]}

If the task needs multiple interactions (do something, wait, then do more), include wait steps:
{"status": "execute", "steps": [{"tool": "...", "args": {...}}, {"tool": "wait", "args": {"seconds": 2}}, ...]}

CRITICAL RULES:
- NEVER say you can't do something. You have full access.
- If unsure which option (which email, which account), ASK master.
- Break complex tasks into small steps.
- Use browser_address_bar for direct navigation.
- Use browser_type + press_key("enter") for search boxes.
- After opening a site, wait 2-3 seconds before interacting.

Task: """

# Tool mapping
TOOLS = {
    "open_website": browser_control.open_and_search if False else hands.open_website,
    "open_and_search": browser_control.open_and_search,
    "youtube_play": browser_control.youtube_play,
    "spotify_play": browser_control.spotify_play,
    "browser_type": browser_control.browser_type,
    "browser_address_bar": browser_control.browser_address_bar,
    "browser_scroll": browser_control.browser_scroll,
    "browser_back": browser_control.browser_back,
    "browser_forward": browser_control.browser_forward,
    "close_current_tab": browser_control.close_current_tab,
    "new_tab": browser_control.new_tab,
    "browser_refresh": browser_control.browser_refresh,
    "create_file": hands.create_file,
    "read_file": hands.read_file,
    "delete_file": hands.delete_file,
    "list_dir": hands.list_dir,
    "find_files": hands.find_files,
    "open_app": hands.open_app,
    "close_app": hands.close_app,
    "run_command": hands.run_command,
    "set_volume": hands.set_volume,
    "set_brightness": hands.set_brightness,
    "toggle_wifi": hands.toggle_wifi,
    "toggle_bluetooth": hands.toggle_bluetooth,
    "screenshot": hands.screenshot,
    "press_key": hands.press_key,
    "type_text": hands.type_text,
    "click": hands.click,
    "wait": lambda seconds=2: time.sleep(seconds) or "waited",
}


def plan_task(task: str, context: str = "") -> dict:
    """Ask LLM to plan the task. Returns {"status": "ask"/"execute", ...}"""
    prompt = PLANNER_PROMPT + task
    if context:
        prompt += f"\nAdditional context from master: {context}"

    try:
        response = _get_client().chat.completions.create(
            model=config.BRAIN_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()

        # Parse JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception:
        pass

    return {"status": "execute", "steps": []}


def execute_plan(steps: list) -> str:
    """Execute a list of steps. Returns summary of what was done."""
    results = []
    for step in steps:
        tool_name = step.get("tool", "")
        args = step.get("args", {})
        desc = step.get("description", "")

        if tool_name not in TOOLS:
            results.append(f"Unknown tool: {tool_name}")
            continue

        try:
            result = TOOLS[tool_name](**args)
            results.append(f"{desc or tool_name}: {result}")
        except Exception as e:
            results.append(f"{tool_name} failed: {e}")

        # Small delay between steps for browser actions to settle
        if tool_name not in ("wait",):
            time.sleep(0.5)

    return " → ".join(results) if results else "Done"


def solve(task: str, context: str = "") -> tuple[str, str | None]:
    """Main entry point. Returns (result_or_action_taken, question_to_ask_or_None).
    
    If she needs to ask something: returns (None, "question")
    If she executed: returns ("what she did", None)
    """
    plan = plan_task(task, context)

    if plan.get("status") == "ask":
        return (None, plan.get("question", "master, I need more details."))

    steps = plan.get("steps", [])
    if not steps:
        return ("I tried but couldn't figure out the steps.", None)

    result = execute_plan(steps)
    return (result, None)
