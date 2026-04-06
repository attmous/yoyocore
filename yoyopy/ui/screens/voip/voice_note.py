"""Voice-note flow screen for the Talk experience."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from yoyopy.ui.display import Display
from yoyopy.ui.screens.base import Screen
from yoyopy.ui.screens.theme import TALK, INK, draw_icon, render_footer, render_status_bar, rounded_panel, wrap_text
from yoyopy.ui.screens.voip.lvgl.voice_note_view import LvglVoiceNoteView

if TYPE_CHECKING:
    from yoyopy.app_context import AppContext
    from yoyopy.ui.screens import ScreenView


class VoiceNoteScreen(Screen):
    """Simple kid-facing voice-note flow with record and review states."""

    def __init__(self, display: Display, context: Optional["AppContext"] = None) -> None:
        super().__init__(display, context, "VoiceNote")
        self._state = "ready"
        self._review_index = 0
        self._lvgl_view: "ScreenView | None" = None

    def enter(self) -> None:
        """Reset the voice-note flow when opened."""

        super().enter()
        self._state = "ready"
        self._review_index = 0
        self._ensure_lvgl_view()

    def exit(self) -> None:
        """Tear down any active LVGL view when leaving voice notes."""

        if self._lvgl_view is not None:
            self._lvgl_view.destroy()
            self._lvgl_view = None
        super().exit()

    def _ensure_lvgl_view(self) -> "ScreenView | None":
        if self._lvgl_view is not None:
            return self._lvgl_view

        if getattr(self.display, "backend_kind", "pil") != "lvgl":
            return None

        ui_backend = self.display.get_ui_backend() if hasattr(self.display, "get_ui_backend") else None
        if ui_backend is None or not getattr(ui_backend, "initialized", False):
            return None

        self._lvgl_view = LvglVoiceNoteView(self, ui_backend)
        self._lvgl_view.build()
        return self._lvgl_view

    def recipient_name(self) -> str:
        """Return the selected recipient."""

        if self.context is None:
            return "Friend"
        return self.context.voice_note_recipient_name or self.context.talk_contact_name or "Friend"

    def current_view_model(self) -> tuple[str, str, str, str]:
        """Return title, subtitle, footer, and icon for the current voice-note state."""

        recipient = self.recipient_name()
        if self._state == "recording":
            return (
                "Recording",
                f"Making a note for {recipient}.",
                "Double stop / Hold back" if self.is_one_button_mode() else "A stop | B back",
                "voice_note",
            )
        if self._state == "review":
            action_label = "Send" if self._review_index == 0 else "Again"
            return (
                action_label,
                f"Choose what to do with {recipient}'s note.",
                "Tap next / Double choose" if self.is_one_button_mode() else "A choose | B back",
                "voice_note",
            )
        if self._state == "queued":
            return (
                "Queued",
                f"Your note for {recipient} is ready.",
                "Hold back" if self.is_one_button_mode() else "B back",
                "voice_note",
            )
        return (
            "Voice Note",
            f"Record something for {recipient}.",
            "Double record / Hold back" if self.is_one_button_mode() else "A record | B back",
            "voice_note",
        )

    def render(self) -> None:
        """Render the current voice-note flow state."""

        lvgl_view = self._ensure_lvgl_view()
        if lvgl_view is not None:
            lvgl_view.sync()
            return

        title_text, subtitle_text, footer_text, icon_key = self.current_view_model()
        render_status_bar(self.display, self.context, show_time=False)

        panel_top = self.display.STATUS_BAR_HEIGHT + 18
        panel_bottom = self.display.HEIGHT - 28
        rounded_panel(
            self.display,
            16,
            panel_top,
            self.display.WIDTH - 16,
            panel_bottom,
            fill=(31, 34, 40),
            outline=TALK.accent_dim,
            radius=24,
            shadow=True,
        )

        draw_icon(self.display, icon_key, (self.display.WIDTH // 2) - 24, panel_top + 18, 48, TALK.accent)

        headline_width, headline_height = self.display.get_text_size(title_text, 18)
        self.display.text(
            title_text,
            (self.display.WIDTH - headline_width) // 2,
            panel_top + 78,
            color=TALK.accent,
            font_size=18,
        )

        copy_lines = wrap_text(
            self.display,
            subtitle_text,
            self.display.WIDTH - 52,
            12,
            max_lines=2,
        )
        line_y = panel_top + 108
        for line in copy_lines:
            line_width, _ = self.display.get_text_size(line, 12)
            self.display.text(line, (self.display.WIDTH - line_width) // 2, line_y, color=INK, font_size=12)
            line_y += 15

        render_footer(self.display, footer_text, mode="talk")
        self.display.update()

    def on_select(self, data=None) -> None:
        """Advance the voice-note flow."""

        if self._state == "ready":
            self._state = "recording"
            return
        if self._state == "recording":
            self._state = "review"
            self._review_index = 0
            return
        if self._state == "review":
            if self._review_index == 0:
                self._state = "queued"
                return
            self._state = "recording"
            return
        self.request_route("back")

    def on_advance(self, data=None) -> None:
        """Cycle review actions in one-button mode."""

        if self._state != "review":
            return
        self._review_index = (self._review_index + 1) % 2

    def on_back(self, data=None) -> None:
        """Return to the previous Talk screen."""

        self.request_route("back")
