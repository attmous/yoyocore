"""Tests for music data models."""

from __future__ import annotations

import sys
from pathlib import Path

from yoyopy.audio.music.models import MusicConfig, Playlist, Track


def test_track_get_artist_string_with_artists() -> None:
    track = Track(uri="/music/song.mp3", name="Song", artists=["Alice", "Bob"])
    assert track.get_artist_string() == "Alice, Bob"


def test_track_get_artist_string_empty() -> None:
    track = Track(uri="/music/song.mp3", name="Song", artists=[])
    assert track.get_artist_string() == "Unknown Artist"


def test_track_from_mpv_metadata_basic() -> None:
    track = Track.from_mpv_metadata(
        "/music/song.mp3",
        {"title": "My Song", "artist": "Alice", "album": "Debut", "duration": 180.5},
    )
    assert track.name == "My Song"
    assert track.artists == ["Alice"]
    assert track.album == "Debut"
    assert track.length == 180500
    assert track.uri == "/music/song.mp3"


def test_track_from_mpv_metadata_missing_fields() -> None:
    track = Track.from_mpv_metadata("/music/unknown.mp3", {})
    assert track.name == "unknown"
    assert track.artists == ["Unknown"]
    assert track.album == ""
    assert track.length == 0


def test_track_from_file_tags(tmp_path: Path) -> None:
    # Create a minimal test - from_file_tags falls back to filename when tinytag fails
    fake_file = tmp_path / "test_song.mp3"
    fake_file.write_bytes(b"\x00" * 100)
    track = Track.from_file_tags(fake_file)
    assert track.uri == str(fake_file)
    assert track.name == "test_song"


def test_playlist_dataclass() -> None:
    pl = Playlist(uri="/music/chill.m3u", name="chill", track_count=5)
    assert pl.name == "chill"
    assert pl.track_count == 5


def test_music_config_defaults() -> None:
    cfg = MusicConfig(music_dir=Path("/home/pi/Music"))
    expected_socket = r"\\.\pipe\yoyopod-mpv" if sys.platform == "win32" else "/tmp/yoyopod-mpv.sock"
    assert cfg.mpv_socket == expected_socket
    assert cfg.mpv_binary == "mpv"
    assert cfg.alsa_device == "default"
