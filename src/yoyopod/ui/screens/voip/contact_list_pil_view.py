"""PIL fallback view for the contact list screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yoyopod.ui.screens.theme import (
    draw_empty_state,
    draw_list_item,
    render_footer,
    render_header,
    talk_monogram,
    text_fit,
)

if TYPE_CHECKING:
    from yoyopod.ui.screens.voip.contact_list import ContactListScreen


def render_contact_list_pil(screen: "ContactListScreen") -> None:
    """Render the contact list through the PIL display path."""

    content_top = render_header(
        screen.display,
        screen.context,
        mode="talk",
        title=screen.title_text,
        page_text=None,
        show_time=False,
        show_mode_chip=False,
    )

    if not screen.contacts:
        draw_empty_state(
            screen.display,
            mode="talk",
            title=screen.empty_title,
            subtitle=screen.empty_subtitle,
            icon="talk",
            top=content_top,
        )
        render_footer(screen.display, "Hold back", mode="talk")
        screen.display.update()
        return

    if screen.selected_index < screen.scroll_offset:
        screen.scroll_offset = screen.selected_index
    elif screen.selected_index >= screen.scroll_offset + screen.max_visible_items:
        screen.scroll_offset = screen.selected_index - screen.max_visible_items + 1

    item_height = 52
    list_top = content_top + 8
    for row in range(screen.max_visible_items):
        contact_index = screen.scroll_offset + row
        if contact_index >= len(screen.contacts):
            break

        contact = screen.contacts[contact_index]
        y1 = list_top + (row * item_height)
        y2 = y1 + 44
        draw_list_item(
            screen.display,
            x1=18,
            y1=y1,
            x2=screen.display.WIDTH - 18,
            y2=y2,
            title=text_fit(screen.display, contact.display_name, screen.display.WIDTH - 90, 15),
            subtitle="",
            mode="talk",
            selected=contact_index == screen.selected_index,
            badge=None,
            icon=f"mono:{talk_monogram(contact.display_name)}",
        )

    render_footer(screen.display, screen._instruction_text(), mode="talk")
    screen.display.update()
