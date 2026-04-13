"""Tests for network status propagation into shared UI state."""

from __future__ import annotations

from yoyopy.app import YoyoPodApp
from yoyopy.app_context import AppContext
from yoyopy.events import (
    NetworkGpsFixEvent,
    NetworkPppDownEvent,
    NetworkPppUpEvent,
    NetworkSignalUpdateEvent,
)
from yoyopy.ui.screens.lvgl_status import network_status_kwargs


def test_network_status_kwargs_normalize_context_state() -> None:
    """LVGL status-bar helpers should clamp and normalize AppContext values."""

    context = AppContext()
    context.update_network_status(
        network_enabled=True,
        signal_bars=9,
        connected=True,
        gps_has_fix=True,
    )

    assert network_status_kwargs(context) == {
        "network_enabled": 1,
        "network_connected": 1,
        "signal_strength": 4,
        "gps_has_fix": 1,
    }


def test_network_event_handlers_keep_context_status_in_sync() -> None:
    """App-level network handlers should keep shared UI state current."""

    app = YoyoPodApp(simulate=True)
    app.context = AppContext()

    app._handle_network_ppp_up(NetworkPppUpEvent(connection_type="4g"))
    assert app.context.network_enabled is True
    assert app.context.is_connected is True
    assert app.context.connection_type == "4g"

    app._handle_network_signal_update(NetworkSignalUpdateEvent(bars=2, csq=12))
    assert app.context.signal_strength == 2

    app._handle_network_gps_fix(NetworkGpsFixEvent(lat=0.0, lng=0.0))
    assert app.context.gps_has_fix is True

    app._handle_network_ppp_down(NetworkPppDownEvent(reason="link lost"))
    assert app.context.network_enabled is True
    assert app.context.is_connected is False
    assert app.context.connection_type == "none"
    assert app.context.gps_has_fix is False
