use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use crate::input::InputAction;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum UiScreen {
    Hub,
    Listen,
    Playlists,
    NowPlaying,
    Ask,
    Call,
    IncomingCall,
    OutgoingCall,
    InCall,
    Power,
    Loading,
    Error,
}

impl UiScreen {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Hub => "hub",
            Self::Listen => "listen",
            Self::Playlists => "playlists",
            Self::NowPlaying => "now_playing",
            Self::Ask => "ask",
            Self::Call => "call",
            Self::IncomingCall => "incoming_call",
            Self::OutgoingCall => "outgoing_call",
            Self::InCall => "in_call",
            Self::Power => "power",
            Self::Loading => "loading",
            Self::Error => "error",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UiIntent {
    pub domain: String,
    pub action: String,
    #[serde(default = "empty_payload")]
    pub payload: Value,
}

impl UiIntent {
    pub fn new(domain: impl Into<String>, action: impl Into<String>) -> Self {
        Self {
            domain: domain.into(),
            action: action.into(),
            payload: empty_payload(),
        }
    }

    pub fn with_payload(
        domain: impl Into<String>,
        action: impl Into<String>,
        payload: Value,
    ) -> Self {
        Self {
            domain: domain.into(),
            action: action.into(),
            payload,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RuntimeSnapshot {
    #[serde(default = "default_app_state")]
    pub app_state: String,
    #[serde(default)]
    pub hub: HubRuntimeSnapshot,
    #[serde(default)]
    pub music: MusicRuntimeSnapshot,
    #[serde(default)]
    pub call: CallRuntimeSnapshot,
    #[serde(default)]
    pub voice: VoiceRuntimeSnapshot,
    #[serde(default)]
    pub power: PowerRuntimeSnapshot,
    #[serde(default)]
    pub network: NetworkRuntimeSnapshot,
    #[serde(default)]
    pub overlay: OverlayRuntimeSnapshot,
}

impl Default for RuntimeSnapshot {
    fn default() -> Self {
        Self {
            app_state: default_app_state(),
            hub: HubRuntimeSnapshot::default(),
            music: MusicRuntimeSnapshot::default(),
            call: CallRuntimeSnapshot::default(),
            voice: VoiceRuntimeSnapshot::default(),
            power: PowerRuntimeSnapshot::default(),
            network: NetworkRuntimeSnapshot::default(),
            overlay: OverlayRuntimeSnapshot::default(),
        }
    }
}

impl RuntimeSnapshot {
    pub fn from_payload(payload: &Value) -> Result<Self> {
        serde_json::from_value(payload.clone()).context("decoding UI runtime snapshot")
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HubRuntimeSnapshot {
    #[serde(default = "default_hub_cards")]
    pub cards: Vec<HubCardSnapshot>,
}

impl Default for HubRuntimeSnapshot {
    fn default() -> Self {
        Self {
            cards: default_hub_cards(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HubCardSnapshot {
    pub key: String,
    pub title: String,
    #[serde(default)]
    pub subtitle: String,
    #[serde(default = "default_hub_accent")]
    pub accent: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MusicRuntimeSnapshot {
    #[serde(default)]
    pub playing: bool,
    #[serde(default)]
    pub paused: bool,
    #[serde(default = "default_music_title")]
    pub title: String,
    #[serde(default)]
    pub artist: String,
    #[serde(default)]
    pub progress_permille: i32,
    #[serde(default)]
    pub playlists: Vec<ListItemSnapshot>,
    #[serde(default)]
    pub recent_tracks: Vec<ListItemSnapshot>,
}

impl Default for MusicRuntimeSnapshot {
    fn default() -> Self {
        Self {
            playing: false,
            paused: false,
            title: default_music_title(),
            artist: String::new(),
            progress_permille: 0,
            playlists: Vec::new(),
            recent_tracks: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CallRuntimeSnapshot {
    #[serde(default = "default_call_state")]
    pub state: String,
    #[serde(default)]
    pub peer_name: String,
    #[serde(default)]
    pub peer_address: String,
    #[serde(default)]
    pub duration_text: String,
    #[serde(default)]
    pub muted: bool,
    #[serde(default)]
    pub contacts: Vec<ListItemSnapshot>,
}

impl Default for CallRuntimeSnapshot {
    fn default() -> Self {
        Self {
            state: default_call_state(),
            peer_name: String::new(),
            peer_address: String::new(),
            duration_text: String::new(),
            muted: false,
            contacts: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VoiceRuntimeSnapshot {
    #[serde(default = "default_voice_phase")]
    pub phase: String,
    #[serde(default = "default_voice_headline")]
    pub headline: String,
    #[serde(default = "default_voice_body")]
    pub body: String,
    #[serde(default)]
    pub capture_in_flight: bool,
    #[serde(default)]
    pub ptt_active: bool,
}

impl Default for VoiceRuntimeSnapshot {
    fn default() -> Self {
        Self {
            phase: default_voice_phase(),
            headline: default_voice_headline(),
            body: default_voice_body(),
            capture_in_flight: false,
            ptt_active: false,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PowerRuntimeSnapshot {
    #[serde(default = "default_battery_percent")]
    pub battery_percent: i32,
    #[serde(default)]
    pub charging: bool,
    #[serde(default)]
    pub power_available: bool,
    #[serde(default)]
    pub rows: Vec<String>,
}

impl Default for PowerRuntimeSnapshot {
    fn default() -> Self {
        Self {
            battery_percent: default_battery_percent(),
            charging: false,
            power_available: true,
            rows: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NetworkRuntimeSnapshot {
    #[serde(default)]
    pub enabled: bool,
    #[serde(default)]
    pub connected: bool,
    #[serde(default)]
    pub signal_strength: i32,
    #[serde(default)]
    pub gps_has_fix: bool,
}

impl Default for NetworkRuntimeSnapshot {
    fn default() -> Self {
        Self {
            enabled: false,
            connected: false,
            signal_strength: 0,
            gps_has_fix: false,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct OverlayRuntimeSnapshot {
    #[serde(default)]
    pub loading: bool,
    #[serde(default)]
    pub error: String,
    #[serde(default)]
    pub message: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ListItemSnapshot {
    pub id: String,
    pub title: String,
    #[serde(default)]
    pub subtitle: String,
    #[serde(default)]
    pub icon_key: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UiView {
    pub screen: UiScreen,
    pub title: String,
    pub subtitle: String,
    pub footer: String,
    pub items: Vec<ListItemSnapshot>,
    pub focus_index: usize,
}

#[derive(Debug, Clone)]
pub struct UiRuntime {
    snapshot: RuntimeSnapshot,
    active_screen: UiScreen,
    screen_stack: Vec<UiScreen>,
    focus_index: usize,
    intents: Vec<UiIntent>,
    dirty: bool,
}

impl Default for UiRuntime {
    fn default() -> Self {
        Self {
            snapshot: RuntimeSnapshot::default(),
            active_screen: UiScreen::Hub,
            screen_stack: Vec::new(),
            focus_index: 0,
            intents: Vec::new(),
            dirty: true,
        }
    }
}

impl UiRuntime {
    pub fn apply_snapshot(&mut self, snapshot: RuntimeSnapshot) {
        self.snapshot = snapshot;
        self.apply_runtime_preemption();
        self.clamp_focus();
        self.dirty = true;
    }

    pub fn handle_input(&mut self, action: InputAction) {
        match action {
            InputAction::Advance => self.advance_focus(),
            InputAction::Select => self.select_focused(),
            InputAction::Back => self.go_back_or_emit(),
            InputAction::PttPress => self.intents.push(UiIntent::new("voice", "capture_start")),
            InputAction::PttRelease => self.intents.push(UiIntent::new("voice", "capture_stop")),
        }
        self.clamp_focus();
        self.dirty = true;
    }

    pub fn active_screen(&self) -> UiScreen {
        self.active_screen
    }

    pub fn snapshot(&self) -> &RuntimeSnapshot {
        &self.snapshot
    }

    pub fn stack(&self) -> &[UiScreen] {
        &self.screen_stack
    }

    pub fn focus_index(&self) -> usize {
        self.focus_index
    }

    pub fn is_dirty(&self) -> bool {
        self.dirty
    }

    pub fn mark_clean(&mut self) {
        self.dirty = false;
    }

    pub fn take_intents(&mut self) -> Vec<UiIntent> {
        std::mem::take(&mut self.intents)
    }

    pub fn active_view(&self) -> UiView {
        match self.active_screen {
            UiScreen::Hub => {
                let cards = self.snapshot.hub.cards.clone();
                let focused = cards.get(self.focus_index);
                UiView {
                    screen: UiScreen::Hub,
                    title: focused
                        .map(|card| card.title.clone())
                        .unwrap_or_else(|| "Listen".to_string()),
                    subtitle: focused
                        .map(|card| card.subtitle.clone())
                        .unwrap_or_else(String::new),
                    footer: "Tap = Next | 2x Tap = Open".to_string(),
                    items: cards
                        .iter()
                        .map(|card| ListItemSnapshot {
                            id: card.key.clone(),
                            title: card.title.clone(),
                            subtitle: card.subtitle.clone(),
                            icon_key: card.key.clone(),
                        })
                        .collect(),
                    focus_index: self.focus_index,
                }
            }
            UiScreen::Listen => UiView {
                screen: UiScreen::Listen,
                title: "Listen".to_string(),
                subtitle: "Music".to_string(),
                footer: "Tap = Next | 2x Tap = Open | Hold = Back".to_string(),
                items: self.listen_items(),
                focus_index: self.focus_index,
            },
            UiScreen::Playlists => UiView {
                screen: UiScreen::Playlists,
                title: "Playlists".to_string(),
                subtitle: String::new(),
                footer: "Tap = Next | 2x Tap = Play | Hold = Back".to_string(),
                items: self.snapshot.music.playlists.clone(),
                focus_index: self.focus_index,
            },
            UiScreen::NowPlaying => UiView {
                screen: UiScreen::NowPlaying,
                title: self.snapshot.music.title.clone(),
                subtitle: self.snapshot.music.artist.clone(),
                footer: "Tap = Next | 2x Tap = Play/Pause | Hold = Back".to_string(),
                items: Vec::new(),
                focus_index: self.focus_index,
            },
            UiScreen::Ask => UiView {
                screen: UiScreen::Ask,
                title: self.snapshot.voice.headline.clone(),
                subtitle: self.snapshot.voice.body.clone(),
                footer: "2x Tap = Ask | Hold = Back".to_string(),
                items: Vec::new(),
                focus_index: self.focus_index,
            },
            UiScreen::Call => UiView {
                screen: UiScreen::Call,
                title: "Talk".to_string(),
                subtitle: "Contacts".to_string(),
                footer: "Tap = Next | 2x Tap = Call | Hold = Back".to_string(),
                items: self.snapshot.call.contacts.clone(),
                focus_index: self.focus_index,
            },
            UiScreen::IncomingCall => UiView {
                screen: UiScreen::IncomingCall,
                title: self.call_peer_name(),
                subtitle: self.snapshot.call.peer_address.clone(),
                footer: "2x Tap = Answer | Hold = Reject".to_string(),
                items: Vec::new(),
                focus_index: self.focus_index,
            },
            UiScreen::OutgoingCall => UiView {
                screen: UiScreen::OutgoingCall,
                title: self.call_peer_name(),
                subtitle: self.snapshot.call.peer_address.clone(),
                footer: "Hold = Cancel".to_string(),
                items: Vec::new(),
                focus_index: self.focus_index,
            },
            UiScreen::InCall => UiView {
                screen: UiScreen::InCall,
                title: self.call_peer_name(),
                subtitle: self.snapshot.call.duration_text.clone(),
                footer: "Tap = Mute | Hold = Hang Up".to_string(),
                items: Vec::new(),
                focus_index: self.focus_index,
            },
            UiScreen::Power => UiView {
                screen: UiScreen::Power,
                title: "Status".to_string(),
                subtitle: format!("Battery {}%", self.snapshot.power.battery_percent),
                footer: "Tap = Next | Hold = Back".to_string(),
                items: self
                    .snapshot
                    .power
                    .rows
                    .iter()
                    .enumerate()
                    .map(|(index, row)| ListItemSnapshot {
                        id: format!("power-{index}"),
                        title: row.clone(),
                        subtitle: String::new(),
                        icon_key: "battery".to_string(),
                    })
                    .collect(),
                focus_index: self.focus_index,
            },
            UiScreen::Loading => UiView {
                screen: UiScreen::Loading,
                title: "Loading".to_string(),
                subtitle: self.snapshot.overlay.message.clone(),
                footer: String::new(),
                items: Vec::new(),
                focus_index: 0,
            },
            UiScreen::Error => UiView {
                screen: UiScreen::Error,
                title: "Error".to_string(),
                subtitle: self.snapshot.overlay.error.clone(),
                footer: "Hold = Back".to_string(),
                items: Vec::new(),
                focus_index: 0,
            },
        }
    }

    fn apply_runtime_preemption(&mut self) {
        let desired = if !self.snapshot.overlay.error.trim().is_empty() {
            Some(UiScreen::Error)
        } else if self.snapshot.overlay.loading {
            Some(UiScreen::Loading)
        } else {
            match self.snapshot.call.state.as_str() {
                "incoming" => Some(UiScreen::IncomingCall),
                "outgoing" => Some(UiScreen::OutgoingCall),
                "active" => Some(UiScreen::InCall),
                _ => None,
            }
        };

        if let Some(screen) = desired {
            if self.active_screen != screen {
                self.push_screen(screen);
            }
            return;
        }

        if matches!(
            self.active_screen,
            UiScreen::IncomingCall | UiScreen::OutgoingCall | UiScreen::InCall
        ) && self.snapshot.call.state == "idle"
        {
            self.pop_until_non_call();
        }
    }

    fn advance_focus(&mut self) {
        let count = self.focus_count();
        if count == 0 {
            return;
        }
        self.focus_index = (self.focus_index + 1) % count;
    }

    fn select_focused(&mut self) {
        match self.active_screen {
            UiScreen::Hub => match self.focus_index {
                0 => self.push_screen(UiScreen::Listen),
                1 => self.push_screen(UiScreen::Call),
                2 => self.push_screen(UiScreen::Ask),
                _ => self.push_screen(UiScreen::Power),
            },
            UiScreen::Listen => match self.focus_index {
                0 => self.push_screen(UiScreen::NowPlaying),
                1 => self.push_screen(UiScreen::Playlists),
                _ => {
                    self.intents.push(UiIntent::new("music", "shuffle_all"));
                    self.push_screen(UiScreen::NowPlaying);
                }
            },
            UiScreen::Playlists => {
                if let Some(item) = self.snapshot.music.playlists.get(self.focus_index) {
                    self.intents.push(UiIntent::with_payload(
                        "music",
                        "load_playlist",
                        json!({"id": item.id, "title": item.title}),
                    ));
                    self.push_screen(UiScreen::NowPlaying);
                }
            }
            UiScreen::NowPlaying => self.intents.push(UiIntent::new("music", "play_pause")),
            UiScreen::Ask => self.intents.push(UiIntent::new("voice", "capture_toggle")),
            UiScreen::Call => {
                if let Some(item) = self.snapshot.call.contacts.get(self.focus_index) {
                    self.intents.push(UiIntent::with_payload(
                        "call",
                        "start",
                        json!({"id": item.id, "name": item.title}),
                    ));
                }
            }
            UiScreen::IncomingCall => self.intents.push(UiIntent::new("call", "answer")),
            UiScreen::InCall => self.intents.push(UiIntent::new("call", "toggle_mute")),
            _ => {}
        }
    }

    fn go_back_or_emit(&mut self) {
        match self.active_screen {
            UiScreen::IncomingCall => self.intents.push(UiIntent::new("call", "reject")),
            UiScreen::OutgoingCall | UiScreen::InCall => {
                self.intents.push(UiIntent::new("call", "hangup"))
            }
            UiScreen::Loading | UiScreen::Error => self.pop_screen_or_hub(),
            UiScreen::Hub => {}
            _ => self.pop_screen_or_hub(),
        }
    }

    fn push_screen(&mut self, screen: UiScreen) {
        if self.active_screen != screen {
            self.screen_stack.push(self.active_screen);
        }
        self.active_screen = screen;
        self.focus_index = 0;
    }

    fn pop_screen_or_hub(&mut self) {
        self.active_screen = self.screen_stack.pop().unwrap_or(UiScreen::Hub);
        self.focus_index = 0;
    }

    fn pop_until_non_call(&mut self) {
        while matches!(
            self.active_screen,
            UiScreen::IncomingCall | UiScreen::OutgoingCall | UiScreen::InCall
        ) {
            self.active_screen = self.screen_stack.pop().unwrap_or(UiScreen::Hub);
        }
        self.focus_index = 0;
    }

    fn clamp_focus(&mut self) {
        let count = self.focus_count();
        if count == 0 {
            self.focus_index = 0;
        } else if self.focus_index >= count {
            self.focus_index = count - 1;
        }
    }

    fn focus_count(&self) -> usize {
        match self.active_screen {
            UiScreen::Hub => self.snapshot.hub.cards.len().max(1),
            UiScreen::Listen => self.listen_items().len(),
            UiScreen::Playlists => self.snapshot.music.playlists.len(),
            UiScreen::Call => self.snapshot.call.contacts.len(),
            UiScreen::Power => self.snapshot.power.rows.len().max(1),
            _ => 0,
        }
    }

    fn listen_items(&self) -> Vec<ListItemSnapshot> {
        vec![
            ListItemSnapshot {
                id: "now_playing".to_string(),
                title: "Now Playing".to_string(),
                subtitle: self.snapshot.music.title.clone(),
                icon_key: "headphones".to_string(),
            },
            ListItemSnapshot {
                id: "playlists".to_string(),
                title: "Playlists".to_string(),
                subtitle: format!("{} saved", self.snapshot.music.playlists.len()),
                icon_key: "list".to_string(),
            },
            ListItemSnapshot {
                id: "shuffle".to_string(),
                title: "Shuffle".to_string(),
                subtitle: "All music".to_string(),
                icon_key: "shuffle".to_string(),
            },
        ]
    }

    fn call_peer_name(&self) -> String {
        if self.snapshot.call.peer_name.trim().is_empty() {
            "Unknown".to_string()
        } else {
            self.snapshot.call.peer_name.clone()
        }
    }
}

fn default_app_state() -> String {
    "hub".to_string()
}

fn default_call_state() -> String {
    "idle".to_string()
}

fn default_voice_phase() -> String {
    "idle".to_string()
}

fn default_voice_headline() -> String {
    "Ask".to_string()
}

fn default_voice_body() -> String {
    "Ask me anything...".to_string()
}

fn default_music_title() -> String {
    "Nothing Playing".to_string()
}

fn default_battery_percent() -> i32 {
    100
}

fn default_hub_accent() -> u32 {
    0x00FF88
}

fn default_hub_cards() -> Vec<HubCardSnapshot> {
    vec![
        HubCardSnapshot {
            key: "listen".to_string(),
            title: "Listen".to_string(),
            subtitle: String::new(),
            accent: 0x00FF88,
        },
        HubCardSnapshot {
            key: "talk".to_string(),
            title: "Talk".to_string(),
            subtitle: "Ready".to_string(),
            accent: 0x00D4FF,
        },
        HubCardSnapshot {
            key: "ask".to_string(),
            title: "Ask".to_string(),
            subtitle: "Voice".to_string(),
            accent: 0x9F7AEA,
        },
        HubCardSnapshot {
            key: "setup".to_string(),
            title: "Setup".to_string(),
            subtitle: "Status".to_string(),
            accent: 0xF6AD55,
        },
    ]
}

fn empty_payload() -> Value {
    json!({})
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::input::InputAction;

    #[test]
    fn default_snapshot_starts_on_hub() {
        let mut runtime = UiRuntime::default();

        runtime.apply_snapshot(RuntimeSnapshot::default());

        assert_eq!(runtime.active_screen(), UiScreen::Hub);
        assert_eq!(runtime.focus_index(), 0);
        assert!(runtime.take_intents().is_empty());
    }

    #[test]
    fn hub_advance_cycles_focus_through_cards() {
        let mut runtime = UiRuntime::default();
        runtime.apply_snapshot(RuntimeSnapshot::default());

        runtime.handle_input(InputAction::Advance);
        runtime.handle_input(InputAction::Advance);
        runtime.handle_input(InputAction::Advance);
        runtime.handle_input(InputAction::Advance);

        assert_eq!(runtime.active_screen(), UiScreen::Hub);
        assert_eq!(runtime.focus_index(), 0);
    }

    #[test]
    fn hub_select_pushes_listen_and_back_returns_home() {
        let mut runtime = UiRuntime::default();
        runtime.apply_snapshot(RuntimeSnapshot::default());

        runtime.handle_input(InputAction::Select);
        assert_eq!(runtime.active_screen(), UiScreen::Listen);
        assert_eq!(runtime.stack(), &[UiScreen::Hub]);

        runtime.handle_input(InputAction::Back);
        assert_eq!(runtime.active_screen(), UiScreen::Hub);
        assert!(runtime.stack().is_empty());
    }

    #[test]
    fn incoming_call_snapshot_preempts_current_screen() {
        let mut runtime = UiRuntime::default();
        runtime.apply_snapshot(RuntimeSnapshot::default());
        runtime.handle_input(InputAction::Select);
        assert_eq!(runtime.active_screen(), UiScreen::Listen);

        let mut snapshot = RuntimeSnapshot::default();
        snapshot.call.state = "incoming".to_string();
        snapshot.call.peer_name = "Mama".to_string();
        snapshot.call.peer_address = "sip:mama@example.com".to_string();
        runtime.apply_snapshot(snapshot);

        assert_eq!(runtime.active_screen(), UiScreen::IncomingCall);
        assert_eq!(runtime.active_view().title, "Mama");
    }

    #[test]
    fn incoming_call_select_emits_answer_intent() {
        let mut runtime = UiRuntime::default();
        let mut snapshot = RuntimeSnapshot::default();
        snapshot.call.state = "incoming".to_string();
        runtime.apply_snapshot(snapshot);

        runtime.handle_input(InputAction::Select);

        assert_eq!(
            runtime.take_intents(),
            vec![UiIntent::new("call", "answer")]
        );
        assert_eq!(runtime.active_screen(), UiScreen::IncomingCall);
    }
}
