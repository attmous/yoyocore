"""Focused tests for scaffold location command dataclasses."""

from __future__ import annotations

from yoyopod.integrations.location.commands import (
    DisableGpsCommand,
    EnableGpsCommand,
    RequestFixCommand,
)


def test_request_fix_argless() -> None:
    assert RequestFixCommand() is not None


def test_enable_gps_argless() -> None:
    assert EnableGpsCommand() is not None


def test_disable_gps_argless() -> None:
    assert DisableGpsCommand() is not None
