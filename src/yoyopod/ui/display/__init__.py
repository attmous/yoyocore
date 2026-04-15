"""
Display HAL for YoyoPod.

Provides hardware abstraction for various display types:
- Pimoroni Display HAT Mini (320×240 landscape)
- PiSugar Whisplay HAT (240×280 portrait)
- Simulation mode (for development without hardware)

The Display class provides a unified interface that works with any supported hardware.
"""

from yoyopod.ui.display.factory import detect_hardware, get_display, get_hardware_info
from yoyopod.ui.display.hal import DisplayHAL
from yoyopod.ui.display.manager import Display

__all__ = [
    'DisplayHAL',
    'Display',
    'get_display',
    'detect_hardware',
    'get_hardware_info',
]
