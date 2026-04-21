"""Compatibility shims for relocated canonical power events."""

from yoyopod.integrations.power.events import (
    GracefulShutdownCancelled,
    GracefulShutdownRequested,
    LowBatteryWarningRaised,
    PowerAvailabilityChanged,
    PowerSnapshotUpdated,
)

__all__ = [
    "GracefulShutdownCancelled",
    "GracefulShutdownRequested",
    "LowBatteryWarningRaised",
    "PowerAvailabilityChanged",
    "PowerSnapshotUpdated",
]

