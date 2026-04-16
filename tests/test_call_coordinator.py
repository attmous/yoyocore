"""Focused tests for the call coordinator's config-driven status behavior."""

from __future__ import annotations

from yoyopod.app_context import AppContext
from yoyopod.communication import RegistrationState
from yoyopod.coordinators.call import CallCoordinator
from yoyopod.coordinators.runtime import CoordinatorRuntime
from yoyopod.fsm import CallFSM, CallInterruptionPolicy, MusicFSM


class _ScreenCoordinatorStub:
    """Small screen-coordinator double for call-coordinator tests."""

    def __init__(self) -> None:
        self.refresh_calls = 0

    def refresh_call_screen_if_visible(self) -> None:
        self.refresh_calls += 1


class _ConfigManagerStub:
    """Small config-manager double exposing only the SIP accessors under test."""

    def __init__(self, *, sip_identity: str = "", sip_username: str = "") -> None:
        self._sip_identity = sip_identity
        self._sip_username = sip_username

    def get_sip_identity(self) -> str:
        return self._sip_identity

    def get_sip_username(self) -> str:
        return self._sip_username


def _build_runtime(*, config_manager: _ConfigManagerStub, context: AppContext) -> CoordinatorRuntime:
    """Create the minimal coordinator runtime required by CallCoordinator."""

    return CoordinatorRuntime(
        music_fsm=MusicFSM(),
        call_fsm=CallFSM(),
        call_interruption_policy=CallInterruptionPolicy(),
        screen_manager=None,
        music_backend=None,
        power_manager=None,
        now_playing_screen=None,
        call_screen=None,
        power_screen=None,
        incoming_call_screen=None,
        outgoing_call_screen=None,
        in_call_screen=None,
        config_manager=config_manager,
        context=context,
    )


def test_registration_change_uses_config_manager_for_voip_configured_status() -> None:
    """VoIP status should come from the canonical config manager, not legacy app config dicts."""

    context = AppContext()
    runtime = _build_runtime(
        config_manager=_ConfigManagerStub(sip_username="kid@example.com"),
        context=context,
    )
    screen_coordinator = _ScreenCoordinatorStub()
    coordinator = CallCoordinator(
        runtime=runtime,
        screen_coordinator=screen_coordinator,
        auto_resume_after_call=True,
    )

    coordinator.handle_registration_change(RegistrationState.OK)

    assert context.voip.configured is True
    assert context.voip.ready is True
    assert runtime.voip_ready is True
    assert screen_coordinator.refresh_calls == 1
