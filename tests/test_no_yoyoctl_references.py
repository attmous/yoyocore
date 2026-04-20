"""Regression guard: `yoyoctl` binary name must not appear anywhere except in
historical archive documentation (docs/archive/, docs/superpowers/ design/plan
files which describe the migration itself, and .git/)."""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# Paths that are allowed to keep historical `yoyoctl` mentions — these describe
# the migration itself and should not be scrubbed.
ALLOWED_PATHS = (
    "docs/archive/",
    "docs/superpowers/specs/",
    "docs/superpowers/plans/",
    ".github/",  # workflow history
)


def _path_is_allowed(rel_path: str) -> bool:
    return any(rel_path.replace("\\", "/").startswith(prefix) for prefix in ALLOWED_PATHS)


def test_no_yoyoctl_references_outside_historical_docs() -> None:
    result = subprocess.run(
        ["git", "grep", "-l", "yoyoctl"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    # git grep returns 1 (and empty stdout) when no matches; 0 when matches.
    if result.returncode not in (0, 1):
        raise AssertionError(f"git grep failed: {result.stderr}")

    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    unexpected = [f for f in files if not _path_is_allowed(f)]
    assert not unexpected, (
        "`yoyoctl` references found outside historical doc paths. "
        f"The binary was renamed to `yoyopod` — these must be updated.\nFiles: {unexpected}"
    )


def test_no_yoyoctl_references_in_runtime_code() -> None:
    """Runtime code must never reference `yoyoctl`. Stricter scope: src/ and yoyopod_cli/."""
    result = subprocess.run(
        ["git", "grep", "-l", "yoyoctl", "--", "src/", "yoyopod_cli/"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise AssertionError(f"git grep failed: {result.stderr}")

    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert not files, (
        "`yoyoctl` found in runtime code. The binary was renamed to `yoyopod`.\n"
        f"Files: {files}"
    )
