"""Compatibility exports for the relocated voice TTS backends."""

from yoyopod.backends.voice.tts import (
    EspeakNgTextToSpeechBackend,
    NullTextToSpeechBackend,
    TextToSpeechBackend,
)

__all__ = [
    "EspeakNgTextToSpeechBackend",
    "NullTextToSpeechBackend",
    "TextToSpeechBackend",
]
