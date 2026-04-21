"""Compatibility shim for the relocated canonical voice command grammar."""

from yoyopod.integrations.voice.commands import (
    VOICE_COMMAND_GRAMMAR,
    VoiceCommandIntent,
    VoiceCommandMatch,
    VoiceCommandTemplate,
    match_voice_command,
)

__all__ = [
    "VOICE_COMMAND_GRAMMAR",
    "VoiceCommandIntent",
    "VoiceCommandMatch",
    "VoiceCommandTemplate",
    "match_voice_command",
]
