use yoyopod_ui_host::lvgl::open_default_facade;

#[cfg(not(feature = "native-lvgl"))]
#[test]
fn open_default_facade_without_native_feature_returns_contextual_error() {
    let error = match open_default_facade(None) {
        Ok(_) => panic!("native-lvgl should be required"),
        Err(error) => error,
    };

    assert!(error.to_string().contains("native-lvgl feature"));
}

#[cfg(feature = "native-lvgl")]
use std::path::Path;
#[cfg(feature = "native-lvgl")]
use std::sync::{Mutex, MutexGuard, OnceLock};

#[cfg(feature = "native-lvgl")]
fn native_lvgl_test_guard() -> MutexGuard<'static, ()> {
    static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    LOCK.get_or_init(|| Mutex::new(()))
        .lock()
        .expect("native LVGL test lock should not be poisoned")
}

#[cfg(feature = "native-lvgl")]
#[test]
fn open_default_facade_with_missing_explicit_source_returns_contextual_error() {
    let _guard = native_lvgl_test_guard();
    let error = match open_default_facade(Some(Path::new("missing-lvgl-source"))) {
        Ok(_) => panic!("missing LVGL source must fail"),
        Err(error) => error,
    };

    assert!(error.to_string().contains("LVGL source"));
}

#[cfg(feature = "native-lvgl")]
#[test]
fn open_default_facade_without_runtime_source_configuration_opens_backend() {
    let _guard = native_lvgl_test_guard();
    open_default_facade(None).expect("native backend should open without runtime source config");
}
