"""
Display hardware factory for YoyoPod.

This module provides factory functions to create the appropriate display
adapter based on hardware detection or configuration.
"""

from __future__ import annotations

import os

from loguru import logger

from yoyopy.ui.display.hal import DisplayHAL
from yoyopy.ui.display.whisplay_paths import find_whisplay_driver


def detect_hardware() -> str:
    """Auto-detect which display hardware is connected."""

    env_display = os.getenv("YOYOPOD_DISPLAY")
    if env_display:
        hardware = env_display.lower()
        logger.info("Display hardware set by YOYOPOD_DISPLAY={}", hardware)
        return hardware

    whisplay_driver_path = find_whisplay_driver()
    if whisplay_driver_path:
        logger.info("Detected Whisplay HAT (driver found at {})", whisplay_driver_path)
        return "whisplay"

    try:
        import displayhatmini  # noqa: F401

        logger.info("Detected Pimoroni Display HAT Mini (library imported successfully)")
        return "pimoroni"
    except Exception as exc:
        logger.debug("DisplayHATMini import failed during detection: {}", exc)

    logger.warning("No display hardware detected - defaulting to simulation mode")
    logger.info("To force hardware type, set YOYOPOD_DISPLAY environment variable")
    return "simulation"


def get_display(
    hardware: str = "auto",
    simulate: bool = False,
    *,
    whisplay_renderer: str = "pil",
) -> DisplayHAL:
    """Create the appropriate display adapter."""

    if simulate:
        hardware = "simulation"
        logger.info("Forcing simulation mode (--simulate flag)")

    if hardware == "auto":
        hardware = detect_hardware()

    hardware = hardware.lower()

    if hardware == "whisplay":
        logger.info(
            "Creating Whisplay display adapter with renderer={}",
            whisplay_renderer,
        )
        from yoyopy.ui.display.adapters.whisplay import WhisplayDisplayAdapter

        return WhisplayDisplayAdapter(
            simulate=simulate,
            renderer=whisplay_renderer,
        )

    if hardware == "pimoroni":
        logger.info("Creating Pimoroni display adapter (320x240 landscape)")
        from yoyopy.ui.display.adapters.pimoroni import PimoroniDisplayAdapter

        return PimoroniDisplayAdapter(simulate=simulate)

    if hardware == "simulation":
        logger.info("Creating simulation display adapter (240x280 portrait)")
        from yoyopy.ui.display.adapters.simulation import SimulationDisplayAdapter

        adapter = SimulationDisplayAdapter(simulate=True)

        if simulate or hardware == "simulation":
            try:
                from yoyopy.ui.web_server import get_server

                server = get_server()
                adapter.web_server = server
                server.start()
                logger.info("Web server started - view display at http://localhost:5000")
            except Exception as exc:
                logger.warning("Failed to start web server: {}", exc)
                logger.warning("Simulation display will work without web view")

        return adapter

    valid_types = ["auto", "whisplay", "pimoroni", "simulation"]
    raise ValueError(
        f"Unknown display hardware type: '{hardware}'. "
        f"Valid options: {', '.join(valid_types)}"
    )


def get_hardware_info(adapter: DisplayHAL) -> dict[str, object]:
    """Return debugging information about a display adapter."""

    return {
        "type": adapter.__class__.__name__,
        "width": adapter.WIDTH,
        "height": adapter.HEIGHT,
        "orientation": adapter.ORIENTATION,
        "status_bar_height": adapter.STATUS_BAR_HEIGHT,
        "simulated": adapter.simulate,
        "renderer": adapter.get_backend_kind(),
    }
