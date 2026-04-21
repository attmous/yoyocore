"""Compatibility export for callers still importing the legacy Liblinphone backend."""

from yoyopod.backends.voip.liblinphone import LiblinphoneBackend

__all__ = ["LiblinphoneBackend"]
