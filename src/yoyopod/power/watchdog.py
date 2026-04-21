"""Compatibility exports for the relocated PiSugar watchdog."""

from yoyopod.backends.power.watchdog import (
    PiSugarWatchdog,
    WatchdogCommandError,
    WatchdogRunner,
    WatchdogRunnerResult,
)

__all__ = [
    "PiSugarWatchdog",
    "WatchdogCommandError",
    "WatchdogRunner",
    "WatchdogRunnerResult",
]
