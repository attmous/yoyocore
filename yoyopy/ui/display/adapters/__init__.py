"""
Display adapter implementations.

Each adapter provides a hardware-specific implementation of the DisplayHAL interface.

Adapters are imported lazily to avoid side effects (GPIO claims, driver loading)
when the adapter is not selected. Use the display factory to create adapters.
"""

__all__ = [
    "PimoroniDisplayAdapter",
    "WhisplayDisplayAdapter",
    "SimulationDisplayAdapter",
    "CubiePimoroniAdapter",
]


def __getattr__(name: str):
    if name == "PimoroniDisplayAdapter":
        from yoyopy.ui.display.adapters.pimoroni import PimoroniDisplayAdapter

        return PimoroniDisplayAdapter
    if name == "WhisplayDisplayAdapter":
        from yoyopy.ui.display.adapters.whisplay import WhisplayDisplayAdapter

        return WhisplayDisplayAdapter
    if name == "SimulationDisplayAdapter":
        from yoyopy.ui.display.adapters.simulation import SimulationDisplayAdapter

        return SimulationDisplayAdapter
    if name == "CubiePimoroniAdapter":
        from yoyopy.ui.display.adapters.cubie_pimoroni import CubiePimoroniAdapter

        return CubiePimoroniAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
