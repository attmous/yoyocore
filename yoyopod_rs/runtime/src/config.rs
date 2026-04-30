use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RuntimeConfig {
    pub ui: UiConfig,
    pub media: MediaRuntimeConfig,
    pub voip: VoipRuntimeConfig,
    pub worker_paths: WorkerPaths,
    pub pid_file: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct UiConfig {
    pub hardware: String,
    pub brightness: f64,
    pub renderer: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MediaRuntimeConfig {
    pub music_dir: String,
    pub mpv_socket: String,
    pub mpv_binary: String,
    pub alsa_device: String,
    pub default_volume: i32,
    pub recent_tracks_file: String,
    pub remote_cache_dir: String,
    pub remote_cache_max_bytes: u64,
    pub auto_resume_after_call: bool,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct VoipRuntimeConfig {
    pub sip_server: String,
    pub sip_username: String,
    pub sip_password: String,
    pub sip_password_ha1: String,
    pub sip_identity: String,
    pub factory_config_path: String,
    pub transport: String,
    pub stun_server: String,
    pub conference_factory_uri: String,
    pub file_transfer_server_url: String,
    pub lime_server_url: String,
    pub iterate_interval_ms: u64,
    pub message_store_dir: String,
    pub voice_note_store_dir: String,
    pub auto_download_incoming_voice_recordings: bool,
    pub playback_dev_id: String,
    pub ringer_dev_id: String,
    pub capture_dev_id: String,
    pub media_dev_id: String,
    pub mic_gain: i32,
    pub output_volume: i32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WorkerPaths {
    pub ui: String,
    pub media: String,
    pub voip: String,
}

#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("failed to read config file {path}: {source}")]
    Read {
        path: String,
        #[source]
        source: std::io::Error,
    },
    #[error("failed to parse YAML config file {path}: {source}")]
    Parse {
        path: String,
        #[source]
        source: serde_yaml::Error,
    },
}

impl RuntimeConfig {
    pub fn load(config_dir: impl AsRef<Path>) -> Result<Self, ConfigError> {
        let config_dir = config_dir.as_ref();
        let app = read_yaml(config_dir.join("app/core.yaml"))?;
        let hardware = read_yaml(config_dir.join("device/hardware.yaml"))?;
        let music = read_yaml(config_dir.join("audio/music.yaml"))?;
        let calling = read_yaml(config_dir.join("communication/calling.yaml"))?;
        let messaging = read_yaml(config_dir.join("communication/messaging.yaml"))?;
        let secrets = read_yaml(config_dir.join("communication/calling.secrets.yaml"))?;

        let default_volume = int_at_env(
            &music,
            &["audio", "default_volume"],
            100,
            "YOYOPOD_DEFAULT_VOLUME",
        );

        Ok(Self {
            ui: UiConfig {
                hardware: string_at_env(
                    &hardware,
                    &["display", "hardware"],
                    "whisplay",
                    "YOYOPOD_DISPLAY",
                ),
                brightness: (int_at(&hardware, &["display", "brightness"], 80) as f64 / 100.0)
                    .clamp(0.0, 1.0),
                renderer: string_at_env(
                    &hardware,
                    &["display", "whisplay_renderer"],
                    "lvgl",
                    "YOYOPOD_WHISPLAY_RENDERER",
                ),
            },
            media: MediaRuntimeConfig {
                music_dir: string_at_env(
                    &music,
                    &["audio", "music_dir"],
                    "/home/pi/Music",
                    "YOYOPOD_MUSIC_DIR",
                ),
                mpv_socket: string_at_env(
                    &music,
                    &["audio", "mpv_socket"],
                    "/tmp/yoyopod-mpv.sock",
                    "YOYOPOD_MPV_SOCKET",
                ),
                mpv_binary: string_at_env(
                    &music,
                    &["audio", "mpv_binary"],
                    "mpv",
                    "YOYOPOD_MPV_BINARY",
                ),
                alsa_device: string_at_env(
                    &hardware,
                    &["media_audio", "alsa_device"],
                    "default",
                    "YOYOPOD_ALSA_DEVICE",
                ),
                default_volume,
                recent_tracks_file: string_at_env(
                    &music,
                    &["audio", "recent_tracks_file"],
                    "data/media/recent_tracks.json",
                    "YOYOPOD_RECENT_TRACKS_FILE",
                ),
                remote_cache_dir: string_at_env(
                    &music,
                    &["audio", "remote_cache_dir"],
                    "data/media/remote_cache",
                    "YOYOPOD_REMOTE_CACHE_DIR",
                ),
                remote_cache_max_bytes: uint_at_env(
                    &music,
                    &["audio", "remote_cache_max_bytes"],
                    536_870_912,
                    "YOYOPOD_REMOTE_CACHE_MAX_BYTES",
                ),
                auto_resume_after_call: bool_at_env(
                    &music,
                    &["audio", "auto_resume_after_call"],
                    true,
                    "YOYOPOD_AUTO_RESUME_AFTER_CALL",
                ),
            },
            voip: VoipRuntimeConfig {
                sip_server: string_at_env(
                    &calling,
                    &["calling", "account", "sip_server"],
                    "sip.linphone.org",
                    "YOYOPOD_SIP_SERVER",
                ),
                sip_username: string_at_env(
                    &calling,
                    &["calling", "account", "sip_username"],
                    "",
                    "YOYOPOD_SIP_USERNAME",
                ),
                sip_password: string_at_env(
                    &secrets,
                    &["secrets", "sip_password"],
                    "",
                    "YOYOPOD_SIP_PASSWORD",
                ),
                sip_password_ha1: string_at_env(
                    &secrets,
                    &["secrets", "sip_password_ha1"],
                    "",
                    "YOYOPOD_SIP_PASSWORD_HA1",
                ),
                sip_identity: string_at_env(
                    &calling,
                    &["calling", "account", "sip_identity"],
                    "",
                    "YOYOPOD_SIP_IDENTITY",
                ),
                factory_config_path: string_at_env(
                    &calling,
                    &["integrations", "liblinphone_factory_config_path"],
                    "config/communication/integrations/liblinphone_factory.conf",
                    "YOYOPOD_LIBLINPHONE_FACTORY_CONFIG",
                ),
                transport: string_at_env(
                    &calling,
                    &["calling", "account", "transport"],
                    "tcp",
                    "YOYOPOD_SIP_TRANSPORT",
                ),
                stun_server: string_at_env(
                    &calling,
                    &["calling", "network", "stun_server"],
                    "stun.linphone.org",
                    "YOYOPOD_STUN_SERVER",
                ),
                conference_factory_uri: string_at_env(
                    &messaging,
                    &["messaging", "conference_factory_uri"],
                    "",
                    "YOYOPOD_CONFERENCE_FACTORY_URI",
                ),
                file_transfer_server_url: string_at_env(
                    &messaging,
                    &["messaging", "file_transfer_server_url"],
                    "https://files.linphone.org/lft.php",
                    "YOYOPOD_FILE_TRANSFER_SERVER_URL",
                ),
                lime_server_url: string_at_env(
                    &messaging,
                    &["messaging", "lime_server_url"],
                    "https://lime.linphone.org/lime-server/lime-server.php",
                    "YOYOPOD_LIME_SERVER_URL",
                ),
                iterate_interval_ms: uint_at_env(
                    &messaging,
                    &["messaging", "iterate_interval_ms"],
                    20,
                    "YOYOPOD_VOIP_ITERATE_INTERVAL_MS",
                ),
                message_store_dir: string_at_env(
                    &messaging,
                    &["messaging", "message_store_dir"],
                    "data/communication/messages",
                    "YOYOPOD_MESSAGE_STORE_DIR",
                ),
                voice_note_store_dir: string_at_env(
                    &messaging,
                    &["messaging", "voice_note_store_dir"],
                    "data/communication/voice_notes",
                    "YOYOPOD_VOICE_NOTE_STORE_DIR",
                ),
                auto_download_incoming_voice_recordings: bool_at_env(
                    &messaging,
                    &["messaging", "auto_download_incoming_voice_recordings"],
                    true,
                    "YOYOPOD_AUTO_DOWNLOAD_INCOMING_VOICE_RECORDINGS",
                ),
                playback_dev_id: string_at_env(
                    &hardware,
                    &["communication_audio", "playback_device_id"],
                    "ALSA: wm8960-soundcard",
                    "YOYOPOD_PLAYBACK_DEVICE",
                ),
                ringer_dev_id: string_at_env(
                    &hardware,
                    &["communication_audio", "ringer_device_id"],
                    "ALSA: wm8960-soundcard",
                    "YOYOPOD_RINGER_DEVICE",
                ),
                capture_dev_id: string_at_env(
                    &hardware,
                    &["communication_audio", "capture_device_id"],
                    "ALSA: wm8960-soundcard",
                    "YOYOPOD_CAPTURE_DEVICE",
                ),
                media_dev_id: string_at_env(
                    &hardware,
                    &["communication_audio", "media_device_id"],
                    "ALSA: wm8960-soundcard",
                    "YOYOPOD_MEDIA_DEVICE",
                ),
                mic_gain: int_at(&hardware, &["communication_audio", "mic_gain"], 80),
                output_volume: default_volume,
            },
            worker_paths: WorkerPaths {
                ui: env_or_default(
                    "YOYOPOD_RUST_UI_HOST_WORKER",
                    "yoyopod_rs/ui-host/build/yoyopod-ui-host",
                ),
                media: env_or_default(
                    "YOYOPOD_RUST_MEDIA_HOST_WORKER",
                    "yoyopod_rs/media-host/build/yoyopod-media-host",
                ),
                voip: env_or_default(
                    "YOYOPOD_RUST_VOIP_HOST_WORKER",
                    "yoyopod_rs/voip-host/build/yoyopod-voip-host",
                ),
            },
            pid_file: string_at_env(
                &app,
                &["logging", "pid_file"],
                "/tmp/yoyopod.pid",
                "YOYOPOD_PID_FILE",
            ),
        })
    }
}

impl MediaRuntimeConfig {
    pub fn to_worker_payload(&self) -> Value {
        json!({
            "music_dir": self.music_dir,
            "mpv_socket": self.mpv_socket,
            "mpv_binary": self.mpv_binary,
            "alsa_device": self.alsa_device,
            "default_volume": self.default_volume,
            "recent_tracks_file": self.recent_tracks_file,
            "remote_cache_dir": self.remote_cache_dir,
            "remote_cache_max_bytes": self.remote_cache_max_bytes,
        })
    }
}

impl VoipRuntimeConfig {
    pub fn to_worker_payload(&self) -> Value {
        json!(self)
    }
}

fn read_yaml(path: PathBuf) -> Result<Value, ConfigError> {
    if !path.exists() {
        return Ok(json!({}));
    }

    let text = fs::read_to_string(&path).map_err(|source| ConfigError::Read {
        path: path.display().to_string(),
        source,
    })?;
    let value: serde_yaml::Value =
        serde_yaml::from_str(&text).map_err(|source| ConfigError::Parse {
            path: path.display().to_string(),
            source,
        })?;

    Ok(serde_json::to_value(value).unwrap_or_else(|_| json!({})))
}

fn at_path<'a>(value: &'a Value, path: &[&str]) -> Option<&'a Value> {
    let mut current = value;
    for segment in path {
        current = current.get(*segment)?;
    }
    Some(current)
}

fn string_at_env(value: &Value, path: &[&str], default: &str, env: &str) -> String {
    env_string(env).unwrap_or_else(|| string_at(value, path, default))
}

fn int_at_env(value: &Value, path: &[&str], default: i32, env: &str) -> i32 {
    env_string(env)
        .and_then(|text| text.parse::<i32>().ok())
        .unwrap_or_else(|| int_at(value, path, default))
}

fn uint_at_env(value: &Value, path: &[&str], default: u64, env: &str) -> u64 {
    env_string(env)
        .and_then(|text| text.parse::<u64>().ok())
        .unwrap_or_else(|| uint_at(value, path, default))
}

fn bool_at_env(value: &Value, path: &[&str], default: bool, env: &str) -> bool {
    env_string(env)
        .and_then(|text| parse_bool(&text))
        .unwrap_or_else(|| bool_at(value, path, default))
}

fn string_at(value: &Value, path: &[&str], default: &str) -> String {
    at_path(value, path)
        .and_then(Value::as_str)
        .filter(|text| !text.trim().is_empty())
        .unwrap_or(default)
        .to_string()
}

fn int_at(value: &Value, path: &[&str], default: i32) -> i32 {
    at_path(value, path)
        .and_then(|value| {
            value
                .as_i64()
                .and_then(|number| i32::try_from(number).ok())
                .or_else(|| value.as_str()?.trim().parse::<i32>().ok())
        })
        .unwrap_or(default)
}

fn uint_at(value: &Value, path: &[&str], default: u64) -> u64 {
    at_path(value, path)
        .and_then(|value| {
            value
                .as_u64()
                .or_else(|| value.as_str()?.trim().parse::<u64>().ok())
        })
        .unwrap_or(default)
}

fn bool_at(value: &Value, path: &[&str], default: bool) -> bool {
    at_path(value, path)
        .and_then(|value| value.as_bool().or_else(|| parse_bool(value.as_str()?)))
        .unwrap_or(default)
}

fn parse_bool(value: &str) -> Option<bool> {
    match value.trim().to_ascii_lowercase().as_str() {
        "1" | "true" | "yes" | "on" => Some(true),
        "0" | "false" | "no" | "off" => Some(false),
        _ => None,
    }
}

fn env_string(name: &str) -> Option<String> {
    std::env::var(name)
        .ok()
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
}

fn env_or_default(name: &str, default: &str) -> String {
    env_string(name).unwrap_or_else(|| default.to_string())
}
