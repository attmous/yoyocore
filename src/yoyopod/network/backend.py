"""Compatibility shim for relocated network modem backends."""

from __future__ import annotations

from yoyopod.backends.network.modem import NetworkBackend, Sim7600Backend

__all__ = ["NetworkBackend", "Sim7600Backend"]
