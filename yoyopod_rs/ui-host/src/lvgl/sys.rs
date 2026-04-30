use std::ffi::c_char;
use std::ffi::c_void;

#[repr(C)]
pub struct lv_display_t {
    _private: [u8; 0],
}

#[repr(C)]
pub struct lv_obj_t {
    _private: [u8; 0],
}

#[repr(C)]
pub struct lv_area_t {
    pub x1: i32,
    pub y1: i32,
    pub x2: i32,
    pub y2: i32,
}

pub type LvDisplayFlushCb = unsafe extern "C" fn(*mut lv_display_t, *const lv_area_t, *mut u8);

pub const LV_DISPLAY_RENDER_MODE_PARTIAL: i32 = 0;

unsafe extern "C" {
    pub fn lv_init();
    pub fn lv_deinit();
    pub fn lv_tick_inc(tick_period: u32);
    pub fn lv_timer_handler() -> u32;

    pub fn lv_display_create(hor_res: i32, ver_res: i32) -> *mut lv_display_t;
    pub fn lv_display_delete(display: *mut lv_display_t);
    pub fn lv_display_set_default(display: *mut lv_display_t);
    pub fn lv_display_set_flush_cb(display: *mut lv_display_t, flush_cb: Option<LvDisplayFlushCb>);
    pub fn lv_display_set_buffers(
        display: *mut lv_display_t,
        buf1: *mut c_void,
        buf2: *mut c_void,
        buf_size: u32,
        render_mode: i32,
    );
    pub fn lv_display_set_user_data(display: *mut lv_display_t, user_data: *mut c_void);
    pub fn lv_display_get_user_data(display: *mut lv_display_t) -> *mut c_void;
    pub fn lv_display_flush_ready(display: *mut lv_display_t);
    pub fn lv_display_get_screen_active(display: *mut lv_display_t) -> *mut lv_obj_t;

    pub fn lv_obj_create(parent: *mut lv_obj_t) -> *mut lv_obj_t;
    pub fn lv_obj_delete(obj: *mut lv_obj_t);
    pub fn lv_obj_set_pos(obj: *mut lv_obj_t, x: i32, y: i32);
    pub fn lv_obj_set_size(obj: *mut lv_obj_t, width: i32, height: i32);
    pub fn lv_obj_set_width(obj: *mut lv_obj_t, width: i32);
    pub fn lv_obj_set_height(obj: *mut lv_obj_t, height: i32);
    pub fn lv_obj_invalidate(obj: *mut lv_obj_t);

    pub fn lv_label_create(parent: *mut lv_obj_t) -> *mut lv_obj_t;
    pub fn lv_label_set_text(obj: *mut lv_obj_t, text: *const c_char);

    pub fn lv_screen_load(screen: *mut lv_obj_t);
}
