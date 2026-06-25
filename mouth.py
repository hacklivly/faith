"""
Isabella - the mouth.

Edge-TTS streaming synthesis + PyAudio playback.
"""
import threading

import voice_engine

_interrupt_flag = threading.Event()
_speaking_flag = threading.Event()


def set_style(style: dict):
    pass  # Vibe is handled by voice_engine


def speak(text: str):
    """Play text via edge-tts."""
    _interrupt_flag.clear()
    _speaking_flag.set()
    try:
        voice_engine.speak(text)
    finally:
        _speaking_flag.clear()


def speak_streamed(sentence_generator):
    """Play sentences one by one via browser. Returns full text."""
    _interrupt_flag.clear()
    _speaking_flag.set()
    full_text = []

    try:
        for sentence in sentence_generator:
            if _interrupt_flag.is_set():
                voice_engine.stop()
                break
            sentence = sentence.strip()
            if not sentence:
                continue
            full_text.append(sentence)
            voice_engine.speak(sentence)
    finally:
        _speaking_flag.clear()

    return " ".join(full_text)


def interrupt():
    """Stop playback."""
    _interrupt_flag.set()
    voice_engine.stop()


def is_speaking() -> bool:
    return _speaking_flag.is_set() or voice_engine.is_playing()
