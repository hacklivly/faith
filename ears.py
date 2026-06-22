"""
Faith - the ears.

Records your mic using voice-activity detection (webrtcvad - rule based,
no GPU needed) and sends the clip to Groq's free hosted Whisper for
transcription. Also runs a background listener that interrupts her speech
the moment you start talking.
"""
import collections
import io
import wave

import pyaudio
import webrtcvad
from openai import OpenAI

import config
import mouth

client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)

RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = int(RATE * FRAME_MS / 1000)


def _open_stream():
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                     frames_per_buffer=FRAME_SAMPLES)
    return pa, stream


def record_until_silence(max_silence_frames: int = 25) -> bytes:
    """Starts recording on first detected speech, stops after silence."""
    import gui
    vad = webrtcvad.Vad(config.VAD_AGGRESSIVENESS)
    pa, stream = _open_stream()
    ring = collections.deque(maxlen=10)
    voiced_frames = []
    triggered = False
    silence_count = 0

    try:
        while True:
            if not gui.get_mic_status():
                break
            frame = stream.read(FRAME_SAMPLES, exception_on_overflow=False)
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
                if silence_count > max_silence_frames:
                    break
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

    if not voiced_frames:
        return b""

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(b"".join(voiced_frames))
    return buf.getvalue()


def transcribe(wav_bytes: bytes) -> str:
    if not wav_bytes or len(wav_bytes) < 100:
        return ""
    for attempt in range(3):
        try:
            buf = io.BytesIO(wav_bytes)
            buf.name = "speech.wav"
            result = client.audio.transcriptions.create(model=config.STT_MODEL, file=buf)
            return result.text.strip()
        except Exception as e:
            if attempt < 2:
                import time
                time.sleep(1)
            else:
                print(f"[Faith] Transcription failed: {e}")
                return ""


def listen_for_interrupt():
    """Run in a background thread while Faith is speaking. Detects your voice
    and tells mouth.py to stop mid-sentence."""
    vad = webrtcvad.Vad(3)  # Max aggressiveness to ignore speaker bleed
    pa, stream = _open_stream()
    speech_streak = 0
    try:
        while mouth.is_speaking():
            frame = stream.read(FRAME_SAMPLES, exception_on_overflow=False)
            if vad.is_speech(frame, RATE):
                speech_streak += 1
                if speech_streak > 25:  # ~750ms of sustained speech to interrupt
                    mouth.interrupt()
                    break
            else:
                speech_streak = max(0, speech_streak - 2)
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
