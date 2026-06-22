"""
Faith - configuration.

Set GROQ_API_KEY as an environment variable before running anything.
Get a free key (no credit card) at https://console.groq.com
"""
import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Models - all available on Groq's free tier
BRAIN_MODEL = "llama-3.1-8b-instant"                          # hyper-fast, low latency model
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"    # text + image, same provider
STT_MODEL = "whisper-large-v3-turbo"                          # speech to text

# Streaming settings
STREAM_ENABLED = True          # Stream brain responses for faster first-word
STREAM_SENTENCE_TTS = True     # Start TTS per sentence instead of waiting for full reply

# Her voice (edge-tts, free, no key needed).
VOICE_NAME = "en-US-AvaMultilingualNeural"  # Original natural female voice

# Where her memory lives
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
JOURNAL_PATH = os.path.join(DATA_DIR, "journal.json")
MOOD_PATH = os.path.join(DATA_DIR, "mood.json")

# Voice activity detection aggressiveness, 0-3.
VAD_AGGRESSIVENESS = 2

# Personality protection (Oura-inspired)
PERSONA_DRIFT_THRESHOLD = 0.4   # How far reply can deviate from core identity before correction
SESSION_TURNS_BEFORE_JOURNAL = 4  # Journal more frequently (was 6)
TOPIC_RESURFACE_HOURS = 12       # Bring topics back sooner (was 24)
