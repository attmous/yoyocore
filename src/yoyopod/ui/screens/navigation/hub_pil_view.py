"""PIL fallback view for the root Hub screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yoyopod.ui.screens.theme import (
    BACKGROUND,
    FOOTER_BAR,
    INK,
    MUTED_DIM,
    draw_icon,
    mix,
    render_backdrop,
    render_status_bar,
    rounded_panel,
)

if TYPE_CHECKING:
    from yoyopod.ui.screens.navigation.hub import HubScreen


def render_hub_pil(screen: "HubScreen") -> None:
    """Render the selected Hub card through the PIL display path."""

    cards = screen.cards()
    screen.selected_index %= len(cards)
    selected_card = cards[screen.selected_index]
    render_backdrop(screen.display, selected_card.mode)
    render_status_bar(screen.display, screen.context, show_time=True)

    tile_size = 96
    tile_left = (screen.display.WIDTH - tile_size) // 2
    tile_top = screen.display.STATUS_BAR_HEIGHT + 30
    glow_padding = 10

    rounded_panel(
        screen.display,
        tile_left - glow_padding,
        tile_top - glow_padding,
        tile_left + tile_size + glow_padding,
        tile_top + tile_size + glow_padding,
        fill=screen.tile_glow_color(selected_card.mode),
        outline=None,
        radius=24,
        shadow=False,
    )

    rounded_panel(
        screen.display,
        tile_left,
        tile_top,
        tile_left + tile_size,
        tile_top + tile_size,
        fill=screen.tile_fill_color(selected_card.mode),
        outline=None,
        radius=16,
        shadow=True,
    )

    draw_icon(
        screen.display,
        selected_card.icon,
        tile_left + 20,
        tile_top + 20,
        56,
        INK,
    )

    title_y = tile_top + tile_size + 24
    title_text = selected_card.title
    title_width, title_height = screen.display.get_text_size(title_text, 22)
    screen.display.text(
        title_text,
        (screen.display.WIDTH - title_width) // 2,
        title_y,
        color=INK,
        font_size=22,
    )

    dots_y = title_y + title_height + 30
    dot_gap = 10
    dots_width = ((len(cards) - 1) * dot_gap) + 4
    dots_x = (screen.display.WIDTH - dots_width) // 2
    inactive_dot = mix(INK, BACKGROUND, 0.8)
    for index in range(len(cards)):
        dot_color = INK if index == screen.selected_index else inactive_dot
        screen.display.circle(dots_x + (index * dot_gap), dots_y, 2, fill=dot_color)

    footer_top = screen.display.HEIGHT - 32
    screen.display.rectangle(
        0, footer_top, screen.display.WIDTH, screen.display.HEIGHT, fill=FOOTER_BAR
    )
    footer_text = "Tap = Next / 2x = Open / Hold = Ask"
    footer_width, footer_height = screen.display.get_text_size(footer_text, 10)
    screen.display.text(
        footer_text,
        (screen.display.WIDTH - footer_width) // 2,
        footer_top + ((32 - footer_height) // 2) - 1,
        color=MUTED_DIM,
        font_size=10,
    )
    screen.display.update()
