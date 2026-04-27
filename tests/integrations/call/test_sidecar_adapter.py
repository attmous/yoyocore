"""Unit tests for :class:`SidecarBackendAdapter`.

The adapter owns command->backend dispatch and backend->protocol event
translation inside the sidecar process. These tests run the adapter in
isolation (no supervisor, no subprocess) by feeding it commands directly
and reading the events it writes onto a real ``multiprocessing.Pipe``.
"""

from __future__ import annotations

import multiprocessing
import time
from multiprocessing.connection import Connection
from typing import Any

import pytest

from yoyopod.backends.voip.mock_backend import MockVoIPBackend
from yoyopod.integrations.call.models import (
    BackendStopped,
    CallState,
    CallStateChanged as BackendCallStateChanged,
    IncomingCallDetected,
    RegistrationState,
    RegistrationStateChanged as BackendRegistrationStateChanged,
    VoIPConfig,
)
from yoyopod.integrations.call.sidecar_adapter import SidecarBackendAdapter
from yoyopod.integrations.call.sidecar_protocol import (
    Accept,
    CallStateChanged,
    Configure,
    Dial,
    Error,
    Hangup,
    IncomingCall,
    Log,
    MediaStateChanged,
    Ping,
    Pong,
    Register,
    RegistrationStateChanged,
    Reject,
    SetMute,
    SetVolume,
    Unregister,
    decode_event,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pipe() -> tuple[Connection, Connection]:
    parent, child = multiprocessing.Pipe(duplex=True)
    yield parent, child
    try:
        parent.close()
    except OSError:
        pass
    try:
        child.close()
    except OSError:
        pass


@pytest.fixture
def parent_conn(pipe: tuple[Connection, Connection]) -> Connection:
    return pipe[0]


@pytest.fixture
def child_conn(pipe: tuple[Connection, Connection]) -> Connection:
    return pipe[1]


@pytest.fixture
def mock_backend() -> MockVoIPBackend:
    return MockVoIPBackend()


@pytest.fixture
def adapter(child_conn: Connection, mock_backend: MockVoIPBackend) -> SidecarBackendAdapter:
    captured: list[MockVoIPBackend] = []

    def factory(_config: VoIPConfig) -> MockVoIPBackend:
        captured.append(mock_backend)
        return mock_backend

    instance = SidecarBackendAdapter(conn=child_conn, backend_factory=factory)
    instance.__test_factory_calls__ = captured  # type: ignore[attr-defined]
    yield instance
    instance.shutdown()


def _drain(conn: Connection, *, timeout: float = 0.5) -> list[Any]:
    """Read every event currently available on the pipe within ``timeout``."""

    deadline = time.monotonic() + timeout
    events: list[Any] = []
    while time.monotonic() < deadline:
        if conn.poll(timeout=0.05):
            try:
                events.append(decode_event(conn.recv_bytes()))
            except (BrokenPipeError, EOFError, OSError):
                break
        elif events:
            break
    return events


def _wait_for(predicate, *, timeout: float = 0.5) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return False


def _config_dict(**overrides: Any) -> dict[str, Any]:
    base = VoIPConfig(sip_server="sip.example.com", sip_identity="sip:alice@example.com")
    payload = {
        f.name: getattr(base, f.name)
        for f in [field for field in VoIPConfig.__dataclass_fields__.values()]
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Configure
# ---------------------------------------------------------------------------


def test_configure_creates_backend_and_logs_info(
    adapter: SidecarBackendAdapter, parent_conn: Connection, mock_backend: MockVoIPBackend
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    events = _drain(parent_conn)

    assert any(
        isinstance(event, Log) and event.level == "INFO" and "configured backend" in event.message
        for event in events
    )
    # Adapter should have asked the factory for one backend.
    assert mock_backend.event_callbacks, "factory should have wired backend callbacks"


def test_configure_with_unknown_field_returns_invalid_config_error(
    adapter: SidecarBackendAdapter, parent_conn: Connection
) -> None:
    bogus = _config_dict()
    bogus["not_a_real_field"] = "boom"
    adapter.handle_command(Configure(config=bogus, cmd_id=42))
    events = _drain(parent_conn)
    errors = [event for event in events if isinstance(event, Error)]
    assert any(error.code == "invalid_config" and error.cmd_id == 42 for error in errors), events


# ---------------------------------------------------------------------------
# Register / Unregister
# ---------------------------------------------------------------------------


def test_register_before_configure_returns_not_configured(
    adapter: SidecarBackendAdapter, parent_conn: Connection
) -> None:
    adapter.handle_command(Register(cmd_id=7))
    events = _drain(parent_conn)
    assert any(
        isinstance(event, Error) and event.code == "not_configured" and event.cmd_id == 7
        for event in events
    )


def test_register_starts_backend_and_iterate_thread(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    _drain(parent_conn)

    adapter.handle_command(Register(cmd_id=2))
    assert _wait_for(lambda: mock_backend.running)
    assert mock_backend.running is True
    assert adapter._iterate_thread is not None
    assert adapter._iterate_thread.is_alive()


def test_register_when_backend_start_returns_false_emits_error(
    parent_conn: Connection, child_conn: Connection
) -> None:
    failing_backend = MockVoIPBackend(start_result=False)

    def factory(_config: VoIPConfig) -> MockVoIPBackend:
        return failing_backend

    adapter = SidecarBackendAdapter(conn=child_conn, backend_factory=factory)
    try:
        adapter.handle_command(Configure(config=_config_dict()))
        _drain(parent_conn)
        adapter.handle_command(Register(cmd_id=3))
        events = _drain(parent_conn)
        assert any(
            isinstance(event, Error) and event.code == "register_failed" and event.cmd_id == 3
            for event in events
        )
    finally:
        adapter.shutdown()


def test_unregister_stops_backend_and_iterate_thread(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    adapter.handle_command(Register(cmd_id=1))
    _drain(parent_conn)
    assert _wait_for(lambda: mock_backend.running)

    adapter.handle_command(Unregister())
    assert _wait_for(lambda: not mock_backend.running)
    assert adapter._wait_for_iterate_thread_to_exit(timeout=1.0)


# ---------------------------------------------------------------------------
# Call control
# ---------------------------------------------------------------------------


def test_dial_assigns_call_id_and_calls_backend(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    adapter.handle_command(Register(cmd_id=1))
    _drain(parent_conn)

    adapter.handle_command(Dial(uri="sip:bob@example.com", cmd_id=10))
    assert mock_backend.commands[-1] == "call sip:bob@example.com"
    assert adapter._current_call_id is not None


def test_dial_when_call_in_progress_returns_call_in_progress_error(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    adapter.handle_command(Register(cmd_id=1))
    _drain(parent_conn)

    adapter.handle_command(Dial(uri="sip:bob@example.com", cmd_id=10))
    adapter.handle_command(Dial(uri="sip:carol@example.com", cmd_id=11))

    events = _drain(parent_conn)
    assert any(
        isinstance(event, Error) and event.code == "call_in_progress" and event.cmd_id == 11
        for event in events
    )


def test_accept_with_unknown_call_id_returns_error(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    adapter.handle_command(Register(cmd_id=1))
    _drain(parent_conn)

    adapter.handle_command(Accept(call_id="call-bogus", cmd_id=20))
    events = _drain(parent_conn)
    assert any(
        isinstance(event, Error) and event.code == "unknown_call_id" and event.cmd_id == 20
        for event in events
    )
    assert "answer" not in mock_backend.commands


def test_accept_with_correct_call_id_calls_backend(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    adapter.handle_command(Register(cmd_id=1))
    _drain(parent_conn)

    mock_backend.emit(IncomingCallDetected(caller_address="sip:bob@example.com"))
    events = _drain(parent_conn)
    incoming = next(event for event in events if isinstance(event, IncomingCall))

    adapter.handle_command(Accept(call_id=incoming.call_id, cmd_id=21))
    assert "answer" in mock_backend.commands


def test_hangup_with_correct_call_id_calls_backend(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    adapter.handle_command(Register(cmd_id=1))
    _drain(parent_conn)

    mock_backend.emit(IncomingCallDetected(caller_address="sip:bob@example.com"))
    events = _drain(parent_conn)
    incoming = next(event for event in events if isinstance(event, IncomingCall))

    adapter.handle_command(Hangup(call_id=incoming.call_id, cmd_id=22))
    assert "terminate" in mock_backend.commands


def test_set_mute_emits_media_state_changed(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    adapter.handle_command(Register(cmd_id=1))
    _drain(parent_conn)

    mock_backend.emit(IncomingCallDetected(caller_address="sip:bob@example.com"))
    events = _drain(parent_conn)
    incoming = next(event for event in events if isinstance(event, IncomingCall))

    adapter.handle_command(SetMute(call_id=incoming.call_id, on=True))
    events = _drain(parent_conn)
    assert "mute" in mock_backend.commands
    assert any(
        isinstance(event, MediaStateChanged)
        and event.call_id == incoming.call_id
        and event.mic_muted
        for event in events
    )


def test_set_volume_does_not_call_backend_but_emits_media_state(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    adapter.handle_command(Register(cmd_id=1))
    _drain(parent_conn)

    mock_backend.emit(IncomingCallDetected(caller_address="sip:bob@example.com"))
    events = _drain(parent_conn)
    incoming = next(event for event in events if isinstance(event, IncomingCall))

    adapter.handle_command(SetVolume(call_id=incoming.call_id, level=0.4))
    events = _drain(parent_conn)
    media = [event for event in events if isinstance(event, MediaStateChanged)]
    assert media and media[-1].speaker_volume == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# Backend events -> protocol events
# ---------------------------------------------------------------------------


def test_backend_registration_state_propagates(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    _drain(parent_conn)

    mock_backend.emit(BackendRegistrationStateChanged(state=RegistrationState.OK))
    events = _drain(parent_conn)
    assert any(
        isinstance(event, RegistrationStateChanged) and event.state == "ok" for event in events
    )


def test_backend_call_state_propagates_with_call_id(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    _drain(parent_conn)

    mock_backend.emit(IncomingCallDetected(caller_address="sip:caller@example.com"))
    events = _drain(parent_conn)
    incoming = next(event for event in events if isinstance(event, IncomingCall))

    mock_backend.emit(BackendCallStateChanged(state=CallState.CONNECTED))
    events = _drain(parent_conn)
    assert any(
        isinstance(event, CallStateChanged)
        and event.call_id == incoming.call_id
        and event.state == "connected"
        for event in events
    )


def test_call_released_clears_current_call_id(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    _drain(parent_conn)

    mock_backend.emit(IncomingCallDetected(caller_address="sip:caller@example.com"))
    _drain(parent_conn)

    mock_backend.emit(BackendCallStateChanged(state=CallState.RELEASED))
    _drain(parent_conn)
    assert adapter._current_call_id is None


def test_backend_stopped_emits_error_event(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    _drain(parent_conn)

    mock_backend.emit(BackendStopped(reason="link reset"))
    events = _drain(parent_conn)
    assert any(
        isinstance(event, Error)
        and event.code == "backend_stopped"
        and "link reset" in event.message
        for event in events
    )


# ---------------------------------------------------------------------------
# Ping
# ---------------------------------------------------------------------------


def test_ping_returns_pong_without_backend(
    adapter: SidecarBackendAdapter, parent_conn: Connection
) -> None:
    adapter.handle_command(Ping(cmd_id=99))
    events = _drain(parent_conn)
    assert any(isinstance(event, Pong) and event.cmd_id == 99 for event in events)


# ---------------------------------------------------------------------------
# Reject path
# ---------------------------------------------------------------------------


def test_reject_with_correct_call_id_calls_backend(
    adapter: SidecarBackendAdapter,
    parent_conn: Connection,
    mock_backend: MockVoIPBackend,
) -> None:
    adapter.handle_command(Configure(config=_config_dict()))
    adapter.handle_command(Register(cmd_id=1))
    _drain(parent_conn)

    mock_backend.emit(IncomingCallDetected(caller_address="sip:caller@example.com"))
    events = _drain(parent_conn)
    incoming = next(event for event in events if isinstance(event, IncomingCall))

    adapter.handle_command(Reject(call_id=incoming.call_id, cmd_id=15))
    assert "decline" in mock_backend.commands
