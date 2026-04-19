"""LVGL status-bar scene bindings."""

from __future__ import annotations


class StatusBarSceneMixin:
    """Bindings for status-bar state updates."""

    def set_status_bar_state(
        self,
        *,
        network_enabled: int,
        network_connected: int,
        wifi_connected: int,
        signal_strength: int,
        gps_has_fix: int,
    ) -> None:
        result = self.lib.yoyopod_lvgl_set_status_bar_state(
            int(network_enabled),
            int(network_connected),
            int(wifi_connected),
            max(0, min(4, int(signal_strength))),
            int(gps_has_fix),
        )
        if result != 0:
            self._raise_if_error(result)
