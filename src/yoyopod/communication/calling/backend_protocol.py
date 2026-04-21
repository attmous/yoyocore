"""Compatibility exports for callers still importing calling.backend_protocol."""

from yoyopod.backends.voip.protocol import VoIPBackend, VoIPIterateMetrics

__all__ = ["VoIPBackend", "VoIPIterateMetrics"]
