"""
Isabella - configuration.

API key loaded from: environment variable OR .env file in project root.
Get a free key (no credit card) at https://console.groq.com
"""
import os

# Load key(s) from .env file if not in environment
def _load_keys():
    keys = {}
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    name, val = line.split("=", 1)
                    name = name.strip()
                    val = val.strip().strip('"').strip("'")
                    if val and val != "your-key-here":
                        keys[name] = val
    # Also check env var
    env_key = os.environ.get("GROQ_API_KEY", "")
    if env_key and env_key != "your-key-here":
        keys.setdefault("GROQ_API_KEY", env_key)
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        keys.setdefault("OPENAI_API_KEY", openai_key)
    return keys

_KEYS = _load_keys()
_ALL_KEYS = [v for k, v in _KEYS.items() if k.startswith("GROQ_")]

# Dedicated key assignments — each module gets its own key = zero rate limits
GROQ_API_KEY = _ALL_KEYS[0] if _ALL_KEYS else ""  # fallback/default
KEY_BRAIN = _ALL_KEYS[0] if len(_ALL_KEYS) > 0 else GROQ_API_KEY      # main conversation
KEY_STT = _ALL_KEYS[1] if len(_ALL_KEYS) > 1 else GROQ_API_KEY        # whisper transcription
KEY_VISION = _ALL_KEYS[2] if len(_ALL_KEYS) > 2 else GROQ_API_KEY     # webcam + screen vision
KEY_PLANNER = _ALL_KEYS[3] if len(_ALL_KEYS) > 3 else GROQ_API_KEY    # self_solve + task_router
KEY_SCREEN_AGENT = _ALL_KEYS[4] if len(_ALL_KEYS) > 4 else GROQ_API_KEY  # screen agent clicks
KEY_RESEARCH = _ALL_KEYS[5] if len(_ALL_KEYS) > 5 else GROQ_API_KEY   # multi_agent research
KEY_JOURNAL = _ALL_KEYS[6] if len(_ALL_KEYS) > 6 else GROQ_API_KEY    # journaling + summarization
KEY_GUARD = _ALL_KEYS[7] if len(_ALL_KEYS) > 7 else GROQ_API_KEY      # persona guard + inner monologue

GROQ_API_KEYS = _ALL_KEYS  # All available keys for multi-agent parallel
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# OpenAI API key (unused, kept for compatibility)
OPENAI_API_KEY = _KEYS.get("OPENAI_API_KEY", "")

# Models - all available on Groq's free tier
BRAIN_MODEL = "llama-3.1-8b-instant"                          # hyper-fast, low latency model
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"    # text + image, same provider
STT_MODEL = "whisper-large-v3-turbo"                          # speech to text

# Streaming settings
STREAM_ENABLED = True          # Stream brain responses for faster first-word
STREAM_SENTENCE_TTS = True     # Start TTS per sentence instead of waiting for full reply

# Her voice (edge-tts, free, no key needed).
VOICE_NAME = "en-US-EmmaMultilingualNeural"
VOICE_RATE = "-5%"
VOICE_PITCH = "+18Hz"

# Where her memory lives
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
JOURNAL_PATH = os.path.join(DATA_DIR, "journal.json")
MOOD_PATH = os.path.join(DATA_DIR, "mood.json")

# XTTS v2 (disabled — Python 3.13 incompatible with required transformers version)
XTTS_ENABLED = False

# Fish.Audio TTS (disabled — no API credits currently)
FISH_ENABLED = False
FISH_REFERENCE_ID = _KEYS.get("FISH_REFERENCE_ID", os.environ.get("FISH_REFERENCE_ID", ""))
_FISH_KEYS = [v for k, v in sorted(_KEYS.items()) if k.startswith("FISH_API_KEY")]
if not _FISH_KEYS:
    _env_fish = os.environ.get("FISH_API_KEY", "")
    if _env_fish:
        _FISH_KEYS = [_env_fish]
FISH_API_KEYS = _FISH_KEYS

# ElevenLabs TTS (secondary — ~10k chars/month per account, multi-key rotation)
ELEVENLABS_ENABLED = True
ELEVENLABS_VOICE_ID = _KEYS.get("ELEVENLABS_VOICE_ID", os.environ.get("ELEVENLABS_VOICE_ID", ""))
ELEVENLABS_MODEL = "eleven_multilingual_v2"  # best quality on free tier

# Load all ElevenLabs API keys (ELEVENLABS_API_KEY, ELEVENLABS_API_KEY_2, etc.)
_ELEVENLABS_KEYS = [v for k, v in sorted(_KEYS.items()) if k.startswith("ELEVENLABS_API_KEY")]
if not _ELEVENLABS_KEYS:
    _env_el = os.environ.get("ELEVENLABS_API_KEY", "")
    if _env_el:
        _ELEVENLABS_KEYS = [_env_el]
ELEVENLABS_API_KEYS = _ELEVENLABS_KEYS  # All keys for rotation
ELEVENLABS_API_KEY = _ELEVENLABS_KEYS[0] if _ELEVENLABS_KEYS else ""  # Backwards compat
XTTS_TIMEOUT = 30  # seconds — if XTTS takes longer, use Edge-TTS
XTTS_VOICE_SAMPLES = [
    os.path.join(DATA_DIR, "voice_sample", "isa1.mp3"),
    os.path.join(DATA_DIR, "voice_sample", "iss3.mp3"),
    os.path.join(DATA_DIR, "voice_sample", "isabella 34.mp3"),
    os.path.join(DATA_DIR, "voice_sample", "is.mp3"),
]
XTTS_SPEED = 0.93
XTTS_LANGUAGE = "en"

# Voice activity detection aggressiveness, 0-3.
VAD_AGGRESSIVENESS = 2

# Personality protection (Oura-inspired)
PERSONA_DRIFT_THRESHOLD = 0.4   # How far reply can deviate from core identity before correction
SESSION_TURNS_BEFORE_JOURNAL = 4  # Journal more frequently (was 6)
TOPIC_RESURFACE_HOURS = 12       # Bring topics back sooner (was 24)
