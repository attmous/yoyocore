"""Tests for the scaffold app shell."""

from __future__ import annotations

from yoyopod.core import LifecycleEvent, YoyoPodAppShell


def test_app_shell_start_stop_and_tick_emit_lifecycle_events() -> None:
    app = YoyoPodAppShell(strict_bus=True)
    seen: list[LifecycleEvent] = []
    ui_ticks: list[str] = []
    app.bus.subscribe(LifecycleEvent, seen.append)
    app.set_ui_tick_callback(lambda: ui_ticks.append("tick"))

    app.start()
    app.tick()
    app.stop()
    app.tick()

    assert [event.phase for event in seen] == ["starting", "ready", "stopping", "stopped"]
    assert ui_ticks == ["tick", "tick"]
    assert app.running is False


def test_app_shell_run_supports_iteration_bounded_loops() -> None:
    app = YoyoPodAppShell(strict_bus=True)
    seen: list[str] = []
    app.set_ui_tick_callback(lambda: seen.append("tick"))

    processed = app.run(sleep_seconds=0.0, max_iterations=2)

    assert processed >= 2
    assert seen == ["tick", "tick"]
    assert app.config is None
    assert app.integrations == {}
