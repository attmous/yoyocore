"""Unit tests for the split navigation soak runner."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import yoyopod.cli.pi.navigation.runner as runner_module

from yoyopod.cli.pi.navigation.runner import NavigationSoakRunner
from yoyopod.ui.input import InteractionProfile


def _install_fake_app(
    monkeypatch,
    *,
    setup_result: bool = True,
    backend_kind: str = "lvgl",
    interaction_profile: InteractionProfile = InteractionProfile.ONE_BUTTON,
):
    """Install a fake yoyopod.app module for runner tests."""

    class FakeApp:
        instances: list["FakeApp"] = []

        def __init__(self, *, config_dir: str, simulate: bool) -> None:
            assert config_dir == "config"
            assert simulate is False
            self.display = SimpleNamespace(backend_kind=backend_kind)
            self.screen_manager = SimpleNamespace(
                get_current_screen=lambda: SimpleNamespace(route_name="hub")
            )
            self.input_manager = SimpleNamespace(
                interaction_profile=interaction_profile,
                simulate_action=lambda _action: None,
            )
            self.power_runtime = SimpleNamespace(
                start_watchdog=lambda *, now: self.watchdog_starts.append(now)
            )
            self.music_backend = None
            self.context = None
            self.event_bus = SimpleNamespace(publish=lambda _event: None)
            self._screen_timeout_seconds = 0.0
            self._last_user_activity_at = 0.0
            self.watchdog_starts: list[float] = []
            self.stop_calls = 0
            type(self).instances.append(self)

        def setup(self) -> bool:
            return setup_result

        def stop(self) -> None:
            self.stop_calls += 1

    fake_module = ModuleType("yoyopod.app")
    fake_module.YoyoPodApp = FakeApp
    monkeypatch.setitem(sys.modules, "yoyopod.app", fake_module)
    return FakeApp


class _FakeRuntimePump:
    """Small runtime pump double for orchestration tests."""

    instances: list["_FakeRuntimePump"] = []

    def __init__(self, app, stats) -> None:
        self.app = app
        self.stats = stats
        self.calls: list[float] = []
        type(self).instances.append(self)

    def run_for(self, duration_seconds: float) -> None:
        self.calls.append(duration_seconds)


class _FakeExercises:
    """Track which exercise hooks the runner invokes."""

    def __init__(self) -> None:
        self.require_calls: list[str] = []
        self.cycle_calls = 0
        self.idle_calls: list[tuple[str, float]] = []
        self.sleep_wake_calls = 0

    def require_screen(self, expected_screen: str) -> None:
        self.require_calls.append(expected_screen)

    def exercise_cycle(self) -> None:
        self.cycle_calls += 1

    def idle_phase(self, label: str, duration_seconds: float) -> None:
        self.idle_calls.append((label, duration_seconds))

    def exercise_sleep_wake(self) -> None:
        self.sleep_wake_calls += 1


def test_navigation_soak_runner_returns_setup_failure_and_stops_app(monkeypatch) -> None:
    """Runner should clean up the app when setup fails."""

    fake_app_type = _install_fake_app(monkeypatch, setup_result=False)
    runner = NavigationSoakRunner(
        config_dir="config",
        cycles=2,
        hold_seconds=0.35,
        idle_seconds=3.0,
        tail_idle_seconds=10.0,
        with_playback=False,
        provision_test_music=False,
        test_music_dir="/tmp/test-music",
        skip_sleep=False,
    )

    ok, details = runner.run()

    assert (ok, details) == (False, "app setup failed")
    assert fake_app_type.instances[0].stop_calls == 1


def test_navigation_soak_runner_uses_exercise_helper_for_cycles(monkeypatch) -> None:
    """Runner should orchestrate setup, initial pump, cycles, and cleanup."""

    fake_app_type = _install_fake_app(monkeypatch)
    _FakeRuntimePump.instances.clear()
    monkeypatch.setattr(runner_module, "_RuntimePump", _FakeRuntimePump)

    runner = NavigationSoakRunner(
        config_dir="config",
        cycles=3,
        hold_seconds=0.4,
        idle_seconds=1.5,
        tail_idle_seconds=2.0,
        with_playback=False,
        provision_test_music=False,
        test_music_dir="/tmp/test-music",
        skip_sleep=True,
    )
    fake_exercises = _FakeExercises()
    runner._exercises = fake_exercises
    monkeypatch.setattr(runner, "_summary_details", lambda: "summary")

    ok, details = runner.run()

    app = fake_app_type.instances[0]
    pump = _FakeRuntimePump.instances[0]
    assert (ok, details) == (True, "summary")
    assert app.watchdog_starts
    assert app.stop_calls == 1
    assert pump.calls == [0.4]
    assert fake_exercises.require_calls == ["hub"]
    assert fake_exercises.cycle_calls == 3
    assert fake_exercises.idle_calls == [("hub_tail_idle", 2.0)]
    assert fake_exercises.sleep_wake_calls == 1


def test_navigation_soak_runner_rejects_non_one_button_profiles(monkeypatch) -> None:
    """Runner should fail fast when the active input profile is not one-button."""

    fake_app_type = _install_fake_app(
        monkeypatch,
        interaction_profile=InteractionProfile.STANDARD,
    )
    _FakeRuntimePump.instances.clear()
    monkeypatch.setattr(runner_module, "_RuntimePump", _FakeRuntimePump)

    runner = NavigationSoakRunner(
        config_dir="config",
        cycles=1,
        hold_seconds=0.35,
        idle_seconds=3.0,
        tail_idle_seconds=10.0,
        with_playback=False,
        provision_test_music=False,
        test_music_dir="/tmp/test-music",
        skip_sleep=False,
    )

    ok, details = runner.run()

    assert (ok, details) == (False, "profile is standard, expected one_button")
    assert fake_app_type.instances[0].stop_calls == 1
