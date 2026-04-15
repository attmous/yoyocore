"""LVGL-backed VoIP screen views."""

from yoyopod.ui.screens.voip.lvgl.call_view import LvglCallView
from yoyopod.ui.screens.voip.lvgl.call_history_view import LvglCallHistoryView
from yoyopod.ui.screens.voip.lvgl.contact_list_view import LvglContactListView
from yoyopod.ui.screens.voip.lvgl.in_call_view import LvglInCallView
from yoyopod.ui.screens.voip.lvgl.incoming_call_view import LvglIncomingCallView
from yoyopod.ui.screens.voip.lvgl.outgoing_call_view import LvglOutgoingCallView
from yoyopod.ui.screens.voip.lvgl.talk_contact_view import LvglTalkContactView
from yoyopod.ui.screens.voip.lvgl.voice_note_view import LvglVoiceNoteView

__all__ = [
    "LvglCallView",
    "LvglCallHistoryView",
    "LvglContactListView",
    "LvglInCallView",
    "LvglIncomingCallView",
    "LvglOutgoingCallView",
    "LvglTalkContactView",
    "LvglVoiceNoteView",
]
