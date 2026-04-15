"""VoIP screens for YoyoPod."""

from yoyopod.ui.screens.voip.quick_call import CallScreen
from yoyopod.ui.screens.voip.call_history import CallHistoryScreen
from yoyopod.ui.screens.voip.incoming_call import IncomingCallScreen
from yoyopod.ui.screens.voip.outgoing_call import OutgoingCallScreen
from yoyopod.ui.screens.voip.in_call import InCallScreen
from yoyopod.ui.screens.voip.contact_list import ContactListScreen
from yoyopod.ui.screens.voip.talk_contact import TalkContactScreen
from yoyopod.ui.screens.voip.voice_note import VoiceNoteScreen

__all__ = [
    'CallScreen',
    'CallHistoryScreen',
    'IncomingCallScreen',
    'OutgoingCallScreen',
    'InCallScreen',
    'ContactListScreen',
    'TalkContactScreen',
    'VoiceNoteScreen',
]
