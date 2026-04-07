#!/usr/bin/env python3
"""Manual incoming-call debug drill for the Liblinphone backend."""

from __future__ import annotations

import sys
import time

from loguru import logger

from yoyopy.config import ConfigManager
from yoyopy.voip import VoIPConfig, VoIPManager
from yoyopy.voip.liblinphone_binding import LiblinphoneBinding

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="DEBUG",
)


def main() -> int:
    """Run a verbose incoming-call check while iterating the Liblinphone core."""

    logger.info("=" * 60)
    logger.info("Incoming Call Debug Test")
    logger.info("=" * 60)

    binding = LiblinphoneBinding.try_load()
    if binding is None:
        logger.error("Liblinphone shim is unavailable. Build it first with scripts/liblinphone_build.py.")
        return 1

    config_manager = ConfigManager(config_dir="config")
    voip_config = VoIPConfig.from_config_manager(config_manager)
    voip_manager = VoIPManager(voip_config, config_manager=config_manager)
    incoming_calls: list[tuple[str, str]] = []

    def on_incoming_call(caller_address: str, caller_name: str) -> None:
        logger.success("=" * 60)
        logger.success("INCOMING CALL CALLBACK FIRED")
        logger.success(f"  Address: {caller_address}")
        logger.success(f"  Name: {caller_name}")
        logger.success("=" * 60)
        incoming_calls.append((caller_address, caller_name))

    voip_manager.on_incoming_call(on_incoming_call)

    try:
        if not voip_manager.start():
            logger.error("Failed to start VoIP manager")
            return 1

        logger.info(f"Waiting for incoming calls on {voip_config.sip_identity}")
        logger.info("Press Ctrl+C to exit")

        while True:
            voip_manager.iterate()
            time.sleep(max(0.01, voip_config.iterate_interval_ms / 1000.0))
    except KeyboardInterrupt:
        logger.info("Interrupted")
        return 0
    finally:
        voip_manager.stop()
        logger.info(f"Total incoming calls detected: {len(incoming_calls)}")
        for address, name in incoming_calls:
            logger.info(f"  - {name} ({address})")


if __name__ == "__main__":
    raise SystemExit(main())
