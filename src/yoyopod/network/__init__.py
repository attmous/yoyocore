"""App-facing seams for the network domain."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yoyopod.config.models import NetworkConfig
    from yoyopod.network.backend import NetworkBackend, Sim7600Backend
    from yoyopod.network.manager import NetworkManager
    from yoyopod.network.models import GpsCoordinate, ModemPhase, ModemState, SignalInfo


_EXPORTS = {
    "GpsCoordinate": ("yoyopod.network.models", "GpsCoordinate"),
    "ModemPhase": ("yoyopod.network.models", "ModemPhase"),
    "ModemState": ("yoyopod.network.models", "ModemState"),
    "NetworkBackend": ("yoyopod.network.backend", "NetworkBackend"),
    "NetworkConfig": ("yoyopod.config.models", "NetworkConfig"),
    "NetworkManager": ("yoyopod.network.manager", "NetworkManager"),
    "SignalInfo": ("yoyopod.network.models", "SignalInfo"),
    "Sim7600Backend": ("yoyopod.network.backend", "Sim7600Backend"),
}


def __getattr__(name: str) -> Any:
    """Load public network exports lazily to avoid submodule import cycles."""

    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = __import__(module_name, fromlist=[attribute])
    return getattr(module, attribute)

__all__ = [
    "GpsCoordinate",
    "ModemPhase",
    "ModemState",
    "NetworkBackend",
    "NetworkConfig",
    "NetworkManager",
    "SignalInfo",
    "Sim7600Backend",
]
