"""Legacy voice public package entrypoint."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yoyopod.integrations.voice import (
        VOICE_COMMAND_GRAMMAR,
        VoiceCaptureRequest,
        VoiceCaptureResult,
        VoiceCommandIntent,
        VoiceCommandMatch,
        VoiceCommandTemplate,
        VoiceManager,
        VoiceService,
        VoiceSettings,
        VoiceTranscript,
        match_voice_command,
    )


_LAZY_EXPORTS = {
    "VOICE_COMMAND_GRAMMAR": "yoyopod.integrations.voice",
    "VoiceCaptureRequest": "yoyopod.integrations.voice",
    "VoiceCaptureResult": "yoyopod.integrations.voice",
    "VoiceCommandIntent": "yoyopod.integrations.voice",
    "VoiceCommandMatch": "yoyopod.integrations.voice",
    "VoiceCommandTemplate": "yoyopod.integrations.voice",
    "VoiceManager": "yoyopod.integrations.voice",
    "VoiceService": "yoyopod.integrations.voice",
    "VoiceSettings": "yoyopod.integrations.voice",
    "VoiceTranscript": "yoyopod.integrations.voice",
    "match_voice_command": "yoyopod.integrations.voice",
}


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = __import__(module_name, fromlist=[name])
    return getattr(module, name)


__all__ = [
    "VOICE_COMMAND_GRAMMAR",
    "VoiceCaptureRequest",
    "VoiceCaptureResult",
    "VoiceCommandIntent",
    "VoiceCommandMatch",
    "VoiceCommandTemplate",
    "VoiceManager",
    "VoiceService",
    "VoiceSettings",
    "VoiceTranscript",
    "match_voice_command",
]
