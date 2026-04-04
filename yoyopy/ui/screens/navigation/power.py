"""Power status screen for PiSugar-backed telemetry and policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Optional

from yoyopy.ui.display import Display
from yoyopy.ui.screens.base import Screen

if TYPE_CHECKING:
    from yoyopy.app_context import AppContext
    from yoyopy.power import PowerManager, PowerSnapshot


@dataclass(frozen=True, slots=True)
class PowerPage:
    """One page of compact power/status rows."""

    title: str
    rows: list[tuple[str, str]]


class PowerScreen(Screen):
    """Compact multi-page power and runtime status screen."""

    def __init__(
        self,
        display: Display,
        context: Optional["AppContext"] = None,
        *,
        power_manager: Optional["PowerManager"] = None,
        status_provider: Optional[Callable[[], dict[str, object]]] = None,
    ) -> None:
        super().__init__(display, context, "PowerStatus")
        self.power_manager = power_manager
        self.status_provider = status_provider or (lambda: {})
        self.page_index = 0

    def render(self) -> None:
        """Render the active power page."""
        snapshot = self._get_snapshot()
        status = self._get_status()
        pages = self.build_pages(snapshot=snapshot, status=status)
        self.page_index %= len(pages)
        active_page = pages[self.page_index]

        self.display.clear(self.display.COLOR_BLACK)
        self._render_status_bar()

        title = active_page.title
        title_size = 18
        title_width, title_height = self.display.get_text_size(title, title_size)
        title_x = (self.display.WIDTH - title_width) // 2
        title_y = self.display.STATUS_BAR_HEIGHT + 12
        self.display.text(
            title,
            title_x,
            title_y,
            color=self.display.COLOR_WHITE,
            font_size=title_size,
        )

        page_text = f"{self.page_index + 1}/{len(pages)}"
        page_width, _ = self.display.get_text_size(page_text, 11)
        self.display.text(
            page_text,
            self.display.WIDTH - page_width - 18,
            title_y + 3,
            color=self.display.COLOR_GRAY,
            font_size=11,
        )

        separator_y = title_y + title_height + 8
        self.display.line(
            18,
            separator_y,
            self.display.WIDTH - 18,
            separator_y,
            color=self.display.COLOR_GRAY,
            width=2,
        )

        row_y = separator_y + 14
        row_gap = 23 if self.display.is_portrait() else 21
        label_size = 12
        value_size = 13

        for label, value in active_page.rows:
            self.display.text(
                label,
                16,
                row_y,
                color=self.display.COLOR_GRAY,
                font_size=label_size,
            )
            value_width, _ = self.display.get_text_size(value, value_size)
            value_x = max(90, self.display.WIDTH - value_width - 16)
            self.display.text(
                value,
                value_x,
                row_y,
                color=self.display.COLOR_WHITE,
                font_size=value_size,
            )
            row_y += row_gap

        help_text = (
            "Tap page | Double page | Hold back"
            if self.is_one_button_mode()
            else "X/Y page | A page | B back"
        )
        help_width, _ = self.display.get_text_size(help_text, 10)
        self.display.text(
            help_text,
            (self.display.WIDTH - help_width) // 2,
            self.display.HEIGHT - 15,
            color=self.display.COLOR_GRAY,
            font_size=10,
        )
        self.display.update()

    def build_pages(
        self,
        *,
        snapshot: Optional["PowerSnapshot"],
        status: dict[str, object],
    ) -> list[PowerPage]:
        """Build the current compact pages for rendering and tests."""
        battery_rows = self._build_battery_rows(snapshot=snapshot)
        runtime_rows = self._build_runtime_rows(snapshot=snapshot, status=status)
        return [
            PowerPage(title="Power Status", rows=battery_rows),
            PowerPage(title="Runtime & Safety", rows=runtime_rows),
        ]

    def _render_status_bar(self) -> None:
        """Render the shared status bar using cached context telemetry."""
        current_time = datetime.now().strftime("%H:%M")
        battery = self.context.battery_percent if self.context else 100
        charging = self.context.battery_charging if self.context else False
        external_power = self.context.external_power if self.context else False
        power_available = self.context.power_available if self.context else False
        signal = self.context.signal_strength if self.context else 4
        self.display.status_bar(
            time_str=current_time,
            battery_percent=battery,
            signal_strength=signal,
            charging=charging,
            external_power=external_power,
            power_available=power_available,
        )

    def _get_snapshot(self) -> Optional["PowerSnapshot"]:
        """Return the latest cached power snapshot."""
        if self.power_manager is None:
            return None
        return self.power_manager.get_snapshot()

    def _get_status(self) -> dict[str, object]:
        """Return the latest app runtime/policy status."""
        try:
            return self.status_provider()
        except Exception:
            return {}

    def _build_battery_rows(self, *, snapshot: Optional["PowerSnapshot"]) -> list[tuple[str, str]]:
        """Build the first page focused on PiSugar telemetry."""
        if snapshot is None:
            return [
                ("Source", "Unavailable"),
                ("Battery", "Unknown"),
                ("Charging", "Unknown"),
                ("External", "Unknown"),
                ("RTC", "Unknown"),
                ("Alarm", "Unknown"),
            ]

        if not snapshot.available:
            error = snapshot.error or "Unavailable"
            return [
                ("Source", snapshot.source),
                ("Model", snapshot.device.model or "Unknown"),
                ("Status", "Offline"),
                ("Reason", self._truncate(error, 18)),
                ("RTC", self._format_datetime(snapshot.rtc.time)),
                ("Alarm", self._format_alarm(snapshot)),
            ]

        return [
            ("Model", snapshot.device.model or "Unknown"),
            ("Battery", self._format_battery(snapshot)),
            ("Charging", self._format_charging(snapshot)),
            ("External", self._format_external_power(snapshot)),
            ("Voltage", self._format_voltage(snapshot)),
            ("RTC", self._format_datetime(snapshot.rtc.time)),
            ("Alarm", self._format_alarm(snapshot)),
        ]

    def _build_runtime_rows(
        self,
        *,
        snapshot: Optional["PowerSnapshot"],
        status: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Build the second page for runtime, watchdog, and shutdown state."""
        warning_percent = self._format_percent(status.get("warning_threshold_percent"))
        critical_percent = self._format_percent(status.get("critical_shutdown_percent"))
        delay_seconds = self._format_duration_short(status.get("shutdown_delay_seconds"))
        shutdown_value = "Ready"
        if status.get("shutdown_pending"):
            shutdown_value = f"In {self._format_duration_short(status.get('shutdown_in_seconds'))}"

        rows = [
            ("Uptime", self._format_duration_short(status.get("app_uptime_seconds"))),
            ("Screen", self._format_screen_state(status)),
            ("Idle", self._format_duration_short(status.get("screen_idle_seconds"))),
            ("Timeout", self._format_duration_short(status.get("screen_timeout_seconds"))),
            ("Warn/Crit", f"{warning_percent}/{critical_percent}"),
            ("Shutdown", shutdown_value if delay_seconds == "0s" else f"{shutdown_value} ({delay_seconds})"),
            ("Watchdog", self._format_watchdog(status)),
        ]

        if snapshot is not None and snapshot.shutdown.safe_shutdown_level_percent is not None:
            rows[4] = (
                "Warn/Crit",
                f"{warning_percent}/{self._format_percent(snapshot.shutdown.safe_shutdown_level_percent)}",
            )
        return rows

    def _format_battery(self, snapshot: "PowerSnapshot") -> str:
        """Format the battery percentage with a compact status suffix."""
        level = snapshot.battery.level_percent
        if level is None:
            return "Unknown"
        suffix = " chg" if snapshot.battery.charging else ""
        return f"{round(level)}%{suffix}"

    def _format_charging(self, snapshot: "PowerSnapshot") -> str:
        """Format the charging state."""
        charging = snapshot.battery.charging
        if charging is None:
            return "Unknown"
        return "Charging" if charging else "Idle"

    def _format_external_power(self, snapshot: "PowerSnapshot") -> str:
        """Format whether USB/external power is present."""
        plugged = snapshot.battery.power_plugged
        if plugged is None:
            return "Unknown"
        return "Plugged" if plugged else "Battery"

    def _format_voltage(self, snapshot: "PowerSnapshot") -> str:
        """Format battery voltage with optional temperature hint."""
        voltage = snapshot.battery.voltage_volts
        temperature = snapshot.battery.temperature_celsius
        if voltage is None and temperature is None:
            return "Unknown"
        if voltage is None:
            return f"{temperature:.1f} C"
        if temperature is None:
            return f"{voltage:.2f} V"
        return f"{voltage:.2f}V {temperature:.0f}C"

    def _format_alarm(self, snapshot: "PowerSnapshot") -> str:
        """Format the current RTC alarm state."""
        if snapshot.rtc.alarm_enabled is not True:
            return "Off"
        if snapshot.rtc.alarm_time is None:
            return "On"
        return snapshot.rtc.alarm_time.strftime("%H:%M")

    @staticmethod
    def _format_datetime(value: datetime | None) -> str:
        """Format one datetime value for compact screen use."""
        if value is None:
            return "Unknown"
        return value.strftime("%m-%d %H:%M")

    @staticmethod
    def _format_duration_short(value: object) -> str:
        """Format short durations like 95 seconds -> 1m35s."""
        if value is None:
            return "0s"
        total_seconds = max(0, int(float(value)))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h{minutes:02d}m"
        if minutes > 0:
            return f"{minutes}m{seconds:02d}s"
        return f"{seconds}s"

    @staticmethod
    def _format_percent(value: object) -> str:
        """Format a percentage-like value for screen use."""
        if value is None:
            return "--"
        return f"{int(round(float(value)))}%"

    @staticmethod
    def _format_watchdog(status: dict[str, object]) -> str:
        """Format the current watchdog state from app status."""
        if not status.get("watchdog_enabled"):
            return "Off"
        if status.get("watchdog_feed_suppressed"):
            return "Suppressed"
        if status.get("watchdog_active"):
            return "Active"
        return "Ready"

    @staticmethod
    def _format_screen_state(status: dict[str, object]) -> str:
        """Format current display-awake plus cumulative screen-on time."""
        state = "Awake" if status.get("screen_awake") else "Sleep"
        screen_on = PowerScreen._format_duration_short(status.get("screen_on_seconds"))
        return f"{state} {screen_on}"

    @staticmethod
    def _truncate(text: str, max_length: int) -> str:
        """Truncate strings that would overflow narrow labels."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _next_page(self) -> None:
        """Advance to the next power page with wraparound."""
        self.page_index = (self.page_index + 1) % 2

    def _previous_page(self) -> None:
        """Return to the previous power page with wraparound."""
        self.page_index = (self.page_index - 1) % 2

    def on_advance(self, data=None) -> None:
        """Single-button tap cycles pages."""
        self._next_page()

    def on_select(self, data=None) -> None:
        """Double tap or standard select also cycles pages."""
        self._next_page()

    def on_back(self, data=None) -> None:
        """Return to the previous screen."""
        self.request_route("back")

    def on_up(self, data=None) -> None:
        """Standard up goes to the previous page."""
        self._previous_page()

    def on_down(self, data=None) -> None:
        """Standard down goes to the next page."""
        self._next_page()

    def on_left(self, data=None) -> None:
        """Standard left goes to the previous page."""
        self._previous_page()

    def on_right(self, data=None) -> None:
        """Standard right goes to the next page."""
        self._next_page()
