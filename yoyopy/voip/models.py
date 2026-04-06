"""Shared VoIP models and typed backend events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias


class RegistrationState(Enum):
    """SIP registration states."""

    NONE = "none"
    PROGRESS = "progress"
    OK = "ok"
    CLEARED = "cleared"
    FAILED = "failed"


class CallState(Enum):
    """Call states."""

    IDLE = "idle"
    INCOMING = "incoming"
    OUTGOING = "outgoing_init"
    OUTGOING_PROGRESS = "outgoing_progress"
    OUTGOING_RINGING = "outgoing_ringing"
    OUTGOING_EARLY_MEDIA = "outgoing_early_media"
    CONNECTED = "connected"
    STREAMS_RUNNING = "streams_running"
    PAUSED = "paused"
    PAUSED_BY_REMOTE = "paused_by_remote"
    UPDATED_BY_REMOTE = "updated_by_remote"
    RELEASED = "released"
    ERROR = "error"
    END = "end"


class MessageKind(Enum):
    """Kinds of VoIP messages handled by the Liblinphone backend."""

    TEXT = "text"
    VOICE_NOTE = "voice_note"


class MessageDirection(Enum):
    """Direction of a VoIP message relative to the local endpoint."""

    INCOMING = "incoming"
    OUTGOING = "outgoing"


class MessageDeliveryState(Enum):
    """Delivery state for one VoIP message."""

    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass(slots=True)
class VoIPConfig:
    """VoIP configuration."""

    sip_server: str = "sip.linphone.org"
    sip_username: str = ""
    sip_password: str = ""
    sip_password_ha1: str = ""
    sip_identity: str = ""
    transport: str = "tcp"
    stun_server: str = ""
    file_transfer_server_url: str = ""
    iterate_interval_ms: int = 20
    message_store_dir: str = "data/messages"
    voice_note_store_dir: str = "data/voice_notes"
    voice_note_max_duration_seconds: int = 30
    auto_download_incoming_voice_recordings: bool = True
    playback_dev_id: str = "ALSA: wm8960-soundcard"
    ringer_dev_id: str = "ALSA: wm8960-soundcard"
    capture_dev_id: str = "ALSA: wm8960-soundcard"
    media_dev_id: str = "ALSA: wm8960-soundcard"
    mic_gain: int = 80
    speaker_volume: int = 80

    @staticmethod
    def from_config_manager(config_manager) -> "VoIPConfig":
        """Create a VoIPConfig from the current config manager."""

        return VoIPConfig(
            sip_server=config_manager.get_sip_server(),
            sip_username=config_manager.get_sip_username(),
            sip_password=config_manager.get_sip_password(),
            sip_password_ha1=config_manager.get_sip_password_ha1(),
            sip_identity=config_manager.get_sip_identity(),
            transport=config_manager.get_transport(),
            stun_server=config_manager.get_stun_server(),
            file_transfer_server_url=config_manager.get_file_transfer_server_url(),
            iterate_interval_ms=config_manager.get_voip_iterate_interval_ms(),
            message_store_dir=config_manager.get_message_store_dir(),
            voice_note_store_dir=config_manager.get_voice_note_store_dir(),
            voice_note_max_duration_seconds=config_manager.get_voice_note_max_duration_seconds(),
            auto_download_incoming_voice_recordings=(
                config_manager.get_auto_download_incoming_voice_recordings()
            ),
            playback_dev_id=config_manager.get_playback_device_id(),
            ringer_dev_id=config_manager.get_ringer_device_id(),
            capture_dev_id=config_manager.get_capture_device_id(),
            media_dev_id=config_manager.get_media_device_id(),
            mic_gain=config_manager.get_mic_gain(),
            speaker_volume=config_manager.get_speaker_volume(),
        )


@dataclass(frozen=True, slots=True)
class VoIPMessageRecord:
    """One text or voice-note message known to the local endpoint."""

    id: str
    peer_sip_address: str
    sender_sip_address: str
    recipient_sip_address: str
    kind: MessageKind
    direction: MessageDirection
    delivery_state: MessageDeliveryState
    created_at: str
    updated_at: str
    text: str = ""
    local_file_path: str = ""
    mime_type: str = ""
    duration_ms: int = 0
    unread: bool = False
    display_name: str = ""


@dataclass(frozen=True, slots=True)
class RegistrationStateChanged:
    """Typed event emitted when SIP registration changes."""

    state: RegistrationState


@dataclass(frozen=True, slots=True)
class CallStateChanged:
    """Typed event emitted when the active call state changes."""

    state: CallState


@dataclass(frozen=True, slots=True)
class IncomingCallDetected:
    """Typed event emitted when an incoming call address is detected."""

    caller_address: str


@dataclass(frozen=True, slots=True)
class BackendStopped:
    """Typed event emitted when the backend process exits unexpectedly."""

    reason: str = ""


@dataclass(frozen=True, slots=True)
class MessageReceived:
    """Typed event emitted when a new message is received."""

    message: VoIPMessageRecord


@dataclass(frozen=True, slots=True)
class MessageDeliveryChanged:
    """Typed event emitted when one message delivery state changes."""

    message_id: str
    delivery_state: MessageDeliveryState
    local_file_path: str = ""
    error: str = ""


@dataclass(frozen=True, slots=True)
class MessageDownloadCompleted:
    """Typed event emitted when an incoming message attachment finishes downloading."""

    message_id: str
    local_file_path: str
    mime_type: str = ""


@dataclass(frozen=True, slots=True)
class MessageFailed:
    """Typed event emitted when a message send or receive operation fails."""

    message_id: str
    reason: str


VoIPEvent: TypeAlias = (
    RegistrationStateChanged
    | CallStateChanged
    | IncomingCallDetected
    | BackendStopped
    | MessageReceived
    | MessageDeliveryChanged
    | MessageDownloadCompleted
    | MessageFailed
)
