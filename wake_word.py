"""Isabella - Wake Word. 'Isabella' keyword activates, otherwise passive."""
import collections
import io
import wave

import pyaudio
import webrtcvad

import config

RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = int(RATE * FRAME_MS / 1000)

_client = None

def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=config.KEY_STT, base_url=config.GROQ_BASE_URL)
    return _client

def is_wake_word(text: str) -> bool:
    """Check if text contains the wake word."""
    lower = text.lower()
    return "isabella" in lower or "fath" in lower or "fase" in lower  # common misheard variants

def listen_for_wake_word(timeout: float = 5.0) -> bool:
    """Listen for short speech, transcribe, check for 'Isabella'. Returns True if heard."""
    vad = webrtcvad.Vad(2)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                     frames_per_buffer=FRAME_SAMPLES)

    ring = collections.deque(maxlen=8)
    voiced_frames = []
    triggered = False
    silence_count = 0
    max_frames = int(timeout * 1000 / FRAME_MS)
    frame_count = 0

    try:
        while frame_count < max_frames:
            frame = stream.read(FRAME_SAMPLES, exception_on_overflow=False)
            frame_count += 1
            is_speech = vad.is_speech(frame, RATE)

            if not triggered:
                ring.append(frame)
                if is_speech:
                    triggered = True
                    voiced_frames.extend(ring)
                    ring.clear()
            else:
                voiced_frames.append(frame)
                silence_count = 0 if is_speech else silence_count + 1
                if silence_count > 15:  # ~450ms silence = end of wake word
                    break
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

    if not voiced_frames or len(voiced_frames) < 5:
        return False

    # Transcribe the short clip
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(b"".join(voiced_frames))

    wav_bytes = buf.getvalue()
    try:
        audio_buf = io.BytesIO(wav_bytes)
        audio_buf.name = "wake.wav"
        result = _get_client().audio.transcriptions.create(model=config.STT_MODEL, file=audio_buf)
        text = result.text.strip()
        return is_wake_word(text)
    except Exception:
        return False
