"""Minimal app shell for the Phase A spine scaffold."""

from __future__ import annotations

import time
import threading
from typing import Callable

from yoyopod.core.bus import Bus
from yoyopod.core.events import LifecycleEvent
from yoyopod.core.logbuffer import LogBuffer
from yoyopod.core.scheduler import MainThreadScheduler
from yoyopod.core.services import Services
from yoyopod.core.states import States


class YoyoPodAppShell:
    """Bundle the scaffold primitives without touching the legacy runtime."""

    def __init__(self, strict_bus: bool = False, log_buffer_size: int = 256) -> None:
        self.main_thread_id = threading.get_ident()
        self.bus = Bus(main_thread_id=self.main_thread_id, strict=strict_bus)
        self.scheduler = MainThreadScheduler(main_thread_id=self.main_thread_id)
        self.log_buffer: LogBuffer[dict[str, object]] = LogBuffer(maxlen=log_buffer_size)
        self.states = States(self.bus)
        self.services = Services(self.bus, diagnostics_log=self.log_buffer)
        self.config: object | None = None
        self.integrations: dict[str, object] = {}
        self.running = False
        self._ui_tick_callback: Callable[[], None] | None = None

    def set_ui_tick_callback(self, callback: Callable[[], None] | None) -> None:
        """Replace the optional UI tick callback."""

        self._ui_tick_callback = callback

    def start(self) -> None:
        """Mark the scaffold shell as running and queue lifecycle events."""

        self.running = True
        self.bus.publish(LifecycleEvent(phase="starting"))
        self.bus.publish(LifecycleEvent(phase="ready"))

    def stop(self) -> None:
        """Queue stop lifecycle events and mark the shell as stopped."""

        self.bus.publish(LifecycleEvent(phase="stopping"))
        self.running = False
        self.bus.publish(LifecycleEvent(phase="stopped"))

    def tick(self) -> int:
        """Advance queued main-thread work once."""

        processed = self.scheduler.drain()
        processed += self.bus.drain()
        if self._ui_tick_callback is not None:
            self._ui_tick_callback()
        return processed

    def run(self, *, sleep_seconds: float = 0.01, max_iterations: int | None = None) -> int:
        """Run the scaffold main loop until stopped or iteration-limited."""

        iterations = 0
        total_processed = 0
        if not self.running:
            self.start()

        while self.running:
            total_processed += self.tick()
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
            time.sleep(sleep_seconds)

        return total_processed
