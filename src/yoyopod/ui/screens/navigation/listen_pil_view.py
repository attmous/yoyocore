"""PIL fallback view for the Listen landing screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yoyopod.ui.screens.theme import (
    draw_list_item,
    render_footer,
    render_header,
)

if TYPE_CHECKING:
    from yoyopod.ui.screens.navigation.listen import ListenScreen


def render_listen_pil(screen: "ListenScreen") -> None:
    """Render the local library menu through the PIL display path."""

    content_top = render_header(
        screen.display,
        screen.context,
        mode="listen",
        title="Your Music",
        subtitle="Local library",
        show_time=False,
        show_mode_chip=False,
    )

    list_top = content_top + 8
    item_height = 76
    for index, item in enumerate(screen.items):
        y1 = list_top + (index * item_height)
        y2 = y1 + 68
        if y2 > screen.display.HEIGHT - 38:
            break

        draw_list_item(
            screen.display,
            x1=18,
            y1=y1,
            x2=screen.display.WIDTH - 18,
            y2=y2,
            title=item.title,
            subtitle=item.subtitle,
            mode="listen",
            selected=index == screen.selected_index,
            icon=screen.item_icon_key(item.key),
        )

    help_text = (
        "Tap = Next / 2x Tap = Open / Hold = Back"
        if screen.is_one_button_mode()
        else "A open | B back | X/Y move"
    )
    render_footer(screen.display, help_text, mode="listen")
    screen.display.update()
