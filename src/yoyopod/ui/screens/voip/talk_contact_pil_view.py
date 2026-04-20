"""PIL fallback view for the Talk contact action screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yoyopod.ui.screens.theme import (
    INK,
    TALK,
    draw_talk_action_button,
    draw_talk_page_dots,
    draw_talk_person_header,
    render_footer,
    render_status_bar,
)

if TYPE_CHECKING:
    from yoyopod.ui.screens.voip.talk_contact import TalkContactScreen


def render_talk_contact_pil(screen: "TalkContactScreen") -> None:
    """Render the Talk contact action picker through the PIL display path."""

    render_status_bar(screen.display, screen.context, show_time=True)
    actions = screen.actions()
    action_icons = screen.get_visible_action_icons()
    button_size = screen.action_button_size()
    selected_index = min(screen.selected_index, len(actions) - 1) if actions else 0
    bottom = draw_talk_person_header(
        screen.display,
        center_x=screen.display.WIDTH // 2,
        top=screen.display.STATUS_BAR_HEIGHT + 28,
        name=screen.current_contact_name(),
        label=screen.current_contact_monogram(),
    )

    diameter = 64 if button_size == "medium" else 56
    gap = 16 if button_size == "medium" else 12
    center_y = bottom + 54
    row_width = (len(actions) * diameter) + (max(0, len(actions) - 1) * gap)
    start_center = ((screen.display.WIDTH - row_width) // 2) + (diameter // 2)

    for row, _action in enumerate(actions):
        draw_talk_action_button(
            screen.display,
            center_x=start_center + (row * (diameter + gap)),
            center_y=center_y,
            button_size=button_size,
            color=TALK.accent,
            icon=action_icons[row],
            filled=row == selected_index,
            active=row == selected_index,
        )

    visible_items, _visible_subtitles, selected_visible_index = screen.get_visible_actions()
    if visible_items:
        selected_visible_index = min(selected_visible_index, len(visible_items) - 1)
        selected_title = visible_items[selected_visible_index]
    else:
        selected_title = ""
    title_width, title_height = screen.display.get_text_size(selected_title, 18)
    title_y = center_y + (diameter // 2) + 16
    screen.display.text(
        selected_title,
        (screen.display.WIDTH - title_width) // 2,
        title_y,
        color=INK,
        font_size=18,
    )
    draw_talk_page_dots(
        screen.display,
        center_x=screen.display.WIDTH // 2,
        top=title_y + title_height + 16,
        total=len(actions),
        current=selected_index,
        color=TALK.accent,
    )

    render_footer(screen.display, screen.footer_text(), mode="talk")
    screen.display.update()
