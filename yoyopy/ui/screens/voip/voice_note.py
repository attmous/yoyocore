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
    from yoyopy.voip import VoIPManager


class VoiceNoteScreen(Screen):
    """Kid-facing voice-note flow with real record, review, and send states."""

    def __init__(
        self,
        display: Display,
        context: Optional["AppContext"] = None,
        voip_manager: Optional["VoIPManager"] = None,
    ) -> None:
        super().__init__(display, context, "VoiceNote")
        self.voip_manager = voip_manager
        self._state = "ready"
        self._review_index = 0
        self._lvgl_view: "ScreenView | None" = None

    def enter(self) -> None:
        """Reset the voice-note flow when opened."""

        super().enter()
        self._sync_state_from_manager(default_state="ready")
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

    def wants_ptt_passthrough(self) -> bool:
        """Return True when the single-button adapter should emit raw PTT hold events."""

        return self.is_one_button_mode() and self._state in {"ready", "recording"}

    def recipient_name(self) -> str:
        """Return the selected recipient."""

        if self.context is None:
            return "Friend"
        return self.context.voice_note_recipient_name or self.context.talk_contact_name or "Friend"

    def recipient_address(self) -> str:
        """Return the selected recipient SIP address."""

        if self.context is None:
            return ""
        return self.context.voice_note_recipient_address or self.context.talk_contact_address

    def _sync_state_from_manager(self, default_state: str = "ready") -> None:
        """Reflect the active voice-note draft from VoIPManager into the screen/context."""

        if self.voip_manager is None:
            self._state = default_state
            return

        draft = self.voip_manager.get_active_voice_note()
        if draft is None:
            self._state = default_state
            if self.context is not None:
                self.context.update_active_voice_note(send_state="idle")
            return

        self._state = draft.send_state or default_state
        if self.context is not None:
            self.context.update_active_voice_note(
                send_state=draft.send_state,
                status_text=draft.status_text,
                file_path=draft.file_path,
                duration_ms=draft.duration_ms,
            )

    def _refresh_input_mode(self) -> None:
        """Rebind active input handlers when the voice-note interaction mode changes."""

        if self.screen_manager is None:
            return
        rebind = getattr(self.screen_manager, "rebind_current_screen_inputs", None)
        if callable(rebind):
            rebind()

    def _duration_label(self) -> str:
        """Return a compact duration label for the active draft."""

        if self.context is None or self.context.voice_note_duration_ms <= 0:
            return ""
        seconds = max(1, round(self.context.voice_note_duration_ms / 1000))
        return f"{seconds}s"

    def current_view_model(self) -> tuple[str, str, str, str]:
        """Return title, subtitle, footer, and icon for the current voice-note state."""

        recipient = self.recipient_name()
        if self._state == "recording":
            return (
                "Recording",
                f"Release to stop for {recipient}.",
                "Release to stop" if self.is_one_button_mode() else "Select stop / Back cancel",
                "voice_note",
            )
        if self._state == "review":
            action_label = "Send" if self._review_index == 0 else "Again"
            return (
                action_label,
                f"Choose what to do with {recipient}'s note.",
                "Tap next / Double choose" if self.is_one_button_mode() else "Select choose / Back",
                "voice_note",
            )
        if self._state == "sending":
            return (
                "Sending",
                f"Sending your note to {recipient}.",
                "Please wait",
                "voice_note",
            )
        if self._state == "sent":
            return (
                "Sent",
                f"Your note reached {recipient}.",
                "Double back" if self.is_one_button_mode() else "Back",
                "voice_note",
            )
        if self._state == "failed":
            return (
                "Couldn't Send",
                self.context.voice_note_status_text or f"Try {recipient}'s note again.",
                "Double retry / Hold back" if self.is_one_button_mode() else "Select retry / Back",
                "voice_note",
            )
        return (
            "Voice Note",
            f"Hold to record for {recipient}.",
            "Hold record / Double back" if self.is_one_button_mode() else "Select record / Back",
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

        duration_label = self._duration_label()
        if duration_label:
            duration_width, _ = self.display.get_text_size(duration_label, 12)
            self.display.text(
                duration_label,
                (self.display.WIDTH - duration_width) // 2,
                line_y + 4,
                color=TALK.accent,
                font_size=12,
            )

        render_footer(self.display, footer_text, mode="talk")
        self.display.update()

    def on_select(self, data=None) -> None:
        """Advance the voice-note flow."""

        if self._state == "ready":
            if self.is_one_button_mode():
                self.request_route("back")
                return
            self._start_recording()
            return
        if self._state == "recording":
            self._stop_recording()
            return
        if self._state == "review":
            if self._review_index == 0:
                self._send_active_voice_note()
                return
            self._discard_and_reset()
            return
        if self._state == "failed":
            self._send_active_voice_note()
            return
        if self._state == "sent":
            self.request_route("back")
            return
        self.request_route("back")

    def on_advance(self, data=None) -> None:
        """Cycle review actions in one-button mode."""

        if self._state != "review":
            return
        self._review_index = (self._review_index + 1) % 2

    def on_back(self, data=None) -> None:
        """Return to the previous Talk screen."""

        if self._state == "recording":
            self._cancel_recording()
            return
        self.request_route("back")

    def on_ptt_press(self, data=None) -> None:
        """Start recording once the raw hold threshold is crossed."""

        if not isinstance(data, dict) or data.get("stage") != "hold_started":
            return
        if self._state != "ready":
            return
        self._start_recording()

    def on_ptt_release(self, data=None) -> None:
        """Stop an active recording when the button is released."""

        if self._state != "recording":
            return
        if not isinstance(data, dict) or not data.get("hold_started", False):
            self._cancel_recording()
            return
        self._stop_recording()

    def _start_recording(self) -> None:
        """Start a new voice-note recording for the active recipient."""

        if self.voip_manager is None:
            return
        if not self.voip_manager.start_voice_note_recording(
            self.recipient_address(),
            recipient_name=self.recipient_name(),
        ):
            self._state = "failed"
            if self.context is not None:
                self.context.update_active_voice_note(
                    send_state="failed",
                    status_text="Couldn't start recorder",
                )
            return
        self._sync_state_from_manager(default_state="recording")
        self._refresh_input_mode()

    def _stop_recording(self) -> None:
        """Stop the active recording and move to review."""

        if self.voip_manager is None:
            return
        draft = self.voip_manager.stop_voice_note_recording()
        if draft is None:
            self._state = "failed"
            if self.context is not None:
                self.context.update_active_voice_note(
                    send_state="failed",
                    status_text="Couldn't save note",
                )
        else:
            self._state = "review"
            self._review_index = 0
            self._sync_state_from_manager(default_state="review")
        self._refresh_input_mode()

    def _cancel_recording(self) -> None:
        """Cancel the active recording and return to the ready state."""

        if self.voip_manager is not None:
            self.voip_manager.cancel_voice_note_recording()
        self._state = "ready"
        if self.context is not None:
            self.context.update_active_voice_note(send_state="idle")
        self._refresh_input_mode()

    def _discard_and_reset(self) -> None:
        """Discard the current draft and return to the ready state."""

        if self.voip_manager is not None:
            self.voip_manager.discard_active_voice_note()
        self._state = "ready"
        self._review_index = 0
        if self.context is not None:
            self.context.update_active_voice_note(send_state="idle")
        self._refresh_input_mode()

    def _send_active_voice_note(self) -> None:
        """Send the recorded voice note through the VoIP manager."""

        if self.voip_manager is None:
            return
        if self.voip_manager.send_active_voice_note():
            self._sync_state_from_manager(default_state="sending")
            self._state = "sending"
            return
        self._sync_state_from_manager(default_state="failed")
        self._state = "failed"
