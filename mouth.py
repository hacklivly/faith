"""
Faith - the mouth.

Streaming TTS: speaks sentence-by-sentence as they arrive from the brain,
instead of waiting for the full reply. First words out in ~1s instead of 5+.
"""
import asyncio
import os
import queue
import tempfile
import threading

import edge_tts

import config

# --- Pygame init with WASAPI fix ---
os.environ["SDL_AUDIODRIVER"] = "directsound"

import pygame

_mixer_ready = False
try:
    pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=2048)
    _mixer_ready = True
except pygame.error:
    try:
        pygame.mixer.init()
        _mixer_ready = True
    except pygame.error:
        print("[Faith] pygame mixer failed. Using pyttsx3 only.")

_interrupt_flag = threading.Event()
_speaking_flag = threading.Event()
_current_style: dict = {"rate": "+0%", "pitch": "+0Hz"}

VOICE_NAME = "en-US-AvaMultilingualNeural"
FALLBACK_VOICES = ["en-US-AvaNeural", "en-US-JennyNeural", "en-US-AriaNeural"]


def set_style(style: dict):
    global _current_style
    _current_style = style


async def _synthesize(text: str, path: str, style: dict = None) -> bool:
    """Try edge-tts synthesis with retries and voice fallbacks."""
    if style is None:
        style = _current_style
    voices_to_try = [VOICE_NAME] + FALLBACK_VOICES
    for voice in voices_to_try:
        for attempt in range(2):
            try:
                communicate = edge_tts.Communicate(
                    text, voice,
                    rate=style.get("rate", "+0%"),
                    pitch=style.get("pitch", "+0Hz"),
                )
                await communicate.save(path)
                return True
            except Exception:
                if attempt < 1:
                    await asyncio.sleep(0.5)
                continue
    return False


def _speak_pyttsx3(text: str):
    """Fallback TTS using pyttsx3."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        for v in voices:
            if "female" in v.name.lower() or "zira" in v.name.lower():
                engine.setProperty("voice", v.id)
                break
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 0.9)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[Faith] pyttsx3 also failed: {e}")


def _play_audio_file(path: str) -> bool:
    """Play a single audio file, returns False if interrupted."""
    if not _mixer_ready or not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if _interrupt_flag.is_set():
                pygame.mixer.music.stop()
                return False
            pygame.time.wait(50)
        return True
    except Exception:
        return False
    finally:
        try:
            pygame.mixer.music.unload()
        except Exception:
            pass


def speak(text: str):
    """Synthesizes and plays full text at once. Original non-streaming behavior."""
    _interrupt_flag.clear()
    _speaking_flag.set()

    if _mixer_ready:
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            import memory
            import voice_style
            mood = memory.load_mood()
            style = voice_style.compute(text, mood)
            
            success = asyncio.run(_synthesize(text, path, style))
            if success:
                _play_audio_file(path)
                _speaking_flag.clear()
                return
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    if not _interrupt_flag.is_set():
        _speak_pyttsx3(text)
    _speaking_flag.clear()


def speak_streamed(sentence_generator):
    """Streaming TTS: synthesize and play sentences as they arrive from brain.
    sentence_generator yields strings (one sentence each).
    Returns the full assembled text."""
    _interrupt_flag.clear()
    _speaking_flag.set()
    full_text = []

    # Pre-synthesis queue: synthesize next sentence while current plays
    synth_queue = queue.Queue(maxsize=3)
    done_event = threading.Event()

    def _synthesizer():
        """Background thread: synthesize each sentence to a temp file."""
        import memory
        import voice_style
        
        mood = memory.load_mood()
        
        for sentence in sentence_generator:
            if _interrupt_flag.is_set():
                break
            sentence = sentence.strip()
            if not sentence:
                continue
            full_text.append(sentence)
            fd, path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            try:
                style = voice_style.compute(sentence, mood)
                success = asyncio.run(_synthesize(sentence, path, style))
                if success and os.path.getsize(path) > 0:
                    synth_queue.put(path)
                else:
                    # Fallback: just queue the text for pyttsx3
                    synth_queue.put(("pyttsx3", sentence))
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            except Exception:
                synth_queue.put(("pyttsx3", sentence))
                try:
                    os.remove(path)
                except OSError:
                    pass
        done_event.set()

    synth_thread = threading.Thread(target=_synthesizer, daemon=True)
    synth_thread.start()

    # Play sentences as they become available
    while True:
        if _interrupt_flag.is_set():
            break
        try:
            item = synth_queue.get(timeout=0.2)
        except queue.Empty:
            if done_event.is_set() and synth_queue.empty():
                break
            continue

        if isinstance(item, tuple) and item[0] == "pyttsx3":
            _speak_pyttsx3(item[1])
        elif isinstance(item, str):
            _play_audio_file(item)
            try:
                os.remove(item)
            except OSError:
                pass

    _speaking_flag.clear()
    return " ".join(full_text)


def interrupt():
    """Call the moment the user starts talking while she's mid-sentence."""
    _interrupt_flag.set()


def is_speaking() -> bool:
    return _speaking_flag.is_set()
