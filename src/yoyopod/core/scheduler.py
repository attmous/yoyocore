"""Main-thread task scheduler for the Phase A spine scaffold."""

from __future__ import annotations

import threading
from queue import Empty, Queue
from typing import Callable


class MainThreadScheduler:
    """Queue work onto the main thread without going through the event bus."""

    def __init__(self, main_thread_id: int | None = None) -> None:
        self.main_thread_id = main_thread_id or threading.get_ident()
        self._queue: Queue[Callable[[], None]] = Queue()

    def run_on_main(self, fn: Callable[[], None]) -> None:
        """Schedule one callback for the main thread, or run it immediately."""

        if threading.get_ident() == self.main_thread_id:
            fn()
            return
        self.post(fn)

    def post(self, fn: Callable[[], None]) -> None:
        """Queue one callback for the main thread to run on a later drain."""

        self._queue.put(fn)

    def drain(self, limit: int | None = None) -> int:
        """Run queued callbacks in FIFO order."""

        processed = 0
        while limit is None or processed < limit:
            try:
                fn = self._queue.get_nowait()
            except Empty:
                break
            fn()
            processed += 1
        return processed

    def pending_count(self) -> int:
        """Return the number of queued callbacks."""

        return self._queue.qsize()
