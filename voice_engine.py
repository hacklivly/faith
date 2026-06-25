"""
Isabella - Voice Engine (Triple Fallback).

Primary: Fish.Audio (10 API keys, auto-rotation)
Secondary: ElevenLabs (10 API keys, auto-rotation)
Fallback: Edge-TTS (unlimited, free, always works)

When a key hits rate limit → rotate to next key.
When ALL keys for a service are exhausted → fall to next service.
"""
import asyncio
import os
import re
import subprocess
import tempfile
import threading
import time
import wave

import pyaudio
import edge_tts
import requests

import config

# Edge-TTS settings
VOICE = config.VOICE_NAME
RATE = getattr(config, "VOICE_RATE", "-5%")
PITCH = getattr(config, "VOICE_PITCH", "+18Hz")

CHUNK_SIZE = 1024

_lock = threading.Lock()
_ready = False
_playing = False
_stop_flag = threading.Event()
_progress_callback = None
_pa = None


def set_progress_callback(cb):
    global _progress_callback
    _progress_callback = cb


def _report_progress(percent: int, status: str):
    if _progress_callback:
        try:
            _progress_callback(percent, status)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# TEXT CLEANING & HUMAN-LIKE EXPRESSIVENESS
# ═══════════════════════════════════════════════════════════

import random

def clean_text(text: str) -> str:
    """Clean text for TTS: strip formatting, keep human-like sounds."""
    text = text.replace("*", "")
    text = re.sub(r'["""]', '', text)
    text = re.sub(r'[_`#]', '', text)
    text = _convert_paralinguistics(text)
    text = re.sub(r'[♡♥❤️💕🥰😊😂🤣💖✨🌸💗💓💞🫠🤭😏😤🥺😭💀🔥👀]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _convert_paralinguistics(text: str) -> str:
    """Convert stage directions into natural speakable sounds."""
    replacements = {
        r'\(sighs?\s*(?:softly|happily|sadly)?\)': '... mmh...',
        r'\(breathes?\s*(?:softly|deeply)?\)': '...',
        r'\(whispers?\)': '...',
        r'\(giggles?\s*(?:softly|shyly|happily|cutely)?\)': 'hehe,',
        r'\(laughs?\s*(?:softly|happily|cutely)?\)': 'ha ha,',
        r'\(blushes?\)': '... um,',
        r'\(pouts?\s*(?:cutely)?\)': 'hmph,',
        r'\(teasing\s*(?:tone|voice)?\)': '',
        r'\(playful(?:ly)?\)': '',
        r'\(in a \w+ (?:voice|tone)\)': '',
        r'\((?:soft|cute|shy|quiet)\s+\w+\)': '...',
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r'\([^)]*\)', '', text)
    return text


def _inject_breathing(text: str) -> str:
    """Add subtle breathing pauses between sentences for natural rhythm."""
    if len(text) < 40:
        return text

    # Split on sentence boundaries
    parts = re.split(r'(?<=[.!?])\s+', text)
    if len(parts) <= 1:
        return text

    result = [parts[0]]
    for part in parts[1:]:
        # 30% chance of a breath pause between sentences
        if random.random() < 0.30:
            result.append("...")
        result.append(part)
    return " ".join(result)


def _inject_micro_pauses(text: str) -> str:
    """Add commas at natural pause points for human-like pacing."""
    # Add pause after "and" / "but" / "so" mid-sentence (20% chance each)
    if random.random() < 0.25:
        text = re.sub(r'\b(and|but|so|then)\b(?!,)', lambda m: m.group(0) + ',', text, count=1)
    return text


def _has_hindi(text: str) -> bool:
    """Check if text contains Devanagari (Hindi) characters."""
    return bool(re.search(r'[\u0900-\u097F]', text))


def _translate_to_english(text: str) -> str:
    """Translate Hindi/Hinglish text to English using Groq."""
    if not _has_hindi(text):
        return text
    try:
        from groq import Groq
        client = Groq(api_key=config.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a translator. Convert the given Hindi/Hinglish text into English. Reply ONLY with the English translation. Do NOT reply in Hindi. Do NOT add explanations."},
                {"role": "user", "content": f"Translate to English: {text}"}
            ],
            temperature=0.2,
            max_tokens=300,
        )
        translated = resp.choices[0].message.content.strip()
        # Verify it's actually English (no Devanagari in output)
        if translated and not _has_hindi(translated):
            return translated
        return text
    except Exception:
        return text


# ═══════════════════════════════════════════════════════════
# FISH.AUDIO ENGINE (PRIMARY — multi-account rotation)
# ═══════════════════════════════════════════════════════════

_fish_available = False
_fish_keys = []
_fish_key_idx = 0
_fish_exhausted = False


def _init_fish():
    """Check if Fish.Audio is configured."""
    global _fish_available, _fish_keys
    if not getattr(config, "FISH_ENABLED", False):
        return
    keys = getattr(config, "FISH_API_KEYS", [])
    if not keys:
        return
    ref_id = getattr(config, "FISH_REFERENCE_ID", "")
    if not ref_id:
        print("[Voice] Fish.Audio REFERENCE_ID not set. Skipping Fish.")
        return
    _fish_keys = keys
    _fish_available = True
    print(f"[Voice] Fish.Audio ready — {len(keys)} key(s) loaded (voice: {ref_id[:8]}...).")


# Fish.Audio emotion mapping — Isabella's voice_style emotions → [bracket] tags
_FISH_EMOTION_MAP = {
    # Girly / Happy / Laughing
    "giggly":          "[delighted][chuckling]",
    "ecstatic":        "[very excited]",
    "giddy":           "[excited][chuckling]",
    "delighted":       "[delighted]",
    "hyper":           "[very excited]",
    "playful":         "[happy]",
    "amused":          "[happy][chuckling]",

    # Teasing / Mischief
    "teasing":         "[sarcastic]",
    "mischievous":     "[sarcastic]",
    "smug":            "[satisfied]",

    # Flustered / Shy
    "flustered":       "[embarrassed][soft tone]",
    "deeply_flustered":"[embarrassed][whispering]",
    "embarrassed":     "[embarrassed]",
    "slightly_shy":    "[nervous][soft tone]",

    # Love / Affection
    "loving":          "[soft tone]",
    "tender":          "[soft tone]",
    "affectionate":    "[happy][soft tone]",
    "caring":          "[empathetic][soft tone]",
    "devoted":         "[soft tone]",

    # Anger / Frustration
    "angry":           "[angry]",
    "frustrated":      "[frustrated]",
    "cold_fury":       "[angry]",
    "irritated":       "[frustrated]",
    "mildly_annoyed":  "[frustrated]",

    # Sadness
    "melancholic":     "[sad]",
    "hurt":            "[sad][soft tone]",
    "lonely":          "[sad][whispering]",
    "resigned":        "[sad][sighing]",

    # Excitement / Surprise
    "excited":         "[excited]",
    "surprised":       "[surprised]",

    # Worry / Concern
    "worried":         "[worried]",
    "protective":      "[determined]",
    "stern":           "[confident]",

    # Jealousy
    "jealous":         "[jealous]",
    "possessive":      "[jealous]",
    "suspicious":      "[doubtful]",

    # Calm / Neutral
    "neutral":         "[calm]",
    "content":         "[satisfied]",
    "thoughtful":      "[calm]",
    "sleepy":          "[relaxed][soft tone]",
    "bored":           "[bored]",
    "curious":         "[curious]",
}


def _fish_add_emotion(text: str) -> str:
    """Prepend Fish.Audio emotion tags based on detected emotion."""
    try:
        import voice_style
        style = voice_style.compute(text)
        emotion = style.get("emotion", "neutral")
    except Exception:
        emotion = "neutral"

    tag = _FISH_EMOTION_MAP.get(emotion, "[calm]")
    return f"{tag} {text}"


def _speak_fish(text: str) -> bool:
    """Speak with Fish.Audio — emotion-aware, multi-key rotation.
    Returns True if successful."""
    global _fish_exhausted, _fish_key_idx
    if not _fish_available or _fish_exhausted:
        return False

    # Add emotion direction tags
    tagged_text = _fish_add_emotion(text)

    url = "https://api.fish.audio/v1/tts"
    payload = {
        "text": tagged_text,
        "reference_id": config.FISH_REFERENCE_ID,
        "format": "mp3",
    }

    attempts = len(_fish_keys)
    for _ in range(attempts):
        key = _fish_keys[_fish_key_idx]
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15, stream=True)

            if resp.status_code == 200:
                audio_data = b""
                for chunk in resp.iter_content(chunk_size=4096):
                    if _stop_flag.is_set():
                        return True
                    audio_data += chunk
                if audio_data and not _stop_flag.is_set():
                    _play_mp3_bytes(audio_data)
                    return True
                return False

            if resp.status_code in (401, 402, 429, 403):
                old_idx = _fish_key_idx + 1
                _fish_key_idx = (_fish_key_idx + 1) % len(_fish_keys)
                print(f"[Voice] Fish.Audio key #{old_idx} exhausted (HTTP {resp.status_code}). Trying key #{_fish_key_idx + 1}...")
                continue

            # Other error — try next key
            _fish_key_idx = (_fish_key_idx + 1) % len(_fish_keys)
            continue

        except requests.exceptions.Timeout:
            _fish_key_idx = (_fish_key_idx + 1) % len(_fish_keys)
            continue
        except Exception as e:
            print(f"[Voice] Fish.Audio error: {e}")
            _fish_key_idx = (_fish_key_idx + 1) % len(_fish_keys)
            continue

    # All keys exhausted
    _fish_exhausted = True
    print(f"[Voice] All {len(_fish_keys)} Fish.Audio keys exhausted -> falling back to ElevenLabs.")
    return False


# ═══════════════════════════════════════════════════════════
# ELEVENLABS ENGINE (SECONDARY — multi-account rotation)
# Emotion-aware: adjusts stability/style/similarity per detected emotion
# ═══════════════════════════════════════════════════════════

_elevenlabs_available = False
_elevenlabs_keys = []
_elevenlabs_key_idx = 0
_elevenlabs_exhausted = False

# Emotion → ElevenLabs voice_settings mapping
_EL_EMOTION_SETTINGS = {
    "giggly":          {"stability": 0.30, "similarity_boost": 0.80, "style": 0.85, "use_speaker_boost": True},
    "ecstatic":        {"stability": 0.28, "similarity_boost": 0.75, "style": 0.90, "use_speaker_boost": True},
    "giddy":           {"stability": 0.32, "similarity_boost": 0.78, "style": 0.80, "use_speaker_boost": True},
    "delighted":       {"stability": 0.35, "similarity_boost": 0.80, "style": 0.75, "use_speaker_boost": True},
    "hyper":           {"stability": 0.25, "similarity_boost": 0.75, "style": 0.90, "use_speaker_boost": True},
    "playful":         {"stability": 0.38, "similarity_boost": 0.82, "style": 0.70, "use_speaker_boost": True},
    "teasing":         {"stability": 0.40, "similarity_boost": 0.80, "style": 0.65, "use_speaker_boost": True},
    "mischievous":     {"stability": 0.35, "similarity_boost": 0.80, "style": 0.72, "use_speaker_boost": True},
    "smug":            {"stability": 0.45, "similarity_boost": 0.82, "style": 0.60, "use_speaker_boost": True},
    "amused":          {"stability": 0.40, "similarity_boost": 0.82, "style": 0.65, "use_speaker_boost": True},
    "flustered":       {"stability": 0.35, "similarity_boost": 0.85, "style": 0.55, "use_speaker_boost": True},
    "deeply_flustered":{"stability": 0.30, "similarity_boost": 0.85, "style": 0.60, "use_speaker_boost": True},
    "embarrassed":     {"stability": 0.38, "similarity_boost": 0.85, "style": 0.50, "use_speaker_boost": True},
    "slightly_shy":    {"stability": 0.42, "similarity_boost": 0.85, "style": 0.45, "use_speaker_boost": True},
    "loving":          {"stability": 0.55, "similarity_boost": 0.90, "style": 0.60, "use_speaker_boost": True},
    "tender":          {"stability": 0.58, "similarity_boost": 0.90, "style": 0.55, "use_speaker_boost": True},
    "affectionate":    {"stability": 0.52, "similarity_boost": 0.88, "style": 0.58, "use_speaker_boost": True},
    "caring":          {"stability": 0.55, "similarity_boost": 0.88, "style": 0.50, "use_speaker_boost": True},
    "devoted":         {"stability": 0.60, "similarity_boost": 0.90, "style": 0.55, "use_speaker_boost": True},
    "angry":           {"stability": 0.30, "similarity_boost": 0.78, "style": 0.45, "use_speaker_boost": True},
    "frustrated":      {"stability": 0.38, "similarity_boost": 0.80, "style": 0.40, "use_speaker_boost": True},
    "cold_fury":       {"stability": 0.65, "similarity_boost": 0.85, "style": 0.25, "use_speaker_boost": True},
    "irritated":       {"stability": 0.42, "similarity_boost": 0.80, "style": 0.38, "use_speaker_boost": True},
    "mildly_annoyed":  {"stability": 0.48, "similarity_boost": 0.82, "style": 0.35, "use_speaker_boost": True},
    "melancholic":     {"stability": 0.55, "similarity_boost": 0.88, "style": 0.50, "use_speaker_boost": True},
    "hurt":            {"stability": 0.45, "similarity_boost": 0.88, "style": 0.55, "use_speaker_boost": True},
    "lonely":          {"stability": 0.50, "similarity_boost": 0.90, "style": 0.48, "use_speaker_boost": True},
    "resigned":        {"stability": 0.60, "similarity_boost": 0.85, "style": 0.30, "use_speaker_boost": True},
    "excited":         {"stability": 0.30, "similarity_boost": 0.78, "style": 0.80, "use_speaker_boost": True},
    "surprised":       {"stability": 0.32, "similarity_boost": 0.80, "style": 0.75, "use_speaker_boost": True},
    "worried":         {"stability": 0.48, "similarity_boost": 0.85, "style": 0.45, "use_speaker_boost": True},
    "protective":      {"stability": 0.50, "similarity_boost": 0.85, "style": 0.42, "use_speaker_boost": True},
    "jealous":         {"stability": 0.40, "similarity_boost": 0.82, "style": 0.50, "use_speaker_boost": True},
    "possessive":      {"stability": 0.45, "similarity_boost": 0.85, "style": 0.45, "use_speaker_boost": True},
    "suspicious":      {"stability": 0.50, "similarity_boost": 0.83, "style": 0.40, "use_speaker_boost": True},
    "neutral":         {"stability": 0.50, "similarity_boost": 0.80, "style": 0.45, "use_speaker_boost": True},
    "content":         {"stability": 0.55, "similarity_boost": 0.82, "style": 0.42, "use_speaker_boost": True},
    "thoughtful":      {"stability": 0.58, "similarity_boost": 0.85, "style": 0.38, "use_speaker_boost": True},
    "sleepy":          {"stability": 0.62, "similarity_boost": 0.88, "style": 0.35, "use_speaker_boost": True},
}

_EL_DEFAULT_SETTINGS = {"stability": 0.50, "similarity_boost": 0.80, "style": 0.45, "use_speaker_boost": True}


def _init_elevenlabs():
    """Check if ElevenLabs is configured with multi-key support."""
    global _elevenlabs_available, _elevenlabs_keys
    if not getattr(config, "ELEVENLABS_ENABLED", False):
        return
    keys = getattr(config, "ELEVENLABS_API_KEYS", [])
    if not keys:
        k = getattr(config, "ELEVENLABS_API_KEY", "")
        if k:
            keys = [k]
    if not keys or not getattr(config, "ELEVENLABS_VOICE_ID", ""):
        return
    _elevenlabs_keys = keys
    _elevenlabs_available = True
    print(f"[Voice] ElevenLabs ready — {len(keys)} key(s) loaded (voice: {config.ELEVENLABS_VOICE_ID[:8]}...).")


def _get_emotion(text: str) -> str:
    """Detect emotion from text for voice tuning."""
    try:
        import voice_style
        style = voice_style.compute(text)
        return style.get("emotion", "neutral")
    except Exception:
        return "neutral"


def _speak_elevenlabs(text: str) -> bool:
    """Speak with ElevenLabs — emotion-aware, multi-key rotation.
    Returns True if successful."""
    global _elevenlabs_exhausted, _elevenlabs_key_idx
    if not _elevenlabs_available or _elevenlabs_exhausted:
        return False

    emotion = _get_emotion(text)
    voice_settings = _EL_EMOTION_SETTINGS.get(emotion, _EL_DEFAULT_SETTINGS)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
    payload = {
        "text": text,
        "model_id": getattr(config, "ELEVENLABS_MODEL", "eleven_multilingual_v2"),
        "voice_settings": voice_settings,
    }

    attempts = len(_elevenlabs_keys)
    for _ in range(attempts):
        key = _elevenlabs_keys[_elevenlabs_key_idx]
        headers = {
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15, stream=True)

            if resp.status_code == 200:
                audio_data = b""
                for chunk in resp.iter_content(chunk_size=4096):
                    if _stop_flag.is_set():
                        return True
                    audio_data += chunk
                if audio_data and not _stop_flag.is_set():
                    _play_mp3_bytes(audio_data)
                    return True
                return False

            if resp.status_code in (401, 429, 403):
                old_idx = _elevenlabs_key_idx + 1
                _elevenlabs_key_idx = (_elevenlabs_key_idx + 1) % len(_elevenlabs_keys)
                print(f"[Voice] ElevenLabs key #{old_idx} exhausted (HTTP {resp.status_code}). Trying key #{_elevenlabs_key_idx + 1}...")
                continue

            _elevenlabs_key_idx = (_elevenlabs_key_idx + 1) % len(_elevenlabs_keys)
            continue

        except requests.exceptions.Timeout:
            _elevenlabs_key_idx = (_elevenlabs_key_idx + 1) % len(_elevenlabs_keys)
            continue
        except Exception as e:
            print(f"[Voice] ElevenLabs error: {e}")
            _elevenlabs_key_idx = (_elevenlabs_key_idx + 1) % len(_elevenlabs_keys)
            continue

    # All keys exhausted
    _elevenlabs_exhausted = True
    print(f"[Voice] All {len(_elevenlabs_keys)} ElevenLabs keys exhausted -> falling back to Edge-TTS.")
    return False


# ═══════════════════════════════════════════════════════════
# EDGE-TTS ENGINE (FINAL FALLBACK — unlimited, free)
# ═══════════════════════════════════════════════════════════

def _run_async(coro):
    """Run async coroutine from sync code."""
    result = []
    error = []

    def _run():
        try:
            result.append(asyncio.run(coro))
        except Exception as e:
            error.append(e)

    t = threading.Thread(target=_run)
    t.start()
    t.join(timeout=60)

    if error:
        print(f"[Voice] Edge-TTS error: {error[0]}")
    return result[0] if result else None


async def _edge_synthesize_and_play(text: str):
    """Synthesize with Edge-TTS using emotion-aware rate/pitch."""
    try:
        import voice_style
        style = voice_style.compute(text)
        rate, pitch = voice_style.get_edge_params(style)

        communicate = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch)
        audio_data = b""
        async for chunk in communicate.stream():
            if _stop_flag.is_set():
                return
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        if _stop_flag.is_set() or not audio_data:
            return

        _play_mp3_bytes(audio_data)
    except Exception as e:
        print(f"[Voice] Edge-TTS synthesis error: {e}")


def _play_mp3_bytes(data: bytes):
    """Decode mp3 via ffmpeg and play via PyAudio."""
    if _stop_flag.is_set():
        return

    tmp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_wav = tmp_mp3.name.replace(".mp3", ".wav")
    try:
        tmp_mp3.write(data)
        tmp_mp3.close()

        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_mp3.name, "-ar", "24000", "-ac", "1", "-f", "wav", tmp_wav],
            capture_output=True, timeout=10
        )

        if not os.path.exists(tmp_wav):
            return

        with wave.open(tmp_wav, 'rb') as wf:
            stream = _pa.open(
                format=_pa.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            try:
                chunk = wf.readframes(CHUNK_SIZE)
                while chunk and not _stop_flag.is_set():
                    stream.write(chunk)
                    chunk = wf.readframes(CHUNK_SIZE)
            finally:
                stream.stop_stream()
                stream.close()
    finally:
        try:
            os.unlink(tmp_mp3.name)
        except OSError:
            pass
        try:
            os.unlink(tmp_wav)
        except OSError:
            pass


def _speak_edge(text: str):
    """Speak using Edge-TTS (reliable fallback)."""
    _run_async(_edge_synthesize_and_play(text))


# ═══════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════

def preload():
    """Initialize audio and TTS engines."""
    global _ready, _pa
    with _lock:
        if _ready:
            return
        _report_progress(20, "Initializing audio...")
        _pa = pyaudio.PyAudio()
        _ready = True

        _init_fish()
        _init_elevenlabs()

        print(f"[Voice] Edge-TTS ready ({VOICE}, rate={RATE}, pitch={PITCH}).")
        _report_progress(100, "Voice ready.")


def speak(text: str):
    """Clean text, translate Hindi->English, humanize, then speak."""
    global _playing
    if not _ready:
        preload()
    text = clean_text(text)
    if not text:
        return

    # Translate Hindi to English so TTS always speaks English
    text = _translate_to_english(text)

    # Humanize: add breathing and micro-pauses for natural delivery
    text = _inject_breathing(text)
    text = _inject_micro_pauses(text)

    _stop_flag.clear()
    _playing = True
    try:
        # 1. Try Fish.Audio (primary)
        if not _stop_flag.is_set() and _speak_fish(text):
            return

        # 2. Try ElevenLabs (secondary)
        if not _stop_flag.is_set() and _speak_elevenlabs(text):
            return

        # 3. Edge-TTS (always works)
        if not _stop_flag.is_set():
            _speak_edge(text)
    finally:
        _playing = False


def speak_streamed(sentence_generator):
    """Play sentences one by one. Returns full text."""
    full_text = []
    for sentence in sentence_generator:
        if _stop_flag.is_set():
            break
        sentence = sentence.strip()
        if not sentence:
            continue
        full_text.append(sentence)
        speak(sentence)
        # Tiny gap between sentences for natural rhythm
        if not _stop_flag.is_set():
            time.sleep(random.uniform(0.05, 0.15))
    return " ".join(full_text)


def is_playing() -> bool:
    return _playing


def stop():
    """Stop current playback."""
    _stop_flag.set()


def cleanup():
    """Cleanup resources."""
    global _pa, _ready
    if _pa:
        try:
            _pa.terminate()
        except Exception:
            pass
        _pa = None
        _ready = False


# Legacy stubs (kept for compatibility)
def get_cached_audio(text: str):
    return None

def cache_audio(text: str):
    return None

def precache_async(texts: list[str]):
    pass
