"""Compatibility export for callers still importing the legacy Liblinphone binding."""

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
