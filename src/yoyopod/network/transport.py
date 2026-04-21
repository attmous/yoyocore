"""Compatibility shim for the relocated UART transport."""

from __future__ import annotations

from yoyopod.backends.network.transport import SerialTransport, TransportError

__all__ = ["SerialTransport", "TransportError"]
