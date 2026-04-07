"""Data models for the music backend."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Track:
    """One music track."""

    uri: str
    name: str
    artists: list[str]
    album: str = ""
    length: int = 0  # milliseconds
    track_no: int | None = None

    def get_artist_string(self) -> str:
        """Get comma-separated artist names."""
        return ", ".join(self.artists) if self.artists else "Unknown Artist"

    @classmethod
    def from_mpv_metadata(cls, path: str, metadata: dict) -> Track:
        """Build from mpv's 'metadata' property dict at runtime."""
        raw_duration = metadata.get("duration", 0)
        duration_ms = int(float(raw_duration) * 1000) if raw_duration else 0
        name = metadata.get("title") or Path(path).stem
        artist = metadata.get("artist") or "Unknown"
        album = metadata.get("album", "")
        track_no_raw = metadata.get("track")
        track_no = int(track_no_raw) if track_no_raw is not None else None
        return cls(
            uri=path,
            name=name,
            artists=[artist] if isinstance(artist, str) else list(artist),
            album=album,
            length=duration_ms,
            track_no=track_no,
        )

    @classmethod
    def from_file_tags(cls, path: Path) -> Track:
        """Build from file metadata tags using tinytag. Falls back to filename."""
        try:
            from tinytag import TinyTag

            tag = TinyTag.get(str(path))
            return cls(
                uri=str(path),
                name=tag.title or path.stem,
                artists=[tag.artist] if tag.artist else ["Unknown"],
                album=tag.album or "",
                length=int((tag.duration or 0) * 1000),
                track_no=int(tag.track) if tag.track is not None else None,
            )
        except Exception:
            return cls(
                uri=str(path),
                name=path.stem,
                artists=["Unknown"],
            )


@dataclass(frozen=True, slots=True)
class Playlist:
    """One M3U playlist."""

    uri: str
    name: str
    track_count: int = 0


def _default_mpv_socket() -> str:
    """Return the platform-appropriate default mpv IPC path."""
    if sys.platform == "win32":
        return r"\\.\pipe\yoyopod-mpv"
    return "/tmp/yoyopod-mpv.sock"


@dataclass(slots=True)
class MusicConfig:
    """Configuration for the mpv music backend."""

    music_dir: Path = Path("/home/pi/Music")
    mpv_socket: str = ""
    mpv_binary: str = "mpv"
    alsa_device: str = "default"

    def __post_init__(self) -> None:
        if not self.mpv_socket:
            self.mpv_socket = _default_mpv_socket()
