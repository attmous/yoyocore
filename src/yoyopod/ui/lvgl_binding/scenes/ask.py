"""LVGL Ask scene bindings."""

from __future__ import annotations


class AskSceneMixin:
    """Bindings for the Ask scene."""

    def ask_build(self) -> None:
        self._raise_if_error(self.lib.yoyopod_lvgl_ask_build())

    def ask_sync(
        self,
        *,
        icon_key: str,
        title_text: str,
        subtitle_text: str,
        footer: str,
        voip_state: int,
        battery_percent: int,
        charging: bool,
        power_available: bool,
        accent: tuple[int, int, int],
    ) -> None:
        icon_raw = self.ffi.new("char[]", icon_key.encode("utf-8"))
        title_raw = self.ffi.new("char[]", title_text.encode("utf-8"))
        subtitle_raw = self.ffi.new("char[]", subtitle_text.encode("utf-8"))
        footer_raw = self.ffi.new("char[]", footer.encode("utf-8"))
        self._raise_if_error(
            self.lib.yoyopod_lvgl_ask_sync(
                icon_raw,
                title_raw,
                subtitle_raw,
                footer_raw,
                voip_state,
                battery_percent,
                1 if charging else 0,
                1 if power_available else 0,
                self._pack_rgb(accent),
            )
        )

    def ask_destroy(self) -> None:
        self.lib.yoyopod_lvgl_ask_destroy()
