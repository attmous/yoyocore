"""PIL fallback view for the voice-note flow screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yoyopod.ui.screens.theme import (
    INK,
    draw_talk_action_button,
    draw_talk_page_dots,
    draw_talk_person_header,
    draw_talk_status_chip,
    render_footer,
    render_status_bar,
)

if TYPE_CHECKING:
    from yoyopod.ui.screens.voip.voice_note import VoiceNoteScreen


def render_voice_note_pil(screen: "VoiceNoteScreen") -> None:
    """Render the voice-note flow through the PIL display path."""

    view_model = screen.view_model()
    _title_text, _subtitle_text, footer_text, _icon_key = view_model.current_view_model()
    render_status_bar(screen.display, screen.context, show_time=True)
    bottom = draw_talk_person_header(
        screen.display,
        center_x=screen.display.WIDTH // 2,
        top=screen.display.STATUS_BAR_HEIGHT + 26,
        name=screen.recipient_name(),
        label=screen.recipient_monogram(),
    )

    items, _badges, selected_index = view_model.current_actions_for_view()
    if items:
        icons = view_model.current_action_icons()
        colors = view_model.current_action_colors()
        diameter = 56
        gap = 12
        center_y = bottom + 52
        row_width = (len(items) * diameter) + (max(0, len(items) - 1) * gap)
        start_center = ((screen.display.WIDTH - row_width) // 2) + (diameter // 2)
        for row, _item_title in enumerate(items):
            draw_talk_action_button(
                screen.display,
                center_x=start_center + (row * (diameter + gap)),
                center_y=center_y,
                button_size="small",
                color=colors[row],
                icon=icons[row],
                filled=row == selected_index,
                active=row == selected_index,
            )

        label = items[selected_index]
        label_width, label_height = screen.display.get_text_size(label, 16)
        label_y = center_y + (diameter // 2) + 14
        screen.display.text(
            label,
            (screen.display.WIDTH - label_width) // 2,
            label_y,
            color=INK,
            font_size=16,
        )
        draw_talk_page_dots(
            screen.display,
            center_x=screen.display.WIDTH // 2,
            top=label_y + label_height + 14,
            total=len(items),
            current=selected_index,
            color=screen.page_dot_color(),
        )
    else:
        center_y = bottom + 64
        draw_talk_action_button(
            screen.display,
            center_x=screen.display.WIDTH // 2,
            center_y=center_y,
            button_size="large",
            color=view_model.current_primary_color(),
            icon=view_model.current_primary_icon(),
            filled=False,
            active=True,
        )
        status_text, status_color = view_model.current_primary_status()
        draw_talk_status_chip(
            screen.display,
            center_x=screen.display.WIDTH // 2,
            top=center_y + 54,
            text=status_text,
            color=status_color,
        )

    render_footer(screen.display, footer_text, mode="talk")
    screen.display.update()
