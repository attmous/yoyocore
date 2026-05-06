"""System validation subcommand."""

from __future__ import annotations

import platform
import time
from pathlib import Path
from typing import Annotated, Any

import typer

from yoyopod_cli.pi.validate._common import (
    _CheckResult,
    _load_app_config,
    _print_summary,
)
from yoyopod_cli.common import configure_logging, resolve_config_dir


def _environment_check() -> _CheckResult:
    """Capture the current execution environment."""
    system = platform.system()
    machine = platform.machine()
    python_version = platform.python_version()

    if system == "Linux" and ("arm" in machine.lower() or "aarch" in machine.lower()):
        status = "pass"
    else:
        status = "warn"

    return _CheckResult(
        name="environment",
        status=status,
        details=f"system={system}, machine={machine}, python={python_version}",
    )


def _display_check(
    app_config: dict[str, Any],
    hold_seconds: float,
) -> tuple[_CheckResult, Any]:
    """Validate display initialization on target hardware."""
    from yoyopod_cli.pi.support.display import Display, detect_hardware
    from yoyopod_cli.pi.support.lvgl_binding.binding import LvglBinding

    def _render_lvgl_probe(display: Any, ui_backend: Any) -> None:
        if not ui_backend.initialize():
            raise RuntimeError("LVGL backend failed to initialize during smoke validation")

        ui_backend.show_probe_scene(LvglBinding.SCENE_CARD)
        ui_backend.force_refresh()
        ui_backend.pump(16)

        refresh_backend_kind = getattr(display, "refresh_backend_kind", None)
        if callable(refresh_backend_kind):
            refresh_backend_kind()

        if hold_seconds <= 0:
            return

        remaining_seconds = hold_seconds
        while remaining_seconds > 0:
            slice_seconds = min(0.05, remaining_seconds)
            time.sleep(slice_seconds)
            ui_backend.pump(max(1, int(slice_seconds * 1000)))
            remaining_seconds -= slice_seconds

    requested_hardware = str(app_config.get("display", {}).get("hardware", "auto")).lower()
    resolved_hardware = detect_hardware() if requested_hardware == "auto" else requested_hardware

    if resolved_hardware == "simulation":
        return (
            _CheckResult(
                name="display",
                status="fail",
                details=(
                    "hardware detection resolved to simulation; "
                    "no supported Raspberry Pi display hardware was found"
                ),
            ),
            None,
        )

    display = None
    try:
        display = Display(hardware=resolved_hardware, simulate=False)
        adapter = display.get_adapter()
        ui_backend = display.get_ui_backend()

        if ui_backend is not None:
            _render_lvgl_probe(display, ui_backend)
        else:
            display.clear(display.COLOR_BLACK)
            display.text("YoYoPod Pi smoke", 10, 40, color=display.COLOR_WHITE, font_size=18)
            display.text("Display OK", 10, 75, color=display.COLOR_GREEN, font_size=18)
            display.update()

            if hold_seconds > 0:
                time.sleep(hold_seconds)

        if display.simulate:
            return (
                _CheckResult(
                    name="display",
                    status="fail",
                    details=(
                        f"adapter {adapter.__class__.__name__} fell back to simulation "
                        "instead of hardware mode"
                    ),
                ),
                display,
            )

        return (
            _CheckResult(
                name="display",
                status="pass",
                details=(
                    f"adapter={adapter.__class__.__name__}, "
                    f"backend={display.backend_kind}, "
                    f"size={display.WIDTH}x{display.HEIGHT}, "
                    f"orientation={display.ORIENTATION}, "
                    f"requested={requested_hardware}, resolved={resolved_hardware}"
                ),
            ),
            display,
        )
    except Exception as exc:
        if display is not None:
            try:
                display.cleanup()
            except Exception:
                pass
        return _CheckResult(name="display", status="fail", details=str(exc)), None


def _input_check(display: Any, app_config: dict[str, Any]) -> _CheckResult:
    """Validate that the active display hardware exposes a readable input path."""

    try:
        adapter = display.get_adapter()
        display_type = _display_type(adapter)
        if display_type == "whisplay":
            return _whisplay_input_check(adapter, app_config)
        if display_type == "pimoroni":
            return _pimoroni_input_check(adapter, app_config)
        return _CheckResult(
            name="input",
            status="fail",
            details=f"no smoke input probe is registered for display type {display_type}",
        )
    except Exception as exc:
        return _CheckResult(name="input", status="fail", details=str(exc))


def _display_type(adapter: Any) -> str:
    display_type = getattr(adapter, "DISPLAY_TYPE", None)
    if isinstance(display_type, str) and display_type.strip():
        return display_type.strip().lower()
    adapter_name = str(adapter.__class__.__name__)
    return adapter_name.replace("DisplayAdapter", "").lower()


def _whisplay_input_check(adapter: Any, app_config: dict[str, Any]) -> _CheckResult:
    input_config = app_config.get("input", {})
    if not isinstance(input_config, dict):
        input_config = {}
    if not bool(input_config.get("ptt_navigation", True)):
        return _CheckResult(
            name="input",
            status="fail",
            details="Whisplay ptt_navigation is disabled; one-button navigation input is unavailable",
        )

    device = getattr(adapter, "device", None)
    if device is None:
        return _CheckResult(
            name="input",
            status="fail",
            details="Whisplay display initialized without a readable button device",
        )

    reader = getattr(device, "button_pressed", None)
    if callable(reader):
        pressed = bool(reader())
        return _CheckResult(
            name="input",
            status="pass",
            details=f"adapter=Whisplay one_button source=button_pressed pressed={pressed}",
        )
    if reader is not None:
        pressed = bool(reader)
        return _CheckResult(
            name="input",
            status="pass",
            details=f"adapter=Whisplay one_button source=button_pressed_attr pressed={pressed}",
        )

    state_reader = getattr(device, "get_button_state", None)
    if callable(state_reader):
        pressed = bool(state_reader())
        return _CheckResult(
            name="input",
            status="pass",
            details=f"adapter=Whisplay one_button source=get_button_state pressed={pressed}",
        )

    return _CheckResult(
        name="input",
        status="fail",
        details="Whisplay button device does not expose button_pressed or get_button_state",
    )


def _pimoroni_input_check(adapter: Any, app_config: dict[str, Any]) -> _CheckResult:
    device = getattr(adapter, "device", None)
    if device is not None and _pimoroni_displayhatmini_probe(device):
        return _CheckResult(
            name="input",
            status="pass",
            details="adapter=Pimoroni source=displayhatmini buttons=A,B,X,Y",
        )

    input_config = app_config.get("input", {})
    if not isinstance(input_config, dict):
        input_config = {}
    gpio_config = input_config.get("pimoroni_gpio")
    if not isinstance(gpio_config, dict) or not gpio_config:
        return _CheckResult(
            name="input",
            status="fail",
            details="Pimoroni input has no displayhatmini device and no input.pimoroni_gpio config",
        )

    acquired = _probe_pimoroni_gpiod_buttons(gpio_config)
    if acquired != 4:
        return _CheckResult(
            name="input",
            status="fail",
            details=f"Pimoroni gpiod probe acquired {acquired}/4 configured buttons",
        )
    return _CheckResult(
        name="input",
        status="pass",
        details="adapter=Pimoroni source=gpiod buttons=A,B,X,Y",
    )


def _pimoroni_displayhatmini_probe(device: Any) -> bool:
    reader = getattr(device, "read_button", None)
    if not callable(reader):
        return False

    button_names = ("BUTTON_A", "BUTTON_B", "BUTTON_X", "BUTTON_Y")
    for name in button_names:
        button = getattr(device, name, None)
        if button is None:
            raise RuntimeError(f"displayhatmini device is missing {name}")
        bool(reader(button))
    return True


def _probe_pimoroni_gpiod_buttons(gpio_config: dict[str, Any]) -> int:
    from yoyopod_cli.pi.support.gpiod_compat import HAS_GPIOD, open_chip, request_input

    if not HAS_GPIOD:
        raise RuntimeError("gpiod module is required for Pimoroni GPIO input smoke probe")

    acquired = 0
    handles: list[Any] = []
    chips: list[Any] = []
    try:
        for key in ("button_a", "button_b", "button_x", "button_y"):
            pin = gpio_config.get(key)
            if not isinstance(pin, dict):
                continue
            chip_name = pin.get("chip")
            line_offset = pin.get("line")
            if chip_name is None or line_offset is None:
                continue
            chip = open_chip(str(chip_name))
            chips.append(chip)
            line = request_input(chip, int(line_offset), f"yoyopod-smoke-{key}")
            handles.append(line)
            getter = getattr(line, "get_value", None)
            if callable(getter):
                getter()
            acquired += 1
        return acquired
    finally:
        for line in handles:
            releaser = getattr(line, "release", None)
            if callable(releaser):
                try:
                    releaser()
                except Exception:
                    pass
        for chip in chips:
            closer = getattr(chip, "close", None)
            if callable(closer):
                try:
                    closer()
                except Exception:
                    pass


def _power_check(config_dir: Path) -> _CheckResult:
    """Validate PiSugar reachability and report a live battery snapshot."""
    from yoyopod_cli.config import ConfigManager
    from yoyopod_cli.pi.support.power_integration import PowerManager

    config_manager = ConfigManager(config_dir=str(config_dir))
    manager = PowerManager.from_config_manager(config_manager)

    if not manager.config.enabled:
        return _CheckResult(
            name="power",
            status="warn",
            details="power backend disabled in config/power/backend.yaml",
        )

    snapshot = manager.refresh()
    if not snapshot.available:
        details = snapshot.error or "power backend unavailable"
        return _CheckResult(name="power", status="fail", details=details)

    details = ", ".join(
        [
            f"model={snapshot.device.model or 'unknown'}",
            (
                f"battery={snapshot.battery.level_percent:.1f}%"
                if snapshot.battery.level_percent is not None
                else "battery=unknown"
            ),
            f"charging={snapshot.battery.charging}",
            f"plugged={snapshot.battery.power_plugged}",
        ]
    )
    return _CheckResult(name="power", status="pass", details=details)


def _rtc_check(config_dir: Path) -> _CheckResult:
    """Validate PiSugar RTC reachability and report the current RTC state."""
    from yoyopod_cli.config import ConfigManager
    from yoyopod_cli.pi.support.power_integration import PowerManager

    config_manager = ConfigManager(config_dir=str(config_dir))
    manager = PowerManager.from_config_manager(config_manager)

    if not manager.config.enabled:
        return _CheckResult(
            name="rtc",
            status="warn",
            details="power backend disabled in config/power/backend.yaml",
        )

    snapshot = manager.refresh()
    if not snapshot.available:
        details = snapshot.error or "power backend unavailable"
        return _CheckResult(name="rtc", status="fail", details=details)

    if snapshot.rtc.time is None:
        return _CheckResult(
            name="rtc",
            status="fail",
            details="PiSugar backend responded but rtc_time is unavailable",
        )

    details = ", ".join(
        [
            f"time={snapshot.rtc.time.isoformat()}",
            f"alarm_enabled={snapshot.rtc.alarm_enabled}",
            f"alarm_time={snapshot.rtc.alarm_time.isoformat() if snapshot.rtc.alarm_time is not None else 'none'}",
            f"repeat_mask={snapshot.rtc.alarm_repeat_mask if snapshot.rtc.alarm_repeat_mask is not None else 'unknown'}",
        ]
    )
    return _CheckResult(name="rtc", status="pass", details=details)


def smoke(
    config_dir: Annotated[
        str, typer.Option("--config-dir", help="Configuration directory to use.")
    ] = "config",
    with_power: Annotated[
        bool, typer.Option("--with-power", help="Also validate PiSugar power telemetry.")
    ] = False,
    with_rtc: Annotated[
        bool, typer.Option("--with-rtc", help="Also validate PiSugar RTC state and alarm.")
    ] = False,
    display_hold_seconds: Annotated[
        float,
        typer.Option(
            "--display-hold-seconds",
            help="How long to keep the display confirmation text visible.",
        ),
    ] = 0.5,
    verbose: Annotated[bool, typer.Option("--verbose", help="Enable DEBUG logging.")] = False,
) -> None:
    """Validate core target hardware paths: environment, display, input, and optional PiSugar state."""
    from loguru import logger

    configure_logging(verbose)
    config_path = resolve_config_dir(config_dir)

    logger.info("Running target smoke validation")

    app_config = _load_app_config(config_path)
    results: list[_CheckResult] = [_environment_check()]
    display = None

    try:
        display_result, display = _display_check(app_config, display_hold_seconds)
        results.append(display_result)

        if display_result.status == "pass" and display is not None:
            results.append(_input_check(display, app_config))

        if with_power:
            results.append(_power_check(config_path))

        if with_rtc:
            results.append(_rtc_check(config_path))
    finally:
        if display is not None:
            try:
                display.cleanup()
            except Exception as exc:
                logger.warning(f"Display cleanup failed: {exc}")

    _print_summary("smoke", results)
    if any(result.status == "fail" for result in results):
        raise typer.Exit(code=1)
