"""PIL fallback view for the playlist browser screen."""

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
    from yoyopod.ui.screens.music.playlist import PlaylistScreen


def render_playlist_pil(screen: "PlaylistScreen") -> None:
    """Render the local playlist browser through the PIL display path."""

    content_top = render_header(
        screen.display,
        screen.context,
        mode="listen",
        title="Playlists",
        show_time=False,
        show_mode_chip=False,
    )

    if screen.loading:
        draw_empty_state(
            screen.display,
            mode="listen",
            title="Loading playlists",
            subtitle="Hold on while your mixes come in.",
            icon="playlist",
            top=content_top,
        )
        render_footer(screen.display, "Hold back", mode="listen")
        screen.display.update()
        return

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

    if not screen.playlists:
        draw_empty_state(
            screen.display,
            mode="listen",
            title="No playlists",
            subtitle="Add local playlists to see them here.",
            icon="playlist",
            top=content_top,
        )
        render_footer(screen.display, "Hold back", mode="listen")
        screen.display.update()
        return

    visible_titles, visible_badges, selected_visible_index = screen.get_visible_window()
    visible_subtitles = screen.get_visible_subtitles()
    visible_icon_keys = screen.get_visible_icon_keys()

    item_height = 52
    list_top = content_top + 8
    for row, playlist_title in enumerate(visible_titles):
        y1 = list_top + (row * item_height)
        y2 = y1 + 44
        draw_list_item(
            screen.display,
            x1=18,
            y1=y1,
            x2=screen.display.WIDTH - 18,
            y2=y2,
            title=text_fit(screen.display, playlist_title, screen.display.WIDTH - 92, 15),
            subtitle=visible_subtitles[row] if row < len(visible_subtitles) else "",
            mode="listen",
            selected=row == selected_visible_index,
            badge=visible_badges[row] or None,
            icon=visible_icon_keys[row] if row < len(visible_icon_keys) else "playlist",
        )

    help_text = (
        f"{screen.get_footer_text()} / Hold back"
        if screen.is_one_button_mode()
        else screen.get_footer_text()
    )
    render_footer(screen.display, help_text, mode="listen")
    screen.display.update()
