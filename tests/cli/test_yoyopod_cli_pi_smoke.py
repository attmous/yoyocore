"""Tests for the legacy `yoyopod.cli.pi.smoke` command surface."""

from __future__ import annotations


def test_legacy_smoke_command_imports() -> None:
    """The legacy smoke command package should stay importable."""

    from yoyopod.cli.pi.smoke.command import smoke_app

    assert smoke_app is not None
