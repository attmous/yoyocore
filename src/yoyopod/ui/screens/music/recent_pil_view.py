"""PIL fallback view for the recent tracks browser screen."""

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
    from yoyopod.ui.screens.music.recent import RecentTracksScreen


def render_recent_tracks_pil(screen: "RecentTracksScreen") -> None:
    """Render the recent-tracks browser through the PIL display path."""

    content_top = render_header(
        screen.display,
        screen.context,
        mode="listen",
        title="Recent",
        show_time=False,
        show_mode_chip=False,
    )

    if screen.error_message:
        draw_empty_state(
            screen.display,
            mode="listen",
            title="Music hiccup",
            subtitle=screen.error_message,
            icon="playlist",
            top=content_top,
        )
        render_footer(screen.display, "Hold back", mode="listen")
        screen.display.update()
        return

    if not screen.tracks:
        draw_empty_state(
            screen.display,
            mode="listen",
            title="No recent tracks",
            subtitle="Play local music to fill this list.",
            icon="playlist",
            top=content_top,
        )
        render_footer(screen.display, "Hold back", mode="listen")
        screen.display.update()
        return

    screen._update_scroll_window()

    item_height = 52
    list_top = content_top + 8
    for row in range(screen.max_visible_items):
        track_index = screen.scroll_offset + row
        if track_index >= len(screen.tracks):
            break

        track = screen.tracks[track_index]
        y1 = list_top + (row * item_height)
        y2 = y1 + 44
        draw_list_item(
            screen.display,
            x1=18,
            y1=y1,
            x2=screen.display.WIDTH - 18,
            y2=y2,
            title=text_fit(screen.display, track.title, screen.display.WIDTH - 48, 15),
            subtitle=text_fit(screen.display, track.subtitle, screen.display.WIDTH - 48, 11),
            mode="listen",
            selected=track_index == screen.selected_index,
            icon="music_note",
        )

    help_text = (
        f"{screen.get_footer_text()} / Hold back"
        if screen.is_one_button_mode()
        else screen.get_footer_text()
    )
    render_footer(screen.display, help_text, mode="listen")
    screen.display.update()
