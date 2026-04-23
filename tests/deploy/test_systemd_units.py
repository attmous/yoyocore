from __future__ import annotations

import configparser
from pathlib import Path


UNITS_DIR = Path(__file__).resolve().parents[2] / "deploy" / "systemd"


def _parse(unit_name: str) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(strict=False, interpolation=None)
    parser.read(UNITS_DIR / unit_name)
    return parser


def test_slot_unit_references_launch_script() -> None:
    cfg = _parse("yoyopod-slot.service")
    assert cfg["Service"]["ExecStart"] == "/opt/yoyopod/current/bin/launch"


def test_slot_unit_has_onfailure_rollback() -> None:
    cfg = _parse("yoyopod-slot.service")
    assert cfg["Unit"]["OnFailure"] == "yoyopod-rollback.service"


def test_slot_unit_has_start_limit_burst() -> None:
    cfg = _parse("yoyopod-slot.service")
    assert cfg["Unit"]["StartLimitBurst"] == "3"
    assert cfg["Unit"]["StartLimitIntervalSec"] == "300"


def test_rollback_unit_calls_rollback_script() -> None:
    cfg = _parse("yoyopod-rollback.service")
    assert cfg["Service"]["ExecStart"] == "/opt/yoyopod/bin/rollback.sh"
    assert cfg["Service"]["Type"] == "oneshot"


def test_rollback_unit_has_its_own_start_limit() -> None:
    cfg = _parse("yoyopod-rollback.service")
    assert cfg["Unit"]["StartLimitBurst"] == "2"
