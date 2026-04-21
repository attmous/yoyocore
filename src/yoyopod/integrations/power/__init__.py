"""Power integration scaffold for the Phase A spine rewrite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from yoyopod.backends.power import PiSugarBackend
from yoyopod.integrations.power.commands import SetRtcAlarmCommand
from yoyopod.integrations.power.handlers import apply_snapshot
from yoyopod.integrations.power.poller import PowerPoller


@dataclass(slots=True)
class PowerIntegration:
    """Runtime handles owned by the scaffold power integration."""

    backend: object
    poller: PowerPoller


__all__ = ["PowerIntegration", "setup", "teardown"]


def setup(
    app: Any,
    *,
    config: object,
    backend: object | None = None,
    poll_interval_seconds: float = 30.0,
) -> PowerIntegration:
    """Register the scaffold power services and poller."""

    actual_backend = backend or PiSugarBackend(config)
    poller = PowerPoller(
        backend=actual_backend,
        scheduler=app.scheduler,
        on_snapshot=lambda snapshot: apply_snapshot(app, snapshot),
        poll_interval_seconds=poll_interval_seconds,
    )
    integration = PowerIntegration(backend=actual_backend, poller=poller)

    app.integrations["power"] = integration

    app.services.register(
        "power",
        "refresh_snapshot",
        lambda data: apply_snapshot(app, actual_backend.get_snapshot()),
    )
    app.services.register(
        "power",
        "sync_time_to_rtc",
        lambda data: _sync_to_rtc(app, actual_backend),
    )
    app.services.register(
        "power",
        "sync_time_from_rtc",
        lambda data: _sync_from_rtc(app, actual_backend),
    )
    app.services.register(
        "power",
        "set_rtc_alarm",
        lambda data: _set_rtc_alarm(app, actual_backend, data),
    )
    app.services.register(
        "power",
        "disable_rtc_alarm",
        lambda data: _disable_rtc_alarm(app, actual_backend),
    )

    return integration


def teardown(app: Any) -> None:
    """Stop the scaffold poller and drop the integration handle."""

    integration = app.integrations.pop("power", None)
    if integration is not None:
        integration.poller.stop()


def _sync_to_rtc(app: Any, backend: object) -> object:
    backend.sync_time_to_rtc()
    return apply_snapshot(app, backend.get_snapshot())


def _sync_from_rtc(app: Any, backend: object) -> object:
    backend.sync_time_from_rtc()
    return apply_snapshot(app, backend.get_snapshot())


def _set_rtc_alarm(app: Any, backend: object, data: SetRtcAlarmCommand) -> object:
    if not isinstance(data, SetRtcAlarmCommand):
        raise TypeError("power.set_rtc_alarm expects SetRtcAlarmCommand")
    backend.set_rtc_alarm(data.when, data.repeat_mask)
    return apply_snapshot(app, backend.get_snapshot())


def _disable_rtc_alarm(app: Any, backend: object) -> object:
    backend.disable_rtc_alarm()
    return apply_snapshot(app, backend.get_snapshot())
