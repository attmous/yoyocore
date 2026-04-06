"""VoIP module exports for Liblinphone-backed calls and messaging."""

from yoyopy.voip.backend import LiblinphoneBackend, MockVoIPBackend, VoIPBackend
from yoyopy.voip.history import CallHistoryEntry, CallHistoryStore
from yoyopy.voip.manager import VoIPManager, VoiceNoteDraft
from yoyopy.voip.messages import VoIPMessageStore
from yoyopy.voip.models import (
    BackendStopped,
    CallState,
    CallStateChanged,
    IncomingCallDetected,
    MessageDeliveryChanged,
    MessageDeliveryState,
    MessageDirection,
    MessageDownloadCompleted,
    MessageFailed,
    MessageKind,
    MessageReceived,
    RegistrationState,
    RegistrationStateChanged,
    VoIPConfig,
    VoIPEvent,
    VoIPMessageRecord,
)

__all__ = [
    "VoIPManager",
    "VoiceNoteDraft",
    "VoIPMessageStore",
    "CallHistoryEntry",
    "CallHistoryStore",
    "VoIPBackend",
    "LiblinphoneBackend",
    "MockVoIPBackend",
    "VoIPConfig",
    "VoIPMessageRecord",
    "RegistrationState",
    "CallState",
    "MessageKind",
    "MessageDirection",
    "MessageDeliveryState",
    "RegistrationStateChanged",
    "CallStateChanged",
    "IncomingCallDetected",
    "MessageReceived",
    "MessageDeliveryChanged",
    "MessageDownloadCompleted",
    "MessageFailed",
    "BackendStopped",
    "VoIPEvent",
]
