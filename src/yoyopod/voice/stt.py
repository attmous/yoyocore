"""Compatibility exports for the relocated voice STT backends."""

from yoyopod.backends.voice.stt import (
    NullSpeechToTextBackend,
    SpeechToTextBackend,
    VoskSpeechToTextBackend,
)

__all__ = [
    "NullSpeechToTextBackend",
    "SpeechToTextBackend",
    "VoskSpeechToTextBackend",
]
