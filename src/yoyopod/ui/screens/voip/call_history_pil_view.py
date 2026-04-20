"""PIL fallback view for the call history screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yoyopod.ui.screens.theme import (
    draw_empty_state,
    draw_list_item,
    render_footer,
    render_header,
    text_fit,
)

if TYPE_CHECKING:
    from yoyopod.ui.screens.voip.call_history import CallHistoryScreen


def render_call_history_pil(screen: "CallHistoryScreen") -> None:
    """Render the recent-calls list through the PIL display path."""

    content_top = render_header(
        screen.display,
        screen.context,
        mode="talk",
        title="Recents",
        page_text=None,
        show_time=False,
        show_mode_chip=False,
    )

    if not screen.entries:
        draw_empty_state(
            screen.display,
            mode="talk",
            title="No recent calls",
            subtitle="Calls will show up here after the first one.",
            icon="talk",
            top=content_top,
        )
        render_footer(screen.display, "Hold back", mode="talk")
        screen.display.update()
        return

    visible_titles, _visible_badges, selected_visible_index = screen.get_visible_window()
    visible_subtitles = screen.get_visible_subtitles()
    visible_icon_keys = screen.get_visible_icon_keys()

    item_height = 52
    list_top = content_top + 8
    for row, entry_title in enumerate(visible_titles):
        y1 = list_top + (row * item_height)
        y2 = y1 + 44
        draw_list_item(
            screen.display,
            x1=18,
            y1=y1,
            x2=screen.display.WIDTH - 18,
            y2=y2,
            title=text_fit(screen.display, entry_title, screen.display.WIDTH - 90, 15),
            subtitle=visible_subtitles[row] if row < len(visible_subtitles) else "",
            mode="talk",
            selected=row == selected_visible_index,
            badge=None,
            icon=visible_icon_keys[row] if row < len(visible_icon_keys) else "talk",
        )

    render_footer(screen.display, screen.instruction_text(), mode="talk")
    screen.display.update()
