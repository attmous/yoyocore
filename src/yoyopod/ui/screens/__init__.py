"""
Screens module for YoyoPod UI.

Provides screen implementations organized by feature:
- base: Screen base class
- manager: ScreenManager for navigation
- navigation: Home, hub, and route-selection screens
- system: Device status and setup screens
- music: Now Playing and Playlist screens
- voip: Call-related screens
"""

# Base screen class
from yoyopod.ui.screens.base import Screen
from yoyopod.ui.screens.view import ScreenView

# Screen manager
from yoyopod.ui.screens.manager import ScreenManager
from yoyopod.ui.screens.router import NavigationRequest, ScreenRouter

# Navigation and system screens
from yoyopod.ui.screens.navigation import AskScreen, HubScreen, HomeScreen, ListenScreen, MenuScreen
from yoyopod.ui.screens.system import PowerScreen

# Music screens
from yoyopod.ui.screens.music import NowPlayingScreen, PlaylistScreen, RecentTracksScreen

# VoIP screens
from yoyopod.ui.screens.voip import (
    CallScreen,
    CallHistoryScreen,
    IncomingCallScreen,
    OutgoingCallScreen,
    InCallScreen,
    ContactListScreen,
    TalkContactScreen,
    VoiceNoteScreen,
)

__all__ = [
    # Base & Manager
    'Screen',
    'ScreenView',
    'ScreenManager',
    'NavigationRequest',
    'ScreenRouter',
    # Navigation
    'HubScreen',
    'HomeScreen',
    'ListenScreen',
    'MenuScreen',
    'AskScreen',
    'PowerScreen',
    # Music
    'NowPlayingScreen',
    'PlaylistScreen',
    'RecentTracksScreen',
    # VoIP
    'CallScreen',
    'CallHistoryScreen',
    'IncomingCallScreen',
    'OutgoingCallScreen',
    'InCallScreen',
    'ContactListScreen',
    'TalkContactScreen',
    'VoiceNoteScreen',
]
