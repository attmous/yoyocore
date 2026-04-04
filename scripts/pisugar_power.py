#!/usr/bin/env python3
"""PiSugar power helper for current telemetry and policy status."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from yoyopy.config import ConfigManager
from yoyopy.power import PowerManager, PowerSnapshot


def configure_logging(verbose: bool) -> None:
    """Configure human-readable logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG" if verbose else "INFO",
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Inspect PiSugar power telemetry through YoyoPod's power module.",
    )
    parser.add_argument(
        "--config-dir",
        default="config",
        help="Configuration directory to use (default: config)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging",
    )
    return parser


def build_manager(config_dir: Path) -> PowerManager:
    """Create a power manager for the configured PiSugar backend."""
    config_manager = ConfigManager(config_dir=str(config_dir))
    manager = PowerManager.from_config_manager(config_manager)
    if not manager.config.enabled:
        raise RuntimeError("power backend disabled in yoyopod_config.yaml")
    return manager


def format_snapshot(snapshot: PowerSnapshot, manager: PowerManager) -> list[str]:
    """Return a readable summary of power telemetry and policy settings."""
    return [
        f"available={snapshot.available}",
        f"source={snapshot.source}",
        f"error={snapshot.error or 'none'}",
        f"model={snapshot.device.model or 'unknown'}",
        f"battery_percent={snapshot.battery.level_percent if snapshot.battery.level_percent is not None else 'unknown'}",
        f"battery_voltage={snapshot.battery.voltage_volts if snapshot.battery.voltage_volts is not None else 'unknown'}",
        f"temperature_celsius={snapshot.battery.temperature_celsius if snapshot.battery.temperature_celsius is not None else 'unknown'}",
        f"charging={snapshot.battery.charging if snapshot.battery.charging is not None else 'unknown'}",
        f"external_power={snapshot.battery.power_plugged if snapshot.battery.power_plugged is not None else 'unknown'}",
        f"allow_charging={snapshot.battery.allow_charging if snapshot.battery.allow_charging is not None else 'unknown'}",
        f"output_enabled={snapshot.battery.output_enabled if snapshot.battery.output_enabled is not None else 'unknown'}",
        f"rtc_time={snapshot.rtc.time.isoformat() if snapshot.rtc.time is not None else 'unknown'}",
        f"rtc_alarm_enabled={snapshot.rtc.alarm_enabled if snapshot.rtc.alarm_enabled is not None else 'unknown'}",
        f"rtc_alarm_time={snapshot.rtc.alarm_time.isoformat() if snapshot.rtc.alarm_time is not None else 'none'}",
        f"safe_shutdown_level={snapshot.shutdown.safe_shutdown_level_percent if snapshot.shutdown.safe_shutdown_level_percent is not None else 'unknown'}",
        f"safe_shutdown_delay={snapshot.shutdown.safe_shutdown_delay_seconds if snapshot.shutdown.safe_shutdown_delay_seconds is not None else 'unknown'}",
        f"warning_threshold={manager.config.low_battery_warning_percent}",
        f"critical_threshold={manager.config.critical_shutdown_percent}",
        f"shutdown_delay_seconds={manager.config.shutdown_delay_seconds}",
        f"watchdog_enabled={manager.config.watchdog_enabled}",
        f"watchdog_timeout_seconds={manager.config.watchdog_timeout_seconds}",
        f"watchdog_feed_interval_seconds={manager.config.watchdog_feed_interval_seconds}",
    ]


def main() -> int:
    """Program entry point."""
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.verbose)

    config_dir = Path(args.config_dir)
    if not config_dir.is_absolute():
        config_dir = REPO_ROOT / config_dir

    manager = build_manager(config_dir)
    snapshot = manager.refresh()
    if not snapshot.available:
        logger.error(snapshot.error or "power backend unavailable")
        return 1

    print("")
    print("PiSugar power status")
    print("====================")
    for line in format_snapshot(snapshot, manager):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
