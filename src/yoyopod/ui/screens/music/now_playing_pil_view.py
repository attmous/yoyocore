"""PIL fallback view for the now-playing screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yoyopod.ui.screens.theme import (
    BACKGROUND,
    INK,
    MUTED,
    SURFACE_RAISED,
    draw_icon,
    mix,
    render_backdrop,
    render_footer,
    render_status_bar,
    rounded_panel,
    text_fit,
    wrap_text,
)

if TYPE_CHECKING:
    from yoyopod.ui.screens.music.now_playing import NowPlayingScreen


def render_now_playing_pil(screen: "NowPlayingScreen") -> None:
    """Render the now-playing screen through the PIL display path."""

    state = screen.current_state()
    state_text = screen.display_state_text(state.state_label)
    footer = screen.get_footer_text(is_playing=state.is_playing, state_label=state.state_label)
    visuals = screen.state_visuals(state.state_label)

    render_backdrop(screen.display, "listen")
    render_status_bar(screen.display, screen.context, show_time=True)

    halo_width = 92
    halo_height = 66
    halo_left = (screen.display.WIDTH - halo_width) // 2
    halo_top = screen.display.STATUS_BAR_HEIGHT + 16
    rounded_panel(
        screen.display,
        halo_left,
        halo_top,
        halo_left + halo_width,
        halo_top + halo_height,
        fill=visuals["icon_fill"],
        outline=visuals["icon_outline"],
        radius=20,
    )
    draw_icon(
        screen.display,
        "music_note",
        halo_left + 24,
        halo_top + 13,
        42,
        visuals["icon_color"],
    )

    title_y = halo_top + halo_height + 18
    title_lines = wrap_text(
        screen.display,
        state.title,
        screen.display.WIDTH - 32,
        18,
        max_lines=2,
    ) or [text_fit(screen.display, state.title, screen.display.WIDTH - 32, 18)]
    title_line_height = screen.display.get_text_size("Ag", 18)[1]
    for index, line in enumerate(title_lines):
        title_width, _ = screen.display.get_text_size(line, 18)
        screen.display.text(
            line,
            (screen.display.WIDTH - title_width) // 2,
            title_y + (index * title_line_height),
            color=INK,
            font_size=18,
        )

    title_bottom = title_y + (len(title_lines) * title_line_height)
    artist_y = title_bottom + 8
    artist_text = text_fit(screen.display, state.artist, screen.display.WIDTH - 36, 11)
    artist_width, _ = screen.display.get_text_size(artist_text, 11)
    screen.display.text(
        artist_text,
        (screen.display.WIDTH - artist_width) // 2,
        artist_y,
        color=MUTED,
        font_size=11,
    )

    state_width, state_height = screen.display.get_text_size(state_text, 10)
    chip_width = state_width + 26
    chip_left = (screen.display.WIDTH - chip_width) // 2
    chip_top = artist_y + 22
    rounded_panel(
        screen.display,
        chip_left,
        chip_top,
        chip_left + chip_width,
        chip_top + state_height + 10,
        fill=visuals["chip_fill"],
        outline=None,
        radius=12,
    )
    screen.display.text(
        state_text,
        (screen.display.WIDTH - state_width) // 2,
        chip_top + 4,
        color=visuals["chip_text"],
        font_size=10,
    )

    progress_width = 168
    progress_x = (screen.display.WIDTH - progress_width) // 2
    progress_y = min(screen.display.HEIGHT - 52, chip_top + state_height + 18)
    screen.display.rectangle(
        progress_x,
        progress_y,
        progress_x + progress_width,
        progress_y + 8,
        fill=mix(BACKGROUND, SURFACE_RAISED, 0.5),
    )
    fill_width = max(0, min(progress_width, int(progress_width * state.progress)))
    if fill_width > 0:
        screen.display.rectangle(
            progress_x,
            progress_y,
            progress_x + fill_width,
            progress_y + 8,
            fill=visuals["progress_fill"],
        )

    render_footer(screen.display, footer, mode="listen")
    screen.display.update()
