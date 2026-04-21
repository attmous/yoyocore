"""Compatibility export for callers still importing calling.mock_backend."""

from yoyopod.backends.voip.mock_backend import MockVoIPBackend

__all__ = ["MockVoIPBackend"]
