"""Isabella - Screen Agent. See screen, decide where to click, verify results."""
import base64
import io
import json
import time

import pyautogui
from PIL import Image

_client = None
_screen_w = None
_screen_h = None

def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        import config
        _client = OpenAI(api_key=config.KEY_SCREEN_AGENT, base_url=config.GROQ_BASE_URL)
    return _client

def _get_screen_size():
    global _screen_w, _screen_h
    if _screen_w is None:
        _screen_w, _screen_h = pyautogui.size()
    return _screen_w, _screen_h

def _screenshot_b64() -> str:
    img = pyautogui.screenshot()
    # Resize to half for API (save bandwidth) but remember scale factor
    img_small = img.resize((img.width // 2, img.height // 2))
    buf = io.BytesIO()
    img_small.save(buf, format="JPEG", quality=55)
    return base64.b64encode(buf.getvalue()).decode()

def _ask_vision(task: str, screenshot_b64: str) -> dict:
    import config
    sw, sh = _get_screen_size()
    img_w, img_h = sw // 2, sh // 2

    prompt = f"""Task: "{task}"
Image size: {img_w}x{img_h}. Respond ONLY as JSON.
Click: {{"action":"click","x":<num>,"y":<num>,"desc":"what"}}
Type: {{"action":"type","text":"what"}}
Key: {{"action":"key","key":"enter"}}
Scroll: {{"action":"scroll","direction":"down"}}
Done: {{"action":"done","result":"what happened"}}"""

    try:
        resp = _get_client().chat.completions.create(
            model=config.VISION_MODEL,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{screenshot_b64}"}},
            ]}],
            temperature=0.1, max_tokens=100,
        )
        raw = resp.choices[0].message.content.strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception as e:
        print(f"[screen_agent] Vision error: {e}")
    return {"action": "done", "result": "vision call failed"}

def execute_visual_task(task: str, max_steps: int = 6) -> str:
    """See screen, act, verify. Returns summary of what was done."""
    results = []
    print(f"[screen_agent] Starting task: {task}")

    for step in range(max_steps):
        shot = _screenshot_b64()
        action = _ask_vision(task, shot)
        act = action.get("action", "done")
        print(f"[screen_agent] Step {step+1}: {act} - {action.get('desc', action.get('text', action.get('key', '')))}")

        if act == "done":
            final = action.get("result", "done")
            results.append(final)
            break
        elif act == "click":
            # Coordinates are in image space (half), multiply by 2 for real screen
            x = int(action.get("x", 0)) * 2
            y = int(action.get("y", 0)) * 2
            # Clamp to screen bounds
            sw, sh = _get_screen_size()
            x = max(0, min(x, sw - 1))
            y = max(0, min(y, sh - 1))
            pyautogui.click(x, y)
            desc = action.get("desc", f"({x},{y})")
            results.append(f"clicked: {desc}")
        elif act == "type":
            text = action.get("text", "")
            if text:
                time.sleep(0.3)
                pyautogui.typewrite(text, interval=0.03)
                results.append(f"typed: {text[:40]}")
        elif act == "key":
            key = action.get("key", "enter")
            pyautogui.press(key)
            results.append(f"pressed: {key}")
        elif act == "scroll":
            direction = action.get("direction", "down")
            pyautogui.scroll(-3 if direction == "down" else 3)
            results.append(f"scrolled {direction}")
        else:
            results.append(f"unknown action: {act}")
            break

        time.sleep(1.5)  # Wait for screen to update

    summary = ", ".join(results) if results else "completed"
    print(f"[screen_agent] Done: {summary}".encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
    return summary
