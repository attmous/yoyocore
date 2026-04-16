"""Power management foundation for YoyoPod."""

from yoyopod.config.models import PowerConfig
from yoyopod.power.backend import (
    PiSugarAutoTransport,
    PiSugarBackend,
    PiSugarTCPTransport,
    PiSugarUnixTransport,
    PowerBackend,
    PowerTransportError,
    build_pisugar_transport,
)
from yoyopod.power.events import (
    GracefulShutdownCancelled,
    GracefulShutdownRequested,
    LowBatteryWarningRaised,
    PowerAvailabilityChanged,
    PowerSnapshotUpdated,
)
from yoyopod.power.manager import PowerManager
from yoyopod.power.models import (
    BatteryState,
    PowerDeviceInfo,
    PowerSnapshot,
    RTCState,
    ShutdownState,
)
from yoyopod.power.policies import PowerSafetyPolicy
from yoyopod.power.runtime import PowerRuntimeService
from yoyopod.power.watchdog import PiSugarWatchdog, WatchdogCommandError

__all__ = [
    "PowerBackend",
    "PowerTransportError",
    "PiSugarBackend",
    "PiSugarTCPTransport",
    "PiSugarUnixTransport",
    "PiSugarAutoTransport",
    "build_pisugar_transport",
    "PowerManager",
    "PowerRuntimeService",
    "PiSugarWatchdog",
    "WatchdogCommandError",
    "PowerConfig",
    "PowerDeviceInfo",
    "BatteryState",
    "RTCState",
    "ShutdownState",
    "PowerSnapshot",
    "PowerSnapshotUpdated",
    "PowerAvailabilityChanged",
    "LowBatteryWarningRaised",
    "GracefulShutdownRequested",
    "GracefulShutdownCancelled",
    "PowerSafetyPolicy",
]
