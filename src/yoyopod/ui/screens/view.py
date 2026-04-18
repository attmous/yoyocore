"""Backend-specific screen view lifecycle protocol."""

from __future__ import annotations

from typing import Protocol


class ScreenView(Protocol):
    """Lifecycle shared by backend-specific screen view implementations."""

    def build(self) -> None:
        """Create widget/object state once for a retained backend view."""

    def sync(self) -> None:
        """Update and present an already-built view from controller state."""

    def destroy(self) -> None:
        """Tear down widgets only when the retained view is permanently released."""
