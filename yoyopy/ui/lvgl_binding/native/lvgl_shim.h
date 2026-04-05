#ifndef YOYOPY_LVGL_SHIM_H
#define YOYOPY_LVGL_SHIM_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*yoyopy_lvgl_flush_cb_t)(
    int32_t x,
    int32_t y,
    int32_t width,
    int32_t height,
    const unsigned char * pixel_data,
    uint32_t byte_length,
    void * user_data
);

enum yoyopy_lvgl_key {
    YOYOPY_LVGL_KEY_NONE = 0,
    YOYOPY_LVGL_KEY_RIGHT = 1,
    YOYOPY_LVGL_KEY_ENTER = 2,
    YOYOPY_LVGL_KEY_ESC = 3
};

enum yoyopy_lvgl_probe_scene {
    YOYOPY_LVGL_SCENE_CARD = 1,
    YOYOPY_LVGL_SCENE_LIST = 2,
    YOYOPY_LVGL_SCENE_FOOTER = 3,
    YOYOPY_LVGL_SCENE_CAROUSEL = 4
};

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

#ifdef __cplusplus
}
#endif

#endif
