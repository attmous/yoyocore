#!/usr/bin/env python3
"""Run the standalone LVGL Whisplay proof scenes."""

from __future__ import annotations

import argparse
import time

from loguru import logger

from yoyopy.ui.display.adapters.whisplay import WhisplayDisplayAdapter
from yoyopy.ui.lvgl_binding import LvglBinding, LvglBindingError, LvglDisplayBackend

SCENE_MAP = {
    "card": LvglBinding.SCENE_CARD,
    "list": LvglBinding.SCENE_LIST,
    "footer": LvglBinding.SCENE_FOOTER,
    "carousel": LvglBinding.SCENE_CAROUSEL,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scene",
        choices=sorted(SCENE_MAP),
        default="carousel",
        help="Probe scene to render",
    )
    parser.add_argument(
        "--duration-seconds",
        type=float,
        default=10.0,
        help="How long to keep pumping the scene",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Use the Whisplay adapter in simulation mode",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    adapter = WhisplayDisplayAdapter(simulate=args.simulate, renderer="pil")
    backend = LvglDisplayBackend(adapter)

    if not backend.available:
        raise SystemExit(
            "LVGL shim unavailable. Build it first with `uv run python scripts/lvgl_build.py`."
        )

    if not backend.initialize():
        raise SystemExit("Failed to initialize the LVGL backend")

    try:
        backend.show_probe_scene(SCENE_MAP[args.scene])
        logger.info("Running LVGL probe scene '{}' for {:.1f}s", args.scene, args.duration_seconds)
        started_at = time.monotonic()
        last_tick = started_at
        while time.monotonic() - started_at < args.duration_seconds:
            now = time.monotonic()
            delta_ms = int(max(0.0, now - last_tick) * 1000.0)
            last_tick = now
            backend.pump(delta_ms)
            time.sleep(0.016)
    except LvglBindingError as exc:
        raise SystemExit(f"LVGL probe failed: {exc}") from exc
    finally:
        backend.cleanup()
        adapter.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
