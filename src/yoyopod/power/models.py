"""Compatibility shims for the relocated canonical power models."""

from yoyopod.integrations.power.models import (
    BatteryState,
    PowerDeviceInfo,
    PowerSnapshot,
    RTCState,
    ShutdownState,
)

__all__ = [
    "BatteryState",
    "PowerDeviceInfo",
    "PowerSnapshot",
    "RTCState",
    "ShutdownState",
]
