"""Contact action screen for the kids-first Talk flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from loguru import logger

from yoyopy.ui.display import Display
from yoyopy.ui.screens.base import Screen
from yoyopy.ui.screens.theme import (
    INK,
    SURFACE,
    TALK,
    draw_icon,
    draw_list_item,
    render_footer,
    render_status_bar,
    rounded_panel,
    text_fit,
)
from yoyopy.ui.screens.voip.lvgl.talk_contact_view import LvglTalkContactView

if TYPE_CHECKING:
    from yoyopy.app_context import AppContext
    from yoyopy.ui.screens import ScreenView


@dataclass(frozen=True, slots=True)
class TalkAction:
    """One action shown on a selected contact."""

    kind: str
    title: str
    subtitle: str = ""


class TalkContactScreen(Screen):
    """Action picker for the currently selected Talk contact."""

    def __init__(
        self,
        display: Display,
        context: Optional["AppContext"] = None,
        voip_manager=None,
    ) -> None:
        super().__init__(display, context, "TalkContact")
        self.voip_manager = voip_manager
        self.selected_index = 0
        self._lvgl_view: "ScreenView | None" = None

    def enter(self) -> None:
        """Reset the action cursor and create the LVGL view when active."""

        super().enter()
        self.selected_index = 0
        self._ensure_lvgl_view()

    def exit(self) -> None:
        """Tear down any active LVGL view when leaving the action screen."""

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

        self._lvgl_view = LvglTalkContactView(self, ui_backend)
        self._lvgl_view.build()
        return self._lvgl_view

    def current_contact_name(self) -> str:
        """Return the child-facing selected contact name."""

        if self.context is None:
            return "Friend"
        return self.context.talk_contact_name or "Friend"

    def current_contact_address(self) -> str:
        """Return the selected contact SIP address."""

        if self.context is None:
            return ""
        return self.context.talk_contact_address

    def actions(self) -> list[TalkAction]:
        """Return the available actions for the selected contact."""

        return [
            TalkAction("call", "Call"),
            TalkAction("voice_note", "Voice Note"),
        ]

    def get_visible_actions(self) -> tuple[list[str], list[str], int]:
        """Return visible action rows for the LVGL playlist-style scene."""

        actions = self.actions()
        return [action.title for action in actions], [action.subtitle for action in actions], self.selected_index

    def render(self) -> None:
        """Render the contact action picker."""

        lvgl_view = self._ensure_lvgl_view()
        if lvgl_view is not None:
            lvgl_view.sync()
            return

        render_status_bar(self.display, self.context, show_time=False)

        panel_top = self.display.STATUS_BAR_HEIGHT + 18
        panel_bottom = self.display.HEIGHT - 28
        rounded_panel(
            self.display,
            12,
            panel_top,
            self.display.WIDTH - 12,
            panel_bottom,
            fill=SURFACE,
            outline=TALK.accent_dim,
            radius=24,
            shadow=True,
        )

        draw_icon(self.display, "talk", 24, panel_top + 12, 28, TALK.accent)
        contact_name = text_fit(self.display, self.current_contact_name(), self.display.WIDTH - 72, 21)
        self.display.text(contact_name, 60, panel_top + 16, color=INK, font_size=21)

        item_top = panel_top + 58
        for row, action in enumerate(self.actions()):
            y1 = item_top + (row * 48)
            y2 = y1 + 40
            draw_list_item(
                self.display,
                x1=20,
                y1=y1,
                x2=self.display.WIDTH - 20,
                y2=y2,
                title=action.title,
                subtitle="",
                mode="talk",
                selected=row == self.selected_index,
                badge=None,
            )

        render_footer(self.display, "Tap next / Double choose", mode="talk")
        self.display.update()

    def _selected_action(self) -> TalkAction:
        """Return the active action row."""

        actions = self.actions()
        return actions[self.selected_index % len(actions)]

    def _start_call(self) -> None:
        """Call the selected contact immediately."""

        contact_name = self.current_contact_name()
        sip_address = self.current_contact_address()
        if not sip_address:
            logger.warning("Cannot place Talk call without a selected address")
            return
        if self.voip_manager is None:
            logger.error("Cannot place Talk call: no VoIP manager")
            return
        if self.voip_manager.make_call(sip_address, contact_name=contact_name):
            self.request_route("call_started")
            return
        logger.error("Failed to place Talk call to {}", contact_name)

    def _open_voice_note(self) -> None:
        """Open the voice-note composer for the selected contact."""

        if self.context is not None:
            self.context.set_voice_note_recipient(
                name=self.current_contact_name(),
                sip_address=self.current_contact_address(),
            )
        self.request_route("voice_note")

    def on_select(self, data=None) -> None:
        """Trigger the selected contact action."""

        selected_action = self._selected_action()
        if selected_action.kind == "call":
            self._start_call()
            return
        self._open_voice_note()

    def on_back(self, data=None) -> None:
        """Return to the contact deck."""

        self.request_route("back")

    def on_advance(self, data=None) -> None:
        """Move to the next action."""

        self.selected_index = (self.selected_index + 1) % len(self.actions())
