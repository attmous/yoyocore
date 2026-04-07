#!/usr/bin/env python3
"""Build the native Liblinphone shim for the current platform."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def build(native_dir: Path, build_dir: Path) -> None:
    build_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "cmake",
            "-S",
            str(native_dir),
            "-B",
            str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release",
        ]
    )
    run(["cmake", "--build", str(build_dir), "--parallel", "2"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    repo_root = Path(__file__).resolve().parents[1]
    native_dir = repo_root / "yoyopy" / "voip" / "liblinphone_binding" / "native"
    default_build = native_dir / "build"
    parser.add_argument("--build-dir", type=Path, default=default_build)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    native_dir = repo_root / "yoyopy" / "voip" / "liblinphone_binding" / "native"
    build(native_dir, args.build_dir)
    print(f"Built Liblinphone shim in {args.build_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
