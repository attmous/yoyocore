"""Backend-specific screen view lifecycle protocol."""

from __future__ import annotations

from typing import Protocol


class ScreenView(Protocol):
    """Lifecycle shared by backend-specific screen view implementations."""

    def build(self) -> None:
        """Create widget/object state once when a screen becomes active."""

    def sync(self) -> None:
        """Update an already-built view from the current controller state."""

    def destroy(self) -> None:
        """Tear down widgets, callbacks, and timers when leaving the screen."""
