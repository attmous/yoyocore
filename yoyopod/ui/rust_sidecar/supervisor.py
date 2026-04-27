"""Subprocess supervisor for the Rust UI PoC sidecar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from yoyopod.ui.rust_sidecar.protocol import UiEnvelope, UiProtocolError


class RustUiSidecarError(RuntimeError):
    """Raised when the Rust UI sidecar cannot be controlled."""


@dataclass(slots=True)
class RustUiSidecarSupervisor:
    argv: list[str]
    cwd: Path | None = None
    ready_timeout_seconds: float = 5.0
    process: subprocess.Popen[str] | None = None

    def start(self) -> UiEnvelope:
        if self.process is not None and self.process.poll() is None:
            raise RustUiSidecarError("Rust UI sidecar is already running")

        self.process = subprocess.Popen(
            self.argv,
            cwd=str(self.cwd) if self.cwd is not None else None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        return self.read_event()

    def send(self, envelope: UiEnvelope) -> None:
        process = self._require_process()
        if process.stdin is None:
            raise RustUiSidecarError("Rust UI sidecar stdin is not available")
        process.stdin.write(envelope.to_json_line())
        process.stdin.flush()

    def read_event(self) -> UiEnvelope:
        process = self._require_process()
        if process.stdout is None:
            raise RustUiSidecarError("Rust UI sidecar stdout is not available")
        line = process.stdout.readline()
        if not line:
            raise RustUiSidecarError("Rust UI sidecar exited before emitting an event")
        try:
            return UiEnvelope.from_json_line(line)
        except UiProtocolError as exc:
            raise RustUiSidecarError(str(exc)) from exc

    def stop(self, timeout_seconds: float = 2.0) -> None:
        process = self.process
        if process is None:
            return
        if process.poll() is None:
            try:
                self.send(UiEnvelope.command("ui.shutdown"))
            except Exception:
                pass
            process.terminate()
            try:
                process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1.0)
        self.process = None

    def _require_process(self) -> subprocess.Popen[str]:
        if self.process is None:
            raise RustUiSidecarError("Rust UI sidecar is not running")
        return self.process
