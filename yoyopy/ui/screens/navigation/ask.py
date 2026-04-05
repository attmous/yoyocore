"""Future-safe Ask screen placeholder for the Graffiti Buddy redesign."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from yoyopy.ui.display import Display
from yoyopy.ui.screens.base import Screen
from yoyopy.ui.screens.navigation.lvgl import LvglAskView
from yoyopy.ui.screens.theme import ASK, INK, MUTED, draw_icon, render_footer, render_header, rounded_panel, wrap_text

if TYPE_CHECKING:
    from yoyopy.app_context import AppContext
    from yoyopy.ui.screens import ScreenView


class AskScreen(Screen):
    """Placeholder surface for the future safe-AI ask mode."""

    def __init__(self, display: Display, context: Optional["AppContext"] = None) -> None:
        super().__init__(display, context, "Ask")
        self._lvgl_view: "ScreenView | None" = None

    def enter(self) -> None:
        """Create the LVGL view when the screen becomes active."""
        super().enter()
        self._ensure_lvgl_view()

    def exit(self) -> None:
        """Tear down any active LVGL view when leaving Ask."""
        if self._lvgl_view is not None:
            self._lvgl_view.destroy()
            self._lvgl_view = None
        super().exit()

    def _ensure_lvgl_view(self) -> "ScreenView | None":
        """Create an LVGL view when the Whisplay renderer is active."""
        if self._lvgl_view is not None:
            return self._lvgl_view

        if getattr(self.display, "backend_kind", "pil") != "lvgl":
            return None

        ui_backend = self.display.get_ui_backend() if hasattr(self.display, "get_ui_backend") else None
        if ui_backend is None or not getattr(ui_backend, "initialized", False):
            return None

        self._lvgl_view = LvglAskView(self, ui_backend)
        self._lvgl_view.build()
        return self._lvgl_view

    def render(self) -> None:
        """Render the future Ask mode preview."""
        lvgl_view = self._ensure_lvgl_view()
        if lvgl_view is not None:
            lvgl_view.sync()
            return

        content_top = render_header(
            self.display,
            self.context,
            mode="ask",
            title="Ask",
            show_time=False,
            show_mode_chip=False,
        )

        panel_top = content_top + 8
        panel_bottom = self.display.HEIGHT - 28
        rounded_panel(
            self.display,
            16,
            panel_top,
            self.display.WIDTH - 16,
            panel_bottom,
            fill=(31, 34, 40),
            outline=ASK.accent_dim,
            radius=24,
        )

        draw_icon(self.display, "ask", (self.display.WIDTH // 2) - 24, panel_top + 18, 48, ASK.accent)

        headline = "Coming soon"
        headline_width, _ = self.display.get_text_size(headline, 18)
        self.display.text(headline, (self.display.WIDTH - headline_width) // 2, panel_top + 78, color=ASK.accent, font_size=18)

        copy_lines = wrap_text(
            self.display,
            "Safe questions will live here soon.",
            self.display.WIDTH - 52,
            12,
            max_lines=1,
        )
        line_y = panel_top + 108
        for line in copy_lines:
            line_width, _ = self.display.get_text_size(line, 12)
            self.display.text(line, (self.display.WIDTH - line_width) // 2, line_y, color=INK, font_size=12)
            line_y += 15

        help_text = "Hold back" if self.is_one_button_mode() else "B back"
        render_footer(self.display, help_text, mode="ask")
        self.display.update()

    def on_select(self, data=None) -> None:
        """Ask is intentionally passive until the future feature lands."""
        return

    def on_back(self, data=None) -> None:
        """Return to the previous screen."""
        self.request_route("back")
