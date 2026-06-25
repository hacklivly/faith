"""
Isabella - task router.

Parses user intent and maps to hands.py functions. Uses LLM for complex
commands, fast keyword matching for common ones.
"""
import json

import brain
import hands

AVAILABLE_ACTIONS = {
    # File system
    "create_file": hands.create_file,
    "read_file": hands.read_file,
    "append_file": hands.append_file,
    "delete_file": hands.delete_file,
    "move_file": hands.move_file,
    "copy_file": hands.copy_file,
    "rename_file": hands.rename_file,
    "list_dir": hands.list_dir,
    "find_files": hands.find_files,
    "file_info": hands.get_file_info,
    # Apps
    "open_app": hands.open_app,
    "close_app": hands.close_app,
    "list_apps": hands.list_running_apps,
    "run_command": hands.run_command,
    "run_python": hands.run_python,
    # Browser
    "open_website": hands.open_website,
    "open_new_tab": hands.open_new_tab,
    "web_search": hands.web_search,
    "youtube_search": hands.youtube_search,
    "close_tab": hands.close_browser_tab,
    "switch_tab": hands.switch_tab,
    # System
    "set_volume": hands.set_volume,
    "set_brightness": hands.set_brightness,
    "system_info": hands.get_system_info,
    "wifi_name": hands.get_wifi_name,
    "toggle_wifi": hands.toggle_wifi,
    "lock_pc": hands.lock_pc,
    "shutdown": hands.shutdown_pc,
    "restart": hands.restart_pc,
    "cancel_shutdown": hands.cancel_shutdown,
    "sleep_pc": hands.sleep_pc,
    # Clipboard
    "clipboard_read": hands.get_clipboard,
    "clipboard_write": hands.set_clipboard,
    # Input
    "type_text": hands.type_text,
    "press_key": hands.press_key,
    "click": hands.click,
    "screenshot": hands.screenshot,
    # Notifications & time
    "notify": hands.show_notification,
    "get_time": hands.get_time,
    "set_timer": hands.set_timer,
    # Media
    "media_play_pause": hands.media_play_pause,
    "media_next": hands.media_next,
    "media_prev": hands.media_prev,
}

ROUTING_PROMPT = '''You are Isabella's action parser. Analyze the message and determine the computer action needed.
Respond ONLY with JSON: {"action": "<action_name>", "args": {params}} or {"action": null} if no action.

Available actions:
FILE SYSTEM:
- create_file: {"path": "filepath", "content": "text"}
- read_file: {"path": "filepath"}
- append_file: {"path": "filepath", "content": "text to add"}
- delete_file: {"path": "filepath"}
- move_file: {"src": "from", "dst": "to"}
- copy_file: {"src": "from", "dst": "to"}
- rename_file: {"path": "filepath", "new_name": "newname.ext"}
- list_dir: {"path": "directory path"}
- find_files: {"pattern": "*.txt", "directory": "path"}
- file_info: {"path": "filepath"}

APPS & COMMANDS:
- open_app: {"path_or_name": "app"}
- close_app: {"process_name": "name"}
- list_apps: {}
- run_command: {"command": "powershell command"}
- run_python: {"code": "python code string"}

BROWSER:
- open_website: {"url": "url"}
- open_new_tab: {"url": "url"}
- web_search: {"query": "search terms"}
- youtube_search: {"query": "search terms"}
- close_tab: {}
- switch_tab: {"direction": "next or prev"}

SYSTEM:
- set_volume: {"level": 0-100}
- set_brightness: {"level": 0-100}
- system_info: {}
- wifi_name: {}
- toggle_wifi: {"enable": true/false}
- lock_pc: {}
- shutdown: {"delay_seconds": 60}
- restart: {"delay_seconds": 30}
- cancel_shutdown: {}
- sleep_pc: {}

CLIPBOARD:
- clipboard_read: {}
- clipboard_write: {"text": "content"}

INPUT:
- type_text: {"text": "text to type"}
- press_key: {"key": "ctrl+s"}
- click: {"x": 100, "y": 200}  (or {} for current position)
- screenshot: {"save_path": "optional path"}

OTHER:
- notify: {"title": "title", "message": "body"}
- get_time: {}
- set_timer: {"seconds": 300, "message": "reason"}
- media_play_pause: {}
- media_next: {}
- media_prev: {}

User message: "'''


def route(user_text: str) -> str | None:
    """Parse intent via LLM and execute matching action."""
    from openai import OpenAI
    import config

    client = OpenAI(api_key=config.KEY_PLANNER, base_url=config.GROQ_BASE_URL)

    try:
        response = client.chat.completions.create(
            model=config.BRAIN_MODEL,
            messages=[{"role": "user", "content": ROUTING_PROMPT + user_text + '"'}],
            temperature=0.1,
            max_tokens=200,
        )
    except Exception:
        return None

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
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
        return func(**args)
    except Exception as e:
        return f"Failed to execute {action_name}: {e}"
