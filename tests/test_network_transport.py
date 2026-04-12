"""Unit tests for the UART serial transport."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

from yoyopy.network.transport import SerialTransport, TransportError


class FakeSerial:
    """Minimal pyserial double."""

    def __init__(self) -> None:
        self.is_open = True
        self._response = b"OK\r\n"
        self.written: list[bytes] = []

    def write(self, data: bytes) -> int:
        self.written.append(data)
        return len(data)

    def read_until(self, expected: bytes = b"\n", size: int | None = None) -> bytes:
        return self._response

    def readline(self) -> bytes:
        return self._response

    def read(self, size: int = 1) -> bytes:
        return self._response[:size]

    def reset_input_buffer(self) -> None:
        pass

    def close(self) -> None:
        self.is_open = False

    @property
    def in_waiting(self) -> int:
        return len(self._response)


def test_send_command_returns_response():
    """send_command should write AT command and return parsed response."""
    fake = FakeSerial()
    transport = SerialTransport.__new__(SerialTransport)
    transport._serial = fake
    transport._lock = threading.Lock()

    result = transport.send_command("AT")
    assert "OK" in result
    assert any(b"AT\r\n" in w for w in fake.written)


def test_send_command_raises_on_closed_port():
    """send_command should raise TransportError when port is closed."""
    transport = SerialTransport.__new__(SerialTransport)
    transport._serial = None
    transport._lock = threading.Lock()

    try:
        transport.send_command("AT")
        assert False, "Expected TransportError"
    except TransportError:
        pass
