"""
Isabella - external integrations.

Weather, battery monitoring, and environmental awareness hooks that
give her real-world grounding instead of being trapped in a text void.
"""
import json
import subprocess
from datetime import datetime
from urllib.request import urlopen


_cached_weather = None
_weather_cache_time = 0.0

def get_weather(city: str = "auto") -> str | None:
    """Get current weather from wttr.in (free, no API key needed)."""
    global _cached_weather, _weather_cache_time
    import time
    now = time.time()
    if _cached_weather and (now - _weather_cache_time < 1800):
        return _cached_weather

    try:
        url = f"https://wttr.in/{city}?format=j1" if city != "auto" else "https://wttr.in/?format=j1"
        response = urlopen(url, timeout=5)
        data = json.loads(response.read())
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp_c = current["temp_C"]
        feels = current["FeelsLikeC"]
        _cached_weather = f"{desc}, {temp_c}°C (feels like {feels}°C)"
        _weather_cache_time = now
        return _cached_weather
    except Exception:
        return _cached_weather


_cached_battery = None
_battery_cache_time = 0.0

def get_battery_level() -> int | None:
    """Get battery percentage on Windows."""
    global _cached_battery, _battery_cache_time
    import time
    now = time.time()
    if _cached_battery is not None and (now - _battery_cache_time < 300):
        return _cached_battery

    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "(Get-WmiObject Win32_Battery).EstimatedChargeRemaining"],
            capture_output=True, text=True, timeout=3
        )
        val = result.stdout.strip()
        if val.isdigit():
            _cached_battery = int(val)
            _battery_cache_time = now
            return _cached_battery
    except Exception:
        pass
    return _cached_battery


def get_system_events() -> list[str]:
    """Check for notable system conditions Isabella should know about."""
    events = []
    hour = datetime.now().hour

    # Late night warning
    if 0 <= hour < 5:
        events.append("It's past midnight — he should probably sleep.")

    # Battery check
    battery = get_battery_level()
    if battery is not None and battery < 15:
        events.append(f"Battery is critically low at {battery}%.")
    elif battery is not None and battery < 30:
        events.append(f"Battery is at {battery}% — might want to plug in.")

    return events


def get_context_for_prompt() -> str:
    """Gather all external context into a prompt block."""
    parts = []

    # Weather (cache-friendly: only fetch occasionally, handled by caller)
    weather = get_weather()
    if weather:
        parts.append(f"Current weather: {weather}")

    # System events
    events = get_system_events()
    if events:
        parts.extend(events)

    if not parts:
        return ""

    return (
        "\n[Real-world context you can reference naturally if relevant — "
        "don't force it, just weave in if it fits]:\n"
        + "\n".join(f"- {p}" for p in parts) + "\n"
    )
