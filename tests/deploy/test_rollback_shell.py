from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="bash script")

ROLLBACK_SH = Path(__file__).resolve().parents[2] / "deploy" / "scripts" / "rollback.sh"


def _make_layout(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    root = tmp_path / "yoyopod"
    releases = root / "releases"
    releases.mkdir(parents=True)
    v1 = releases / "v1"
    v2 = releases / "v2"
    v1.mkdir()
    v2.mkdir()
    current = root / "current"
    previous = root / "previous"
    current.symlink_to(v2)  # v2 is active, v1 was prior
    previous.symlink_to(v1)
    return root, current, previous, v1


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "YOYOPOD_ROOT": str(root), "YOYOPOD_SKIP_SYSTEMCTL": "1"}
    return subprocess.run(
        ["bash", str(ROLLBACK_SH)],
        env=env,
        capture_output=True,
        text=True,
    )


def test_rollback_swaps_current_and_previous(tmp_path: Path) -> None:
    root, current, previous, v1 = _make_layout(tmp_path)
    result = _run(root)
    assert result.returncode == 0, result.stderr
    assert current.resolve() == v1.resolve()
    assert previous.resolve() == (root / "releases" / "v2").resolve()


def test_rollback_fails_when_previous_missing(tmp_path: Path) -> None:
    root = tmp_path / "yoyopod"
    releases = root / "releases"
    releases.mkdir(parents=True)
    (releases / "v1").mkdir()
    (root / "current").symlink_to(releases / "v1")
    # no previous symlink
    result = _run(root)
    assert result.returncode != 0
    assert "previous" in result.stderr.lower()


def test_rollback_fails_when_current_is_not_symlink(tmp_path: Path) -> None:
    root = tmp_path / "yoyopod"
    root.mkdir()
    (root / "current").mkdir()  # real dir, not a symlink
    (root / "releases").mkdir()
    (root / "releases" / "v1").mkdir()
    (root / "previous").symlink_to(root / "releases" / "v1")
    result = _run(root)
    assert result.returncode != 0
