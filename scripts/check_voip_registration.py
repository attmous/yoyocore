#!/usr/bin/env python3
"""Manual Liblinphone registration drill."""

from __future__ import annotations

import sys
import time

from loguru import logger

from yoyopy.config import ConfigManager
from yoyopy.voip import RegistrationState, VoIPConfig, VoIPManager
from yoyopy.voip.liblinphone_binding import LiblinphoneBinding

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="DEBUG",
)


def main() -> int:
    """Run a verbose SIP registration-only check against the Liblinphone backend."""

    logger.info("=" * 60)
    logger.info("Liblinphone Registration Test")
    logger.info("=" * 60)

    binding = LiblinphoneBinding.try_load()
    if binding is None:
        logger.error("Liblinphone shim is unavailable. Build it first with scripts/liblinphone_build.py.")
        return 1

    config_manager = ConfigManager(config_dir="config")
    voip_config = VoIPConfig.from_config_manager(config_manager)

    logger.info(f"SIP Server: {voip_config.sip_server}")
    logger.info(f"SIP Username: {voip_config.sip_username}")
    logger.info(f"SIP Identity: {voip_config.sip_identity}")
    logger.info(f"Transport: {voip_config.transport}")
    logger.info(f"STUN Server: {voip_config.stun_server}")
    logger.info(f"File transfer server: {voip_config.file_transfer_server_url or 'unset'}")

    voip_manager = VoIPManager(voip_config, config_manager=config_manager)
    registration_states: list[RegistrationState] = []
    voip_manager.on_registration_change(lambda state: registration_states.append(state))

    try:
        if not voip_manager.start():
            logger.error("Failed to start VoIP manager")
            return 1

        deadline = time.time() + 10.0
        while time.time() < deadline:
            voip_manager.iterate()
            status = voip_manager.get_status()
            if status["registered"]:
                logger.success("Registration successful")
                logger.success(f"State history: {[state.value for state in registration_states]}")
                return 0
            time.sleep(max(0.01, voip_config.iterate_interval_ms / 1000.0))

        status = voip_manager.get_status()
        logger.error("Registration failed or timed out")
        logger.error(f"State: {status['registration_state']}")
        logger.error(f"History: {[state.value for state in registration_states]}")
        return 1
    finally:
        voip_manager.stop()


if __name__ == "__main__":
    raise SystemExit(main())
