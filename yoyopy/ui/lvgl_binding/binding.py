"""Low-level cffi binding for the native YoyoPod LVGL shim."""

from __future__ import annotations

import os
from pathlib import Path

from cffi import FFI
from loguru import logger

SHIM_CDEF = """
typedef void (*yoyopy_lvgl_flush_cb_t)(
    int32_t x,
    int32_t y,
    int32_t width,
    int32_t height,
    const unsigned char * pixel_data,
    uint32_t byte_length,
    void * user_data
);

int yoyopy_lvgl_init(void);
void yoyopy_lvgl_shutdown(void);
int yoyopy_lvgl_register_display(
    int32_t width,
    int32_t height,
    uint32_t buffer_pixel_count,
    yoyopy_lvgl_flush_cb_t flush_cb,
    void * user_data
);
int yoyopy_lvgl_register_input(void);
void yoyopy_lvgl_tick_inc(uint32_t ms);
uint32_t yoyopy_lvgl_timer_handler(void);
int yoyopy_lvgl_queue_key_event(int32_t key, int32_t pressed);
int yoyopy_lvgl_show_probe_scene(int32_t scene_id);
int yoyopy_lvgl_hub_build(void);
int yoyopy_lvgl_hub_sync(
    const char * icon_key,
    const char * title,
    const char * subtitle,
    const char * footer,
    const char * time_text,
    uint8_t accent_r,
    uint8_t accent_g,
    uint8_t accent_b,
    int32_t selected_index,
    int32_t total_cards,
    int32_t voip_state,
    int32_t battery_percent,
    int32_t charging,
    int32_t power_available
);
void yoyopy_lvgl_hub_destroy(void);
void yoyopy_lvgl_clear_screen(void);
const char * yoyopy_lvgl_last_error(void);
const char * yoyopy_lvgl_version(void);
"""


class LvglBindingError(RuntimeError):
    """Raised when the native LVGL shim cannot be loaded or initialized."""


class LvglBinding:
    """Thin ABI-mode wrapper over the native LVGL shim."""

    KEY_NONE = 0
    KEY_RIGHT = 1
    KEY_ENTER = 2
    KEY_ESC = 3

    SCENE_CARD = 1
    SCENE_LIST = 2
    SCENE_FOOTER = 3
    SCENE_CAROUSEL = 4

    def __init__(self, library_path: Path | None = None) -> None:
        self.ffi = FFI()
        self.ffi.cdef(SHIM_CDEF)
        self.library_path = library_path or self._resolve_library_path()
        if self.library_path is None:
            raise LvglBindingError(
                "LVGL shim library not found; run scripts/lvgl_build.py on the target platform",
            )

        self.lib = self.ffi.dlopen(str(self.library_path))
        self._flush_callback = None
        logger.info("Loaded LVGL shim from {}", self.library_path)

    @classmethod
    def try_load(cls, library_path: Path | None = None) -> "LvglBinding | None":
        """Attempt to load the native shim without raising."""

        try:
            return cls(library_path=library_path)
        except Exception as exc:
            logger.debug("LVGL shim not available: {}", exc)
            return None

    def _resolve_library_path(self) -> Path | None:
        env_override = os.getenv("YOYOPOD_LVGL_SHIM_PATH")
        candidates: list[Path] = []
        if env_override:
            candidates.append(Path(env_override))

        base_dir = Path(__file__).resolve().parent
        candidates.extend(
            [
                base_dir / "native" / "build" / "libyoyopy_lvgl_shim.so",
                base_dir / "native" / "build" / "yoyopy_lvgl_shim.dll",
                base_dir / "native" / "build" / "libyoyopy_lvgl_shim.dylib",
                Path.cwd() / "build" / "lvgl" / "libyoyopy_lvgl_shim.so",
            ]
        )

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def init(self) -> None:
        if self.lib.yoyopy_lvgl_init() != 0:
            raise LvglBindingError(self.last_error())

    def shutdown(self) -> None:
        self.lib.yoyopy_lvgl_shutdown()

    def register_display(self, width: int, height: int, buffer_pixel_count: int, flush_callback) -> None:
        callback = self.ffi.callback(
            "void(int32_t, int32_t, int32_t, int32_t, const unsigned char *, uint32_t, void *)",
            flush_callback,
        )
        result = self.lib.yoyopy_lvgl_register_display(
            width,
            height,
            buffer_pixel_count,
            callback,
            self.ffi.NULL,
        )
        if result != 0:
            raise LvglBindingError(self.last_error())
        self._flush_callback = callback

    def register_input(self) -> None:
        if self.lib.yoyopy_lvgl_register_input() != 0:
            raise LvglBindingError(self.last_error())

    def tick_inc(self, milliseconds: int) -> None:
        self.lib.yoyopy_lvgl_tick_inc(max(0, int(milliseconds)))

    def timer_handler(self) -> int:
        return int(self.lib.yoyopy_lvgl_timer_handler())

    def queue_key_event(self, key: int, pressed: bool) -> None:
        if self.lib.yoyopy_lvgl_queue_key_event(int(key), 1 if pressed else 0) != 0:
            raise LvglBindingError(self.last_error())

    def show_probe_scene(self, scene_id: int) -> None:
        if self.lib.yoyopy_lvgl_show_probe_scene(scene_id) != 0:
            raise LvglBindingError(self.last_error())

    def hub_build(self) -> None:
        if self.lib.yoyopy_lvgl_hub_build() != 0:
            raise LvglBindingError(self.last_error())

    def hub_sync(
        self,
        *,
        icon_key: str,
        title: str,
        subtitle: str,
        footer: str,
        time_text: str | None,
        accent: tuple[int, int, int],
        selected_index: int,
        total_cards: int,
        voip_state: int,
        battery_percent: int,
        charging: bool,
        power_available: bool,
    ) -> None:
        icon_key_raw = self.ffi.new("char[]", icon_key.encode("utf-8"))
        title_raw = self.ffi.new("char[]", title.encode("utf-8"))
        subtitle_raw = self.ffi.new("char[]", subtitle.encode("utf-8"))
        footer_raw = self.ffi.new("char[]", footer.encode("utf-8"))
        if time_text:
            time_raw = self.ffi.new("char[]", time_text.encode("utf-8"))
        else:
            time_raw = self.ffi.NULL

        result = self.lib.yoyopy_lvgl_hub_sync(
            icon_key_raw,
            title_raw,
            subtitle_raw,
            footer_raw,
            time_raw,
            accent[0],
            accent[1],
            accent[2],
            selected_index,
            total_cards,
            voip_state,
            battery_percent,
            1 if charging else 0,
            1 if power_available else 0,
        )
        if result != 0:
            raise LvglBindingError(self.last_error())

    def hub_destroy(self) -> None:
        self.lib.yoyopy_lvgl_hub_destroy()

    def clear_screen(self) -> None:
        self.lib.yoyopy_lvgl_clear_screen()

    def to_bytes(self, pixel_data: object, byte_length: int) -> bytes:
        return bytes(self.ffi.buffer(pixel_data, byte_length))

    def last_error(self) -> str:
        raw = self.lib.yoyopy_lvgl_last_error()
        if raw == self.ffi.NULL:
            return "unknown LVGL shim error"
        return self.ffi.string(raw).decode("utf-8", errors="replace")

    def version(self) -> str:
        raw = self.lib.yoyopy_lvgl_version()
        if raw == self.ffi.NULL:
            return "unknown"
        return self.ffi.string(raw).decode("utf-8", errors="replace")
