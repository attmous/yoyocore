"""Compatibility alias for the relocated Liblinphone binding module."""

from yoyopod.backends.voip.binding import (
    LiblinphoneBinding,
    LiblinphoneBindingError,
    LiblinphoneNativeEvent,
)

__all__ = [
    "LiblinphoneBinding",
    "LiblinphoneBindingError",
    "LiblinphoneNativeEvent",
]
