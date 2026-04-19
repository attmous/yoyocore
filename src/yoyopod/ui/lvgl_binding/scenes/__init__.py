"""Scene-level LVGL binding mixins for per-screen UI operations."""

from __future__ import annotations

from .ask import AskSceneMixin
from .calls import CallsSceneMixin
from .hub import HubSceneMixin
from .listen import ListenSceneMixin
from .now_playing import NowPlayingSceneMixin
from .playlist import PlaylistSceneMixin
from .power import PowerSceneMixin
from .status_bar import StatusBarSceneMixin
from .talk import TalkSceneMixin

__all__ = [
    "AskSceneMixin",
    "CallsSceneMixin",
    "HubSceneMixin",
    "ListenSceneMixin",
    "NowPlayingSceneMixin",
    "PlaylistSceneMixin",
    "PowerSceneMixin",
    "StatusBarSceneMixin",
    "TalkSceneMixin",
]
