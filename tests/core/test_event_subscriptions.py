"""Tests for typed runtime bus subscription wiring."""

from __future__ import annotations

from types import SimpleNamespace

from yoyopod.core import ScreenChangedEvent, UserActivityEvent
from yoyopod.integrations.location.events import NetworkGpsFixEvent, NetworkGpsNoFixEvent
from yoyopod.integrations.network.events import (
    NetworkPppDownEvent,
    NetworkPppUpEvent,
    NetworkSignalUpdateEvent,
)
from yoyopod.core.event_subscriptions import RuntimeEventSubscriptions
from yoyopod.integrations.power.events import (
    GracefulShutdownCancelled,
    GracefulShutdownRequested,
    LowBatteryWarningRaised,
)


def test_runtime_event_subscriptions_register_all_runtime_handlers() -> None:
    """App runtime wiring should subscribe the expected event handlers exactly once."""

    subscriptions: list[tuple[type[object], object]] = []
    app = SimpleNamespace(
        bus=SimpleNamespace(
            subscribe=lambda event_type, handler: subscriptions.append((event_type, handler))
        ),
        screen_power_service=SimpleNamespace(
            handle_screen_changed_event="screen_changed",
            handle_user_activity_event="user_activity",
            handle_low_battery_warning_event="low_battery",
        ),
        shutdown_service=SimpleNamespace(
            handle_graceful_shutdown_requested_event="shutdown_requested",
            handle_graceful_shutdown_cancelled_event="shutdown_cancelled",
        ),
        network_events=SimpleNamespace(
            handle_network_ppp_up="ppp_up",
            handle_network_signal_update="signal_update",
            handle_network_gps_fix="gps_fix",
            handle_network_gps_no_fix="gps_no_fix",
            handle_network_ppp_down="ppp_down",
        ),
    )

    RuntimeEventSubscriptions(app).register()

    assert subscriptions == [
        (ScreenChangedEvent, "screen_changed"),
        (UserActivityEvent, "user_activity"),
        (LowBatteryWarningRaised, "low_battery"),
        (GracefulShutdownRequested, "shutdown_requested"),
        (GracefulShutdownCancelled, "shutdown_cancelled"),
        (NetworkPppUpEvent, "ppp_up"),
        (NetworkSignalUpdateEvent, "signal_update"),
        (NetworkGpsFixEvent, "gps_fix"),
        (NetworkGpsNoFixEvent, "gps_no_fix"),
        (NetworkPppDownEvent, "ppp_down"),
    ]
