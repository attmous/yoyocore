"""Compatibility facade for historical communication imports."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yoyopod.integrations.call import (
        CallHistoryEntry,
        CallHistoryStore,
        CallState,
        MessageDeliveryState,
        MessageDirection,
        MessageKind,
        MessagingService,
        RegistrationState,
        VoIPConfig,
        VoIPIterateMetrics,
        VoIPManager,
        VoIPMessageRecord,
        VoIPMessageStore,
        VoiceNoteDraft,
        VoiceNoteService,
    )

_LAZY_EXPORTS = {
    "CallHistoryEntry": "yoyopod.integrations.call",
    "CallHistoryStore": "yoyopod.integrations.call",
    "CallState": "yoyopod.integrations.call",
    "MessageDeliveryState": "yoyopod.integrations.call",
    "MessageDirection": "yoyopod.integrations.call",
    "MessageKind": "yoyopod.integrations.call",
    "MessagingService": "yoyopod.integrations.call",
    "RegistrationState": "yoyopod.integrations.call",
    "VoIPConfig": "yoyopod.integrations.call",
    "VoIPIterateMetrics": "yoyopod.integrations.call",
    "VoIPManager": "yoyopod.integrations.call",
    "VoIPMessageRecord": "yoyopod.integrations.call",
    "VoIPMessageStore": "yoyopod.integrations.call",
    "VoiceNoteDraft": "yoyopod.integrations.call",
    "VoiceNoteService": "yoyopod.integrations.call",
}

def __getattr__(name: str) -> Any:
    """Load relocated call exports lazily for legacy communication imports."""

    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    return getattr(import_module(module_name), name)

__all__ = list(_LAZY_EXPORTS)
