#!/usr/bin/env python3
"""Top-level launcher and compatibility package shim for YoyoPod."""

from __future__ import annotations

import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent / "src"
PACKAGE_ROOT = SRC_ROOT / "yoyopod"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

__path__ = [str(PACKAGE_ROOT)]
__package__ = "yoyopod"

if __name__ != "__main__":
    init_path = PACKAGE_ROOT / "__init__.py"
    exec(compile(init_path.read_text(encoding="utf-8"), str(init_path), "exec"))


def _run() -> int:
    from yoyopod.main import main

    return main()


if __name__ == "__main__":
    sys.exit(_run())
