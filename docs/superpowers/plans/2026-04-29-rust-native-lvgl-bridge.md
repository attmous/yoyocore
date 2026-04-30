# Rust-Native LVGL Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Rust UI host's YoYoPod-specific LVGL shim dependency with a Rust-owned typed renderer that derives screen models from generic runtime snapshots and talks directly to upstream LVGL.

**Architecture:** Keep Python generic: it continues to send `ui.runtime_snapshot`, `ui.tick`, and intent-driving inputs only. Inside `yoyopod_rs/ui-host/`, split routing/model derivation from rendering, add typed screen models plus persistent controller logic, then add a direct upstream-LVGL backend under a narrow `lvgl/` boundary and remove `lvgl_bridge.rs` from the Rust host path.

**Tech Stack:** Rust 2021, Cargo workspace at `yoyopod_rs/`, Bazel `rules_rust` test surface, upstream LVGL 9.5 C library, manual Rust FFI, `cmake` build helper for Cargo, `serde`, `serde_json`, `anyhow`, Python 3.12, pytest, Raspberry Pi Zero 2W Whisplay hardware.

---

## Scope Check

This plan covers one subsystem: the Rust UI host render boundary. It does not move music, VoIP, voice, power, network, or Python runtime ownership into Rust. It also does not replace LVGL with another toolkit.

## Required Execution Rules

- Do not build Rust on the Pi Zero 2W.
- For target validation, use the GitHub Actions UI-host artifact for the exact commit under test.
- Before every commit and every push, run:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
```

- During implementation, also run the Rust-specific commands that match the touched surface:

```bash
cargo fmt --manifest-path yoyopod_rs/Cargo.toml
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host --locked
bazel test //yoyopod_rs/ui-host/...
```

- Once the direct LVGL backend lands, also run:

```bash
$env:YOYOPOD_LVGL_SOURCE_DIR = "C:\\path\\to\\lvgl"
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host --features native-lvgl --locked
cargo build --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host --release --features "whisplay-hardware,native-lvgl" --locked
```

## File Structure

Create or modify these files during the full implementation:

- Create: `yoyopod_rs/ui-host/src/screens/models.rs` - typed screen models derived from generic runtime facts.
- Modify: `yoyopod_rs/ui-host/src/screens/mod.rs` - export screen model types.
- Modify: `yoyopod_rs/ui-host/src/screens/hub.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/listen.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/music.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/ask.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/talk.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/call.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/power.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/overlay.rs`
- Modify: `yoyopod_rs/ui-host/src/runtime/state_machine.rs` - expose typed active screen model.
- Modify: `yoyopod_rs/ui-host/src/runtime/mod.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/mod.rs` - new LVGL boundary root.
- Create: `yoyopod_rs/ui-host/src/lvgl/primitives.rs` - widget ids and facade trait.
- Create: `yoyopod_rs/ui-host/src/lvgl/chrome.rs` - shared status/footer/apply helpers.
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/mod.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/hub.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/list.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/ask.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/call.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/power.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/overlay.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/sys.rs` - raw upstream LVGL FFI.
- Create: `yoyopod_rs/ui-host/src/lvgl/native_backend.rs` - direct LVGL runtime/display backend.
- Modify: `yoyopod_rs/ui-host/src/render/lvgl.rs` - persistent renderer over typed screen models.
- Modify: `yoyopod_rs/ui-host/src/render/framebuffer.rs` - fallback renderer for typed screen models.
- Modify: `yoyopod_rs/ui-host/src/render/mod.rs`
- Modify: `yoyopod_rs/ui-host/src/worker.rs` - render from `ScreenModel`, remove shim commands.
- Modify: `yoyopod_rs/ui-host/src/lib.rs`
- Delete: `yoyopod_rs/ui-host/src/lvgl_bridge.rs`
- Create: `yoyopod_rs/ui-host/build.rs`
- Modify: `yoyopod_rs/ui-host/Cargo.toml`
- Modify: `yoyopod_rs/ui-host/BUILD.bazel`
- Modify: `yoyopod_rs/ui-host/tests/runtime_state_machine.rs`
- Modify: `yoyopod_rs/ui-host/tests/render_lvgl.rs`
- Modify: `yoyopod_rs/ui-host/tests/worker.rs`
- Move: `yoyopod_rs/ui-host/tests/lvgl_bridge.rs` -> `yoyopod_rs/ui-host/tests/lvgl_runtime.rs`
- Modify: `tests/core/test_rust_ui_worker_contract.py`
- Modify: `tests/cli/test_pi_rust_ui_host.py`
- Modify: `yoyopod_cli/pi/rust_ui_host.py`
- Modify: `docs/RUST_UI_HOST.md`

## Task 1: Derive Typed Screen Models From Generic Runtime Snapshots

**Files:**
- Create: `yoyopod_rs/ui-host/src/screens/models.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/mod.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/hub.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/listen.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/music.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/ask.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/talk.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/call.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/power.rs`
- Modify: `yoyopod_rs/ui-host/src/screens/overlay.rs`
- Modify: `yoyopod_rs/ui-host/src/runtime/state_machine.rs`
- Modify: `yoyopod_rs/ui-host/src/runtime/mod.rs`
- Test: `yoyopod_rs/ui-host/tests/runtime_state_machine.rs`

- [ ] **Step 1: Write failing tests for typed screen-model derivation**

In `yoyopod_rs/ui-host/tests/runtime_state_machine.rs`, add:

```rust
use yoyopod_ui_host::screens::ScreenModel;

#[test]
fn hub_runtime_derives_typed_screen_model() {
    let mut runtime = UiRuntime::default();
    runtime.apply_snapshot(RuntimeSnapshot::default());

    match runtime.active_screen_model() {
        ScreenModel::Hub(model) => {
            assert_eq!(model.cards.len(), 4);
            assert_eq!(model.selected_index, 0);
            assert_eq!(model.chrome.footer, "Tap = Next | 2x Tap = Open");
            assert_eq!(model.chrome.status.battery_percent, 100);
        }
        other => panic!("expected hub model, got {other:?}"),
    }
}

#[test]
fn incoming_call_runtime_derives_call_screen_model() {
    let mut runtime = UiRuntime::default();
    let mut snapshot = RuntimeSnapshot::default();
    snapshot.call.state = "incoming".to_string();
    snapshot.call.peer_name = "Mama".to_string();
    snapshot.call.peer_address = "sip:mama@example.com".to_string();
    runtime.apply_snapshot(snapshot);

    match runtime.active_screen_model() {
        ScreenModel::IncomingCall(model) => {
            assert_eq!(model.title, "Mama");
            assert_eq!(model.subtitle, "sip:mama@example.com");
            assert_eq!(model.chrome.status.voip_state, 2);
        }
        other => panic!("expected incoming call model, got {other:?}"),
    }
}
```

- [ ] **Step 2: Run the focused runtime tests and verify they fail for the right reason**

Run:

```bash
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host runtime_state_machine --locked
```

Expected: failure because `ScreenModel` and `active_screen_model()` do not exist yet.

- [ ] **Step 3: Add shared typed model definitions**

Create `yoyopod_rs/ui-host/src/screens/models.rs`:

```rust
use crate::runtime::UiScreen;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StatusBarModel {
    pub network_connected: bool,
    pub network_enabled: bool,
    pub signal_strength: i32,
    pub battery_percent: i32,
    pub charging: bool,
    pub voip_state: i32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChromeModel {
    pub status: StatusBarModel,
    pub footer: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HubCardModel {
    pub key: String,
    pub title: String,
    pub subtitle: String,
    pub accent: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HubViewModel {
    pub chrome: ChromeModel,
    pub cards: Vec<HubCardModel>,
    pub selected_index: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ListRowModel {
    pub id: String,
    pub title: String,
    pub subtitle: String,
    pub icon_key: String,
    pub selected: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ListScreenModel {
    pub screen: UiScreen,
    pub chrome: ChromeModel,
    pub title: String,
    pub subtitle: String,
    pub rows: Vec<ListRowModel>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NowPlayingViewModel {
    pub chrome: ChromeModel,
    pub title: String,
    pub artist: String,
    pub state_text: String,
    pub progress_permille: i32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AskViewModel {
    pub screen: UiScreen,
    pub chrome: ChromeModel,
    pub title: String,
    pub subtitle: String,
    pub icon_key: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CallViewModel {
    pub screen: UiScreen,
    pub chrome: ChromeModel,
    pub title: String,
    pub subtitle: String,
    pub detail: String,
    pub muted: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PowerViewModel {
    pub chrome: ChromeModel,
    pub title: String,
    pub subtitle: String,
    pub rows: Vec<ListRowModel>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OverlayViewModel {
    pub screen: UiScreen,
    pub chrome: ChromeModel,
    pub title: String,
    pub subtitle: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ScreenModel {
    Hub(HubViewModel),
    Listen(ListScreenModel),
    Playlists(ListScreenModel),
    RecentTracks(ListScreenModel),
    NowPlaying(NowPlayingViewModel),
    Ask(AskViewModel),
    Talk(ListScreenModel),
    Contacts(ListScreenModel),
    CallHistory(ListScreenModel),
    VoiceNote(AskViewModel),
    IncomingCall(CallViewModel),
    OutgoingCall(CallViewModel),
    InCall(CallViewModel),
    Power(PowerViewModel),
    Loading(OverlayViewModel),
    Error(OverlayViewModel),
}

impl ScreenModel {
    pub fn screen(&self) -> UiScreen {
        match self {
            Self::Hub(_) => UiScreen::Hub,
            Self::Listen(_) => UiScreen::Listen,
            Self::Playlists(_) => UiScreen::Playlists,
            Self::RecentTracks(_) => UiScreen::RecentTracks,
            Self::NowPlaying(_) => UiScreen::NowPlaying,
            Self::Ask(_) => UiScreen::Ask,
            Self::Talk(_) => UiScreen::Talk,
            Self::Contacts(_) => UiScreen::Contacts,
            Self::CallHistory(_) => UiScreen::CallHistory,
            Self::VoiceNote(_) => UiScreen::VoiceNote,
            Self::IncomingCall(_) => UiScreen::IncomingCall,
            Self::OutgoingCall(_) => UiScreen::OutgoingCall,
            Self::InCall(_) => UiScreen::InCall,
            Self::Power(_) => UiScreen::Power,
            Self::Loading(_) => UiScreen::Loading,
            Self::Error(_) => UiScreen::Error,
        }
    }
}
```

- [ ] **Step 4: Convert screen modules from `UiView` builders to typed model builders**

In `yoyopod_rs/ui-host/src/screens/mod.rs`, export the model types:

```rust
pub mod ask;
pub mod call;
pub mod hub;
pub mod listen;
pub mod models;
pub mod music;
pub mod overlay;
pub mod power;
pub mod talk;

pub use models::{
    AskViewModel, CallViewModel, ChromeModel, HubCardModel, HubViewModel, ListRowModel,
    ListScreenModel, NowPlayingViewModel, OverlayViewModel, PowerViewModel, ScreenModel,
    StatusBarModel,
};
```

Update `yoyopod_rs/ui-host/src/screens/hub.rs`:

```rust
use crate::runtime::RuntimeSnapshot;
use crate::screens::{ChromeModel, HubCardModel, HubViewModel, StatusBarModel};

pub fn model(snapshot: &RuntimeSnapshot, focus_index: usize) -> HubViewModel {
    HubViewModel {
        chrome: chrome(snapshot, "Tap = Next | 2x Tap = Open"),
        cards: snapshot
            .hub
            .cards
            .iter()
            .map(|card| HubCardModel {
                key: card.key.clone(),
                title: card.title.clone(),
                subtitle: card.subtitle.clone(),
                accent: card.accent,
            })
            .collect(),
        selected_index: focus_index,
    }
}

pub fn chrome(snapshot: &RuntimeSnapshot, footer: &str) -> ChromeModel {
    ChromeModel {
        status: StatusBarModel {
            network_connected: snapshot.network.connected,
            network_enabled: snapshot.network.enabled,
            signal_strength: snapshot.network.signal_strength,
            battery_percent: snapshot.power.battery_percent,
            charging: snapshot.power.charging,
            voip_state: if snapshot.call.state == "idle" { 1 } else { 2 },
        },
        footer: footer.to_string(),
    }
}
```

Update `yoyopod_rs/ui-host/src/screens/music.rs`:

```rust
use crate::runtime::RuntimeSnapshot;
use crate::screens::{hub, ListRowModel, ListScreenModel, NowPlayingViewModel};
use crate::runtime::UiScreen;

pub fn playlists_model(snapshot: &RuntimeSnapshot, focus_index: usize) -> ListScreenModel {
    ListScreenModel {
        screen: UiScreen::Playlists,
        chrome: hub::chrome(snapshot, "Tap = Next | 2x Tap = Play | Hold = Back"),
        title: "Playlists".to_string(),
        subtitle: "Saved mixes".to_string(),
        rows: snapshot
            .music
            .playlists
            .iter()
            .enumerate()
            .map(|(index, item)| ListRowModel {
                id: item.id.clone(),
                title: item.title.clone(),
                subtitle: item.subtitle.clone(),
                icon_key: item.icon_key.clone(),
                selected: index == focus_index,
            })
            .collect(),
    }
}

pub fn now_playing_model(snapshot: &RuntimeSnapshot) -> NowPlayingViewModel {
    NowPlayingViewModel {
        chrome: hub::chrome(snapshot, "Tap = Next | 2x Tap = Play/Pause | Hold = Back"),
        title: snapshot.music.title.clone(),
        artist: snapshot.music.artist.clone(),
        state_text: if snapshot.music.playing {
            "Playing".to_string()
        } else if snapshot.music.paused {
            "Paused".to_string()
        } else {
            "Stopped".to_string()
        },
        progress_permille: snapshot.music.progress_permille,
    }
}
```

Update `yoyopod_rs/ui-host/src/screens/call.rs`:

```rust
use crate::runtime::{RuntimeSnapshot, UiScreen};
use crate::screens::{hub, CallViewModel};

pub fn incoming_model(snapshot: &RuntimeSnapshot) -> CallViewModel {
    CallViewModel {
        screen: UiScreen::IncomingCall,
        chrome: hub::chrome(snapshot, "2x Tap = Answer | Hold = Reject"),
        title: snapshot.call.peer_name.clone(),
        subtitle: snapshot.call.peer_address.clone(),
        detail: "Incoming Call".to_string(),
        muted: snapshot.call.muted,
    }
}
```

Update `yoyopod_rs/ui-host/src/screens/listen.rs`:

```rust
use crate::runtime::{RuntimeSnapshot, UiScreen};
use crate::screens::{hub, ListRowModel, ListScreenModel};

pub fn model(snapshot: &RuntimeSnapshot, focus_index: usize) -> ListScreenModel {
    let items = vec![
        ("now_playing", "Now Playing", snapshot.music.title.as_str(), "track"),
        ("playlists", "Playlists", "Saved mixes", "playlist"),
        ("recent_tracks", "Recent", "Recently played", "recent"),
        ("shuffle", "Shuffle All", "Start music", "shuffle"),
    ];

    ListScreenModel {
        screen: UiScreen::Listen,
        chrome: hub::chrome(snapshot, "Tap = Next | 2x Tap = Open"),
        title: "Listen".to_string(),
        subtitle: "Music".to_string(),
        rows: items
            .into_iter()
            .enumerate()
            .map(|(index, (id, title, subtitle, icon_key))| ListRowModel {
                id: id.to_string(),
                title: title.to_string(),
                subtitle: subtitle.to_string(),
                icon_key: icon_key.to_string(),
                selected: index == focus_index,
            })
            .collect(),
    }
}
```

Update `yoyopod_rs/ui-host/src/screens/ask.rs`:

```rust
use crate::runtime::RuntimeSnapshot;
use crate::runtime::UiScreen;
use crate::screens::{hub, AskViewModel};

pub fn ask_model(snapshot: &RuntimeSnapshot) -> AskViewModel {
    AskViewModel {
        screen: UiScreen::Ask,
        chrome: hub::chrome(snapshot, "2x Tap = Record | Hold = Back"),
        title: snapshot.voice.headline.clone(),
        subtitle: snapshot.voice.body.clone(),
        icon_key: "ask".to_string(),
    }
}

pub fn voice_note_model(snapshot: &RuntimeSnapshot) -> AskViewModel {
    AskViewModel {
        screen: UiScreen::VoiceNote,
        chrome: hub::chrome(snapshot, "2x Tap = Record | Hold = Back"),
        title: "Voice Note".to_string(),
        subtitle: if snapshot.voice.capture_in_flight {
            "Recording...".to_string()
        } else {
            "Ready to record".to_string()
        },
        icon_key: "microphone".to_string(),
    }
}
```

Update `yoyopod_rs/ui-host/src/screens/talk.rs`:

```rust
use crate::runtime::{RuntimeSnapshot, UiScreen};
use crate::screens::{hub, ListRowModel, ListScreenModel};

pub fn model(snapshot: &RuntimeSnapshot, focus_index: usize) -> ListScreenModel {
    let items = [
        ("contacts", "Contacts", "People", "person"),
        ("call_history", "History", "Recent calls", "phone"),
        ("voice_note", "Voice Note", "Record message", "microphone"),
    ];

    ListScreenModel {
        screen: UiScreen::Talk,
        chrome: hub::chrome(snapshot, "Tap = Next | 2x Tap = Open | Hold = Back"),
        title: "Talk".to_string(),
        subtitle: "Calls and messages".to_string(),
        rows: items
            .into_iter()
            .enumerate()
            .map(|(index, (id, title, subtitle, icon_key))| ListRowModel {
                id: id.to_string(),
                title: title.to_string(),
                subtitle: subtitle.to_string(),
                icon_key: icon_key.to_string(),
                selected: index == focus_index,
            })
            .collect(),
    }
}
```

Update `yoyopod_rs/ui-host/src/screens/power.rs`:

```rust
use crate::runtime::RuntimeSnapshot;
use crate::screens::{hub, ListRowModel, PowerViewModel};

pub fn model(snapshot: &RuntimeSnapshot, focus_index: usize) -> PowerViewModel {
    PowerViewModel {
        chrome: hub::chrome(snapshot, "Tap = Next | Hold = Back"),
        title: "Power".to_string(),
        subtitle: "System status".to_string(),
        rows: snapshot
            .power
            .rows
            .iter()
            .enumerate()
            .map(|(index, row)| ListRowModel {
                id: format!("power-{index}"),
                title: row.clone(),
                subtitle: String::new(),
                icon_key: "battery".to_string(),
                selected: index == focus_index,
            })
            .collect(),
    }
}
```

Update `yoyopod_rs/ui-host/src/screens/overlay.rs`:

```rust
use crate::runtime::{RuntimeSnapshot, UiScreen};
use crate::screens::{hub, OverlayViewModel};

pub fn loading_model(snapshot: &RuntimeSnapshot) -> OverlayViewModel {
    OverlayViewModel {
        screen: UiScreen::Loading,
        chrome: hub::chrome(snapshot, "Hold = Back"),
        title: "Loading".to_string(),
        subtitle: snapshot.overlay.message.clone(),
    }
}

pub fn error_model(snapshot: &RuntimeSnapshot) -> OverlayViewModel {
    OverlayViewModel {
        screen: UiScreen::Error,
        chrome: hub::chrome(snapshot, "Hold = Back"),
        title: "Error".to_string(),
        subtitle: snapshot.overlay.error.clone(),
    }
}
```

- [ ] **Step 5: Expose `active_screen_model()` from the runtime**

In `yoyopod_rs/ui-host/src/runtime/state_machine.rs`, add:

```rust
use crate::screens::ScreenModel;

pub fn active_screen_model(&self) -> ScreenModel {
    match self.active_screen {
        UiScreen::Hub => ScreenModel::Hub(screens::hub::model(&self.snapshot, self.focus_index)),
        UiScreen::Listen => {
            ScreenModel::Listen(screens::listen::model(&self.snapshot, self.focus_index))
        }
        UiScreen::Playlists => ScreenModel::Playlists(
            screens::music::playlists_model(&self.snapshot, self.focus_index),
        ),
        UiScreen::RecentTracks => ScreenModel::RecentTracks(
            screens::music::recent_tracks_model(&self.snapshot, self.focus_index),
        ),
        UiScreen::NowPlaying => ScreenModel::NowPlaying(screens::music::now_playing_model(&self.snapshot)),
        UiScreen::Ask => ScreenModel::Ask(screens::ask::ask_model(&self.snapshot)),
        UiScreen::Talk => ScreenModel::Talk(screens::talk::model(&self.snapshot, self.focus_index)),
        UiScreen::Contacts => {
            ScreenModel::Contacts(screens::call::contacts_model(&self.snapshot, self.focus_index))
        }
        UiScreen::CallHistory => ScreenModel::CallHistory(
            screens::call::call_history_model(&self.snapshot, self.focus_index),
        ),
        UiScreen::VoiceNote => ScreenModel::VoiceNote(screens::ask::voice_note_model(&self.snapshot)),
        UiScreen::IncomingCall => ScreenModel::IncomingCall(screens::call::incoming_model(&self.snapshot)),
        UiScreen::OutgoingCall => ScreenModel::OutgoingCall(screens::call::outgoing_model(&self.snapshot)),
        UiScreen::InCall => ScreenModel::InCall(screens::call::in_call_model(&self.snapshot)),
        UiScreen::Power => ScreenModel::Power(screens::power::model(&self.snapshot, self.focus_index)),
        UiScreen::Loading => ScreenModel::Loading(screens::overlay::loading_model(&self.snapshot)),
        UiScreen::Error => ScreenModel::Error(screens::overlay::error_model(&self.snapshot)),
    }
}
```

In `yoyopod_rs/ui-host/src/runtime/mod.rs`, re-export:

```rust
pub use state_machine::{UiRuntime, UiScreen, UiView};
```

and in `yoyopod_rs/ui-host/src/lib.rs`, add:

```rust
pub mod screens;
```

- [ ] **Step 6: Run the runtime tests and make sure they pass**

Run:

```bash
cargo fmt --manifest-path yoyopod_rs/Cargo.toml
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host runtime_state_machine --locked
```

Expected: the new typed-model tests pass and existing runtime navigation tests remain green.

- [ ] **Step 7: Commit the typed-model seam**

Run:

```bash
git add yoyopod_rs/ui-host/src/screens yoyopod_rs/ui-host/src/runtime yoyopod_rs/ui-host/src/lib.rs yoyopod_rs/ui-host/tests/runtime_state_machine.rs
git commit -m "refactor: derive typed rust ui screen models"
```

## Task 2: Introduce A Persistent Renderer And A Testable LVGL Facade

**Files:**
- Create: `yoyopod_rs/ui-host/src/lvgl/mod.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/primitives.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/chrome.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/mod.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/hub.rs`
- Modify: `yoyopod_rs/ui-host/src/render/lvgl.rs`
- Modify: `yoyopod_rs/ui-host/src/render/mod.rs`
- Modify: `yoyopod_rs/ui-host/src/lib.rs`
- Test: `yoyopod_rs/ui-host/tests/render_lvgl.rs`

- [ ] **Step 1: Write a failing renderer test that proves widgets are built once**

Replace the contents of `yoyopod_rs/ui-host/tests/render_lvgl.rs` with:

```rust
use std::collections::HashMap;

use anyhow::Result;
use yoyopod_ui_host::lvgl::{HubController, LvglFacade, LvglRenderer, WidgetId};
use yoyopod_ui_host::runtime::UiScreen;
use yoyopod_ui_host::screens::{
    ChromeModel, HubCardModel, HubViewModel, ScreenModel, StatusBarModel,
};

#[derive(Default)]
struct FakeLvgl {
    next_id: u32,
    created: HashMap<&'static str, usize>,
    text: HashMap<&'static str, String>,
}

impl FakeLvgl {
    fn created_count(&self, key: &'static str) -> usize {
        *self.created.get(key).unwrap_or(&0)
    }

    fn text_value(&self, key: &'static str) -> &str {
        self.text.get(key).map(String::as_str).unwrap_or("")
    }
}

impl LvglFacade for FakeLvgl {
    fn root(&self) -> WidgetId {
        WidgetId(0)
    }

    fn container(&mut self, _parent: WidgetId, key: &'static str) -> WidgetId {
        *self.created.entry(key).or_insert(0) += 1;
        self.next_id += 1;
        WidgetId(self.next_id)
    }

    fn label(&mut self, _parent: WidgetId, key: &'static str) -> WidgetId {
        *self.created.entry(key).or_insert(0) += 1;
        self.next_id += 1;
        WidgetId(self.next_id)
    }

    fn set_text(&mut self, _widget: WidgetId, key: &'static str, value: &str) {
        self.text.insert(key, value.to_string());
    }

    fn set_accent(&mut self, _widget: WidgetId, _rgb: u32) {}
    fn set_selected(&mut self, _widget: WidgetId, _selected: bool) {}
    fn set_progress(&mut self, _widget: WidgetId, _permille: i32) {}
    fn set_visible(&mut self, _widget: WidgetId, _visible: bool) {}
    fn clear_children(&mut self, _widget: WidgetId) {}
    fn flush(&mut self) -> Result<()> {
        Ok(())
    }
}

fn hub_model(title: &str) -> ScreenModel {
    ScreenModel::Hub(HubViewModel {
        chrome: ChromeModel {
            status: StatusBarModel {
                network_connected: false,
                network_enabled: false,
                signal_strength: 0,
                battery_percent: 100,
                charging: false,
                voip_state: 1,
            },
            footer: "Tap = Next | 2x Tap = Open".to_string(),
        },
        cards: vec![HubCardModel {
            key: "listen".to_string(),
            title: title.to_string(),
            subtitle: String::new(),
            accent: 0x00FF88,
        }],
        selected_index: 0,
    })
}

#[test]
fn hub_controller_builds_widgets_once_and_updates_text_in_place() {
    let mut facade = FakeLvgl::default();
    let mut renderer = LvglRenderer::new();

    renderer.render_screen_model(&mut facade, &hub_model("Listen")).unwrap();
    renderer.render_screen_model(&mut facade, &hub_model("Talk")).unwrap();

    assert_eq!(renderer.active_screen(), Some(UiScreen::Hub));
    assert_eq!(facade.created_count("hub.title"), 1);
    assert_eq!(facade.text_value("hub.title"), "Talk");
}
```

- [ ] **Step 2: Run the focused renderer test and verify it fails**

Run:

```bash
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host render_lvgl --locked
```

Expected: failure because `LvglFacade`, `WidgetId`, `HubController`, and the new `LvglRenderer` interface do not exist yet.

- [ ] **Step 3: Add the facade and controller traits**

Create `yoyopod_rs/ui-host/src/lvgl/primitives.rs`:

```rust
use anyhow::Result;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct WidgetId(pub u32);

pub trait LvglFacade {
    fn root(&self) -> WidgetId;
    fn container(&mut self, parent: WidgetId, key: &'static str) -> WidgetId;
    fn label(&mut self, parent: WidgetId, key: &'static str) -> WidgetId;
    fn set_text(&mut self, widget: WidgetId, key: &'static str, value: &str);
    fn set_accent(&mut self, widget: WidgetId, rgb: u32);
    fn set_selected(&mut self, widget: WidgetId, selected: bool);
    fn set_progress(&mut self, widget: WidgetId, permille: i32);
    fn set_visible(&mut self, widget: WidgetId, visible: bool);
    fn clear_children(&mut self, widget: WidgetId);
    fn flush(&mut self) -> Result<()>;
}
```

Create `yoyopod_rs/ui-host/src/lvgl/controllers/mod.rs`:

```rust
use anyhow::Result;

use crate::lvgl::LvglFacade;
use crate::runtime::UiScreen;
use crate::screens::ScreenModel;

pub mod hub;

pub trait ScreenController {
    fn screen(&self) -> UiScreen;
    fn ensure_built(&mut self, ui: &mut dyn LvglFacade) -> Result<()>;
    fn sync(&mut self, ui: &mut dyn LvglFacade, model: &ScreenModel) -> Result<()>;
    fn teardown(&mut self, ui: &mut dyn LvglFacade) -> Result<()>;
}
```

Create `yoyopod_rs/ui-host/src/lvgl/mod.rs`:

```rust
mod chrome;
mod controllers;
mod primitives;

pub use controllers::hub::HubController;
pub use controllers::ScreenController;
pub use primitives::{LvglFacade, WidgetId};
```

- [ ] **Step 4: Rewrite `render/lvgl.rs` as a persistent model-based renderer**

Replace `yoyopod_rs/ui-host/src/render/lvgl.rs` with:

```rust
use anyhow::Result;

use crate::lvgl::{LvglFacade, ScreenController};
use crate::runtime::UiScreen;
use crate::screens::ScreenModel;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RendererMode {
    Auto,
    Lvgl,
    Framebuffer,
}

impl RendererMode {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Auto => "auto",
            Self::Lvgl => "lvgl",
            Self::Framebuffer => "framebuffer",
        }
    }
}

pub struct LvglRenderer {
    active_screen: Option<UiScreen>,
    controller: Option<Box<dyn ScreenController>>,
}

impl LvglRenderer {
    pub fn new() -> Self {
        Self {
            active_screen: None,
            controller: None,
        }
    }

    pub fn active_screen(&self) -> Option<UiScreen> {
        self.active_screen
    }

    fn controller_for(screen: UiScreen) -> Box<dyn ScreenController> {
        match screen {
            UiScreen::Hub => Box::new(crate::lvgl::HubController::default()),
            _ => panic!("controller not implemented for {}", screen.as_str()),
        }
    }

    pub fn render_screen_model(
        &mut self,
        ui: &mut dyn LvglFacade,
        model: &ScreenModel,
    ) -> Result<()> {
        if self.active_screen != Some(model.screen()) {
            if let Some(controller) = self.controller.as_mut() {
                controller.teardown(ui)?;
            }
            let mut controller = Self::controller_for(model.screen());
            controller.ensure_built(ui)?;
            self.controller = Some(controller);
            self.active_screen = Some(model.screen());
        }
        self.controller
            .as_mut()
            .expect("controller exists after ensure_built")
            .sync(ui, model)?;
        ui.flush()
    }
}
```

Update `yoyopod_rs/ui-host/src/render/mod.rs`:

```rust
pub mod framebuffer;
pub mod lvgl;
```

Update `yoyopod_rs/ui-host/src/lib.rs`:

```rust
pub mod lvgl;
pub mod render;
```

- [ ] **Step 5: Add the first concrete controller**

Create `yoyopod_rs/ui-host/src/lvgl/controllers/hub.rs`:

```rust
use anyhow::{bail, Result};

use crate::lvgl::{LvglFacade, WidgetId};
use crate::lvgl::controllers::ScreenController;
use crate::runtime::UiScreen;
use crate::screens::ScreenModel;

#[derive(Default)]
pub struct HubController {
    root: Option<WidgetId>,
    title: Option<WidgetId>,
}

impl ScreenController for HubController {
    fn screen(&self) -> UiScreen {
        UiScreen::Hub
    }

    fn ensure_built(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if self.root.is_none() {
            let root = ui.container(ui.root(), "hub.root");
            let title = ui.label(root, "hub.title");
            self.root = Some(root);
            self.title = Some(title);
        }
        Ok(())
    }

    fn sync(&mut self, ui: &mut dyn LvglFacade, model: &ScreenModel) -> Result<()> {
        let ScreenModel::Hub(model) = model else {
            bail!("hub controller received non-hub model");
        };
        let title = self.title.expect("hub title exists after ensure_built");
        let focused = model
            .cards
            .get(model.selected_index)
            .or_else(|| model.cards.first())
            .map(|card| card.title.as_str())
            .unwrap_or("Listen");
        ui.set_text(title, "hub.title", focused);
        Ok(())
    }

    fn teardown(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if let Some(root) = self.root {
            ui.clear_children(root);
        }
        self.root = None;
        self.title = None;
        Ok(())
    }
}
```

- [ ] **Step 6: Run renderer tests and commit the persistent renderer seam**

Run:

```bash
cargo fmt --manifest-path yoyopod_rs/Cargo.toml
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host render_lvgl --locked
```

Commit:

```bash
git add yoyopod_rs/ui-host/src/lvgl yoyopod_rs/ui-host/src/render yoyopod_rs/ui-host/src/lib.rs yoyopod_rs/ui-host/tests/render_lvgl.rs
git commit -m "refactor: add persistent rust ui renderer seam"
```

## Task 3: Port Navigation, Music, And Ask Controllers Against The Facade

**Files:**
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/list.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/ask.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/chrome.rs`
- Modify: `yoyopod_rs/ui-host/src/lvgl/controllers/mod.rs`
- Modify: `yoyopod_rs/ui-host/src/render/lvgl.rs`
- Modify: `yoyopod_rs/ui-host/tests/render_lvgl.rs`

- [ ] **Step 1: Write failing controller tests for list selection and now-playing progress**

In `yoyopod_rs/ui-host/tests/render_lvgl.rs`, add:

```rust
#[test]
fn list_controller_marks_the_selected_row_without_rebuilding_widgets() {
    let mut facade = FakeLvgl::default();
    let mut renderer = LvglRenderer::new();

    let first = ScreenModel::Listen(ListScreenModel {
        screen: UiScreen::Listen,
        chrome: ChromeModel {
            status: StatusBarModel {
                network_connected: false,
                network_enabled: false,
                signal_strength: 0,
                battery_percent: 90,
                charging: false,
                voip_state: 1,
            },
            footer: "Tap = Next | 2x Tap = Open".to_string(),
        },
        title: "Listen".to_string(),
        subtitle: "Music".to_string(),
        rows: vec![
            ListRowModel {
                id: "now_playing".to_string(),
                title: "Now Playing".to_string(),
                subtitle: "Little Song".to_string(),
                icon_key: "track".to_string(),
                selected: true,
            },
            ListRowModel {
                id: "playlists".to_string(),
                title: "Playlists".to_string(),
                subtitle: "Saved mixes".to_string(),
                icon_key: "playlist".to_string(),
                selected: false,
            },
        ],
    });

    let second = ScreenModel::Listen(ListScreenModel {
        rows: vec![
            ListRowModel {
                id: "now_playing".to_string(),
                title: "Now Playing".to_string(),
                subtitle: "Little Song".to_string(),
                icon_key: "track".to_string(),
                selected: false,
            },
            ListRowModel {
                id: "playlists".to_string(),
                title: "Playlists".to_string(),
                subtitle: "Saved mixes".to_string(),
                icon_key: "playlist".to_string(),
                selected: true,
            },
        ],
        ..match first.clone() {
            ScreenModel::Listen(model) => model,
            _ => unreachable!(),
        }
    });

    renderer.render_screen_model(&mut facade, &first).unwrap();
    renderer.render_screen_model(&mut facade, &second).unwrap();

    assert_eq!(facade.created_count("list.row.0"), 1);
    assert_eq!(facade.created_count("list.row.1"), 1);
}
```

- [ ] **Step 2: Run the list-controller test and verify it fails**

Run:

```bash
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host render_lvgl --locked
```

Expected: failure because `ListController` does not exist yet.

- [ ] **Step 3: Add shared chrome helpers**

Create `yoyopod_rs/ui-host/src/lvgl/chrome.rs`:

```rust
use anyhow::Result;

use crate::lvgl::{LvglFacade, WidgetId};
use crate::screens::ChromeModel;

pub struct ChromeWidgets {
    pub footer: WidgetId,
}

pub fn build_footer(ui: &mut dyn LvglFacade, parent: WidgetId) -> ChromeWidgets {
    let footer = ui.label(parent, "chrome.footer");
    ChromeWidgets { footer }
}

pub fn sync_footer(ui: &mut dyn LvglFacade, widgets: &ChromeWidgets, chrome: &ChromeModel) -> Result<()> {
    ui.set_text(widgets.footer, "chrome.footer", &chrome.footer);
    Ok(())
}
```

- [ ] **Step 4: Add generic list and ask controllers**

Create `yoyopod_rs/ui-host/src/lvgl/controllers/list.rs`:

```rust
use anyhow::{bail, Result};

use crate::lvgl::chrome::{build_footer, sync_footer, ChromeWidgets};
use crate::lvgl::{LvglFacade, WidgetId};
use crate::lvgl::controllers::ScreenController;
use crate::runtime::UiScreen;
use crate::screens::ScreenModel;

pub struct ListController {
    screen: UiScreen,
    root: Option<WidgetId>,
    title: Option<WidgetId>,
    footer: Option<ChromeWidgets>,
    rows: Vec<WidgetId>,
}

impl ListController {
    pub fn new(screen: UiScreen) -> Self {
        Self {
            screen,
            root: None,
            title: None,
            footer: None,
            rows: Vec::new(),
        }
    }
}

impl ScreenController for ListController {
    fn screen(&self) -> UiScreen {
        self.screen
    }

    fn ensure_built(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if self.root.is_none() {
            let root = ui.container(ui.root(), "list.root");
            let title = ui.label(root, "list.title");
            let footer = build_footer(ui, root);
            let rows = (0..4)
                .map(|index| ui.container(root, match index {
                    0 => "list.row.0",
                    1 => "list.row.1",
                    2 => "list.row.2",
                    _ => "list.row.3",
                }))
                .collect();
            self.root = Some(root);
            self.title = Some(title);
            self.footer = Some(footer);
            self.rows = rows;
        }
        Ok(())
    }

    fn sync(&mut self, ui: &mut dyn LvglFacade, model: &ScreenModel) -> Result<()> {
        let list = match model {
            ScreenModel::Listen(model)
            | ScreenModel::Playlists(model)
            | ScreenModel::RecentTracks(model)
            | ScreenModel::Talk(model)
            | ScreenModel::Contacts(model)
            | ScreenModel::CallHistory(model) => model,
            _ => bail!("list controller received non-list model"),
        };
        ui.set_text(self.title.expect("list title exists"), "list.title", &list.title);
        if let Some(footer) = &self.footer {
            sync_footer(ui, footer, &list.chrome)?;
        }
        for (index, row) in self.rows.iter().copied().enumerate() {
            let selected = list.rows.get(index).map(|item| item.selected).unwrap_or(false);
            ui.set_selected(row, selected);
        }
        Ok(())
    }

    fn teardown(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if let Some(root) = self.root {
            ui.clear_children(root);
        }
        self.root = None;
        self.title = None;
        self.footer = None;
        self.rows.clear();
        Ok(())
    }
}
```

Create `yoyopod_rs/ui-host/src/lvgl/controllers/ask.rs`:

```rust
use anyhow::{bail, Result};

use crate::lvgl::chrome::{build_footer, sync_footer, ChromeWidgets};
use crate::lvgl::{LvglFacade, WidgetId};
use crate::lvgl::controllers::ScreenController;
use crate::runtime::UiScreen;
use crate::screens::ScreenModel;

#[derive(Default)]
pub struct AskController {
    root: Option<WidgetId>,
    title: Option<WidgetId>,
    subtitle: Option<WidgetId>,
    footer: Option<ChromeWidgets>,
}

impl ScreenController for AskController {
    fn screen(&self) -> UiScreen {
        UiScreen::Ask
    }

    fn ensure_built(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if self.root.is_none() {
            let root = ui.container(ui.root(), "ask.root");
            let title = ui.label(root, "ask.title");
            let subtitle = ui.label(root, "ask.subtitle");
            let footer = build_footer(ui, root);
            self.root = Some(root);
            self.title = Some(title);
            self.subtitle = Some(subtitle);
            self.footer = Some(footer);
        }
        Ok(())
    }

    fn sync(&mut self, ui: &mut dyn LvglFacade, model: &ScreenModel) -> Result<()> {
        let ask = match model {
            ScreenModel::Ask(model) | ScreenModel::VoiceNote(model) => model,
            _ => bail!("ask controller received non-ask model"),
        };
        ui.set_text(self.title.expect("ask title exists"), "ask.title", &ask.title);
        ui.set_text(self.subtitle.expect("ask subtitle exists"), "ask.subtitle", &ask.subtitle);
        if let Some(footer) = &self.footer {
            sync_footer(ui, footer, &ask.chrome)?;
        }
        Ok(())
    }

    fn teardown(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if let Some(root) = self.root {
            ui.clear_children(root);
        }
        self.root = None;
        self.title = None;
        self.subtitle = None;
        self.footer = None;
        Ok(())
    }
}
```

Update `yoyopod_rs/ui-host/src/lvgl/controllers/mod.rs`:

```rust
pub mod ask;
pub mod hub;
pub mod list;
```

Update `yoyopod_rs/ui-host/src/lvgl/mod.rs` so it re-exports the new controllers:

```rust
pub use controllers::ask::AskController;
pub use controllers::hub::HubController;
pub use controllers::list::ListController;
```

- [ ] **Step 5: Expand the renderer controller factory for navigation/music screens**

In `yoyopod_rs/ui-host/src/render/lvgl.rs`, replace `controller_for` with:

```rust
use crate::lvgl::{AskController, HubController, ListController};

fn controller_for(screen: UiScreen) -> Box<dyn ScreenController> {
    match screen {
        UiScreen::Hub => Box::new(HubController::default()),
        UiScreen::Listen
        | UiScreen::Playlists
        | UiScreen::RecentTracks
        | UiScreen::Talk
        | UiScreen::Contacts
        | UiScreen::CallHistory => Box::new(ListController::new(screen)),
        UiScreen::Ask | UiScreen::VoiceNote => Box::new(AskController::default()),
        _ => panic!("controller not implemented for {}", screen.as_str()),
    }
}
```

and update the test to construct:

```rust
let mut renderer = LvglRenderer::new();
```

- [ ] **Step 6: Run renderer tests and commit navigation/music controller coverage**

Run:

```bash
cargo fmt --manifest-path yoyopod_rs/Cargo.toml
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host render_lvgl --locked
```

Commit:

```bash
git add yoyopod_rs/ui-host/src/lvgl yoyopod_rs/ui-host/src/render/lvgl.rs yoyopod_rs/ui-host/tests/render_lvgl.rs
git commit -m "feat: port rust ui navigation controllers"
```

## Task 4: Port Call, Power, And Overlay Controllers And Wire The Worker To `ScreenModel`

**Files:**
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/call.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/power.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/controllers/overlay.rs`
- Modify: `yoyopod_rs/ui-host/src/lvgl/controllers/mod.rs`
- Modify: `yoyopod_rs/ui-host/src/render/lvgl.rs`
- Modify: `yoyopod_rs/ui-host/src/render/framebuffer.rs`
- Modify: `yoyopod_rs/ui-host/src/worker.rs`
- Modify: `yoyopod_rs/ui-host/tests/worker.rs`

- [ ] **Step 1: Write failing worker tests for model-based rendering and call preemption**

In `yoyopod_rs/ui-host/tests/worker.rs`, add:

```rust
#[test]
fn worker_runtime_snapshot_still_reports_screen_changes_with_model_renderer() {
    let input = br#"{"kind":"command","type":"ui.runtime_snapshot","payload":{"music":{"title":"Little Song","artist":"YoYo"}}}
{"kind":"command","type":"ui.health","payload":{}}
{"kind":"command","type":"ui.shutdown","payload":{}}
"#;
    let mut output = Vec::new();
    let mut errors = Vec::new();
    let display = MockDisplay::new(240, 280);
    let button = MockButton::new();

    run_worker(input.as_slice(), &mut output, &mut errors, display, button)
        .expect("worker exits cleanly");

    let stdout = String::from_utf8(output).expect("utf8");
    assert!(stdout.contains("\"type\":\"ui.screen_changed\""));
    assert!(stdout.contains("\"screen\":\"hub\""));
    assert!(stdout.contains("\"last_ui_renderer\":\"framebuffer\"") || stdout.contains("\"last_ui_renderer\":\"lvgl\""));
}

#[test]
fn worker_incoming_call_input_emits_answer_intent_with_model_renderer() {
    let input = br#"{"kind":"command","type":"ui.runtime_snapshot","payload":{"call":{"state":"incoming","peer_name":"Mama","peer_address":"sip:mama@example.com"}}}
{"kind":"command","type":"ui.input_action","payload":{"action":"select"}}
{"kind":"command","type":"ui.shutdown","payload":{}}
"#;
    let mut output = Vec::new();
    let mut errors = Vec::new();
    let display = MockDisplay::new(240, 280);
    let button = MockButton::new();

    run_worker(input.as_slice(), &mut output, &mut errors, display, button)
        .expect("worker exits cleanly");

    let stdout = String::from_utf8(output).expect("utf8");
    assert!(stdout.contains("\"type\":\"ui.intent\""));
    assert!(stdout.contains("\"action\":\"answer\""));
}
```

- [ ] **Step 2: Run the worker tests and verify they fail**

Run:

```bash
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host worker --locked
```

Expected: failure because the renderer still consumes `UiView` and the remaining controller families do not exist.

- [ ] **Step 3: Add the remaining controller families**

Create `yoyopod_rs/ui-host/src/lvgl/controllers/call.rs`:

```rust
use anyhow::{bail, Result};

use crate::lvgl::chrome::{build_footer, sync_footer, ChromeWidgets};
use crate::lvgl::{LvglFacade, WidgetId};
use crate::lvgl::controllers::ScreenController;
use crate::runtime::UiScreen;
use crate::screens::ScreenModel;

pub struct CallController {
    screen: UiScreen,
    root: Option<WidgetId>,
    title: Option<WidgetId>,
    subtitle: Option<WidgetId>,
    detail: Option<WidgetId>,
    footer: Option<ChromeWidgets>,
}

impl CallController {
    pub fn new(screen: UiScreen) -> Self {
        Self {
            screen,
            root: None,
            title: None,
            subtitle: None,
            detail: None,
            footer: None,
        }
    }
}

impl ScreenController for CallController {
    fn screen(&self) -> UiScreen {
        self.screen
    }

    fn ensure_built(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if self.root.is_none() {
            let root = ui.container(ui.root(), "call.root");
            self.title = Some(ui.label(root, "call.title"));
            self.subtitle = Some(ui.label(root, "call.subtitle"));
            self.detail = Some(ui.label(root, "call.detail"));
            self.footer = Some(build_footer(ui, root));
            self.root = Some(root);
        }
        Ok(())
    }

    fn sync(&mut self, ui: &mut dyn LvglFacade, model: &ScreenModel) -> Result<()> {
        let call = match model {
            ScreenModel::IncomingCall(model)
            | ScreenModel::OutgoingCall(model)
            | ScreenModel::InCall(model) => model,
            _ => bail!("call controller received non-call model"),
        };
        ui.set_text(self.title.expect("call title exists"), "call.title", &call.title);
        ui.set_text(self.subtitle.expect("call subtitle exists"), "call.subtitle", &call.subtitle);
        ui.set_text(self.detail.expect("call detail exists"), "call.detail", &call.detail);
        if let Some(footer) = &self.footer {
            sync_footer(ui, footer, &call.chrome)?;
        }
        Ok(())
    }

    fn teardown(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if let Some(root) = self.root {
            ui.clear_children(root);
        }
        *self = Self::new(self.screen);
        Ok(())
    }
}
```

Create `yoyopod_rs/ui-host/src/lvgl/controllers/power.rs`:

```rust
use anyhow::{bail, Result};

use crate::lvgl::chrome::{build_footer, sync_footer, ChromeWidgets};
use crate::lvgl::{LvglFacade, WidgetId};
use crate::lvgl::controllers::ScreenController;
use crate::runtime::UiScreen;
use crate::screens::ScreenModel;

#[derive(Default)]
pub struct PowerController {
    root: Option<WidgetId>,
    title: Option<WidgetId>,
    subtitle: Option<WidgetId>,
    footer: Option<ChromeWidgets>,
    rows: Vec<WidgetId>,
}

impl ScreenController for PowerController {
    fn screen(&self) -> UiScreen {
        UiScreen::Power
    }

    fn ensure_built(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if self.root.is_none() {
            let root = ui.container(ui.root(), "power.root");
            self.title = Some(ui.label(root, "power.title"));
            self.subtitle = Some(ui.label(root, "power.subtitle"));
            self.footer = Some(build_footer(ui, root));
            self.rows = (0..5)
                .map(|index| ui.label(root, match index {
                    0 => "power.row.0",
                    1 => "power.row.1",
                    2 => "power.row.2",
                    3 => "power.row.3",
                    _ => "power.row.4",
                }))
                .collect();
            self.root = Some(root);
        }
        Ok(())
    }

    fn sync(&mut self, ui: &mut dyn LvglFacade, model: &ScreenModel) -> Result<()> {
        let ScreenModel::Power(model) = model else {
            bail!("power controller received non-power model");
        };
        ui.set_text(self.title.expect("power title exists"), "power.title", &model.title);
        ui.set_text(
            self.subtitle.expect("power subtitle exists"),
            "power.subtitle",
            &model.subtitle,
        );
        if let Some(footer) = &self.footer {
            sync_footer(ui, footer, &model.chrome)?;
        }
        for (index, row) in self.rows.iter().copied().enumerate() {
            let text = model.rows.get(index).map(|item| item.title.as_str()).unwrap_or("");
            ui.set_text(row, match index {
                0 => "power.row.0",
                1 => "power.row.1",
                2 => "power.row.2",
                3 => "power.row.3",
                _ => "power.row.4",
            }, text);
        }
        Ok(())
    }

    fn teardown(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if let Some(root) = self.root {
            ui.clear_children(root);
        }
        *self = Self::default();
        Ok(())
    }
}
```

Create `yoyopod_rs/ui-host/src/lvgl/controllers/overlay.rs`:

```rust
use anyhow::{bail, Result};

use crate::lvgl::chrome::{build_footer, sync_footer, ChromeWidgets};
use crate::lvgl::{LvglFacade, WidgetId};
use crate::lvgl::controllers::ScreenController;
use crate::runtime::UiScreen;
use crate::screens::ScreenModel;

pub struct OverlayController {
    screen: UiScreen,
    root: Option<WidgetId>,
    title: Option<WidgetId>,
    subtitle: Option<WidgetId>,
    footer: Option<ChromeWidgets>,
}

impl OverlayController {
    pub fn new(screen: UiScreen) -> Self {
        Self {
            screen,
            root: None,
            title: None,
            subtitle: None,
            footer: None,
        }
    }
}

impl ScreenController for OverlayController {
    fn screen(&self) -> UiScreen {
        self.screen
    }

    fn ensure_built(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if self.root.is_none() {
            let root = ui.container(ui.root(), "overlay.root");
            self.title = Some(ui.label(root, "overlay.title"));
            self.subtitle = Some(ui.label(root, "overlay.subtitle"));
            self.footer = Some(build_footer(ui, root));
            self.root = Some(root);
        }
        Ok(())
    }

    fn sync(&mut self, ui: &mut dyn LvglFacade, model: &ScreenModel) -> Result<()> {
        let overlay = match model {
            ScreenModel::Loading(model) | ScreenModel::Error(model) => model,
            _ => bail!("overlay controller received non-overlay model"),
        };
        ui.set_text(
            self.title.expect("overlay title exists"),
            "overlay.title",
            &overlay.title,
        );
        ui.set_text(
            self.subtitle.expect("overlay subtitle exists"),
            "overlay.subtitle",
            &overlay.subtitle,
        );
        if let Some(footer) = &self.footer {
            sync_footer(ui, footer, &overlay.chrome)?;
        }
        Ok(())
    }

    fn teardown(&mut self, ui: &mut dyn LvglFacade) -> Result<()> {
        if let Some(root) = self.root {
            ui.clear_children(root);
        }
        *self = Self::new(self.screen);
        Ok(())
    }
}
```

Update `yoyopod_rs/ui-host/src/lvgl/controllers/mod.rs`:

```rust
pub mod ask;
pub mod call;
pub mod hub;
pub mod list;
pub mod overlay;
pub mod power;
```

Update `yoyopod_rs/ui-host/src/lvgl/mod.rs` so it re-exports every production controller:

```rust
pub use controllers::ask::AskController;
pub use controllers::call::CallController;
pub use controllers::hub::HubController;
pub use controllers::list::ListController;
pub use controllers::overlay::OverlayController;
pub use controllers::power::PowerController;
```

- [ ] **Step 4: Switch both renderers from `UiView` to `ScreenModel`**

In `yoyopod_rs/ui-host/src/render/framebuffer.rs`, replace:

```rust
use crate::runtime::{RuntimeSnapshot, UiScreen, UiView};
```

with:

```rust
use crate::runtime::UiScreen;
use crate::screens::ScreenModel;
```

and rename:

```rust
pub fn render_ui_view_fallback(
    framebuffer: &mut Framebuffer,
    view: &UiView,
    snapshot: &RuntimeSnapshot,
)
```

to:

```rust
pub fn render_screen_model_fallback(framebuffer: &mut Framebuffer, model: &ScreenModel)
```

matching over `ScreenModel` variants instead of `UiView.screen`.

In `yoyopod_rs/ui-host/src/worker.rs`, replace:

```rust
let view = ui_runtime.active_view();
```

with:

```rust
let screen_model = ui_runtime.active_screen_model();
```

and replace the render branches with:

```rust
match renderer {
    RendererMode::Auto => {
        FramebufferRenderer::render_screen_model(framebuffer, &screen_model);
        *last_ui_renderer = RendererMode::Framebuffer.as_str().to_string();
    }
    RendererMode::Framebuffer => {
        FramebufferRenderer::render_screen_model(framebuffer, &screen_model);
        *last_ui_renderer = RendererMode::Framebuffer.as_str().to_string();
    }
    RendererMode::Lvgl => {
        let Some(renderer) = lvgl_renderer.as_mut() else {
            emit(
                output,
                Envelope::error("lvgl_unavailable", "LVGL runtime renderer unavailable"),
            )?;
            bail!("LVGL runtime renderer unavailable");
        };
        renderer.render_screen_model(framebuffer, &screen_model)?;
        *last_ui_renderer = RendererMode::Lvgl.as_str().to_string();
    }
}
```

- [ ] **Step 5: Remove shim-specific worker bookkeeping**

In `yoyopod_rs/ui-host/src/worker.rs`, delete:

```rust
let mut last_hub_renderer = String::new();
```

Delete the entire `"ui.show_hub"` command branch.

In the `ui.health` payload, keep only:

```rust
"frames": frames,
"button_events": input_events,
"last_ui_renderer": last_ui_renderer,
"active_screen": ui_runtime.active_screen().as_str(),
```

- [ ] **Step 6: Run worker and renderer tests, then commit**

Run:

```bash
cargo fmt --manifest-path yoyopod_rs/Cargo.toml
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host worker --locked
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host render_lvgl --locked
```

Commit:

```bash
git add yoyopod_rs/ui-host/src/lvgl yoyopod_rs/ui-host/src/render yoyopod_rs/ui-host/src/worker.rs yoyopod_rs/ui-host/tests/worker.rs
git commit -m "feat: wire rust ui host to typed screen renderer"
```

## Task 5: Add The Direct Upstream LVGL Backend And Delete `lvgl_bridge.rs`

**Files:**
- Create: `yoyopod_rs/ui-host/build.rs`
- Modify: `yoyopod_rs/ui-host/Cargo.toml`
- Create: `yoyopod_rs/ui-host/src/lvgl/sys.rs`
- Create: `yoyopod_rs/ui-host/src/lvgl/native_backend.rs`
- Modify: `yoyopod_rs/ui-host/src/lvgl/mod.rs`
- Modify: `yoyopod_rs/ui-host/src/render/lvgl.rs`
- Modify: `yoyopod_rs/ui-host/src/lib.rs`
- Delete: `yoyopod_rs/ui-host/src/lvgl_bridge.rs`
- Move: `yoyopod_rs/ui-host/tests/lvgl_bridge.rs` -> `yoyopod_rs/ui-host/tests/lvgl_runtime.rs`
- Modify: `yoyopod_rs/ui-host/BUILD.bazel`

- [ ] **Step 1: Write failing direct-backend tests**

Create `yoyopod_rs/ui-host/tests/lvgl_runtime.rs`:

```rust
use std::path::Path;

use yoyopod_ui_host::lvgl::open_default_facade;

#[test]
fn default_facade_explains_missing_native_feature() {
    let error = open_default_facade(None).expect_err("native backend should be unavailable");
    assert!(error.to_string().contains("native-lvgl feature"));
}

#[cfg(feature = "native-lvgl")]
#[test]
fn explicit_missing_lvgl_source_path_returns_contextual_error() {
    let error = open_default_facade(Some(Path::new("missing-lvgl-source")))
        .expect_err("missing lvgl source path must fail");
    assert!(error.to_string().contains("LVGL"));
}
```

- [ ] **Step 2: Run the runtime test and verify it fails**

Run:

```bash
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host lvgl_runtime --locked
```

Expected: failure because `open_default_facade()` and the native backend do not exist.

- [ ] **Step 3: Add Cargo build support for upstream LVGL**

Update `yoyopod_rs/ui-host/Cargo.toml`:

```toml
[build-dependencies]
cmake = "0.1"

[features]
default = []
native-lvgl = []
whisplay-hardware = ["dep:rppal"]
```

Create `yoyopod_rs/ui-host/build.rs`:

```rust
use std::env;
use std::path::PathBuf;

fn main() {
    if env::var_os("CARGO_FEATURE_NATIVE_LVGL").is_none() {
        return;
    }

    let native_dir = PathBuf::from("..")
        .join("..")
        .join("yoyopod")
        .join("ui")
        .join("lvgl_binding")
        .join("native");

    let lvgl_source_dir = env::var("YOYOPOD_LVGL_SOURCE_DIR")
        .or_else(|_| env::var("LVGL_SOURCE_DIR"))
        .expect("set YOYOPOD_LVGL_SOURCE_DIR to an LVGL 9.5 checkout");

    let dst = cmake::Config::new(&native_dir)
        .define("LVGL_SOURCE_DIR", lvgl_source_dir)
        .build_target("lvgl")
        .profile("Release")
        .build();

    println!("cargo:rustc-link-search=native={}", dst.join("build").display());
    println!("cargo:rustc-link-lib=static=lvgl");
}
```

- [ ] **Step 4: Add the raw FFI and native facade**

Create `yoyopod_rs/ui-host/src/lvgl/sys.rs`:

```rust
#![allow(non_camel_case_types, non_snake_case, non_upper_case_globals)]

use std::ffi::c_void;
use std::os::raw::{c_int, c_uint};

pub enum lv_display_t {}
pub enum lv_obj_t {}

#[repr(C)]
pub struct lv_area_t {
    pub x1: i32,
    pub y1: i32,
    pub x2: i32,
    pub y2: i32,
}

#[link(name = "lvgl")]
unsafe extern "C" {
    pub fn lv_init();
    pub fn lv_tick_inc(ms: u32);
    pub fn lv_timer_handler() -> u32;
    pub fn lv_display_create(horizontal: c_int, vertical: c_int) -> *mut lv_display_t;
    pub fn lv_display_set_buffers(
        display: *mut lv_display_t,
        buf1: *mut c_void,
        buf2: *mut c_void,
        size_in_bytes: c_uint,
        render_mode: c_int,
    );
    pub fn lv_screen_active() -> *mut lv_obj_t;
    pub fn lv_obj_clean(obj: *mut lv_obj_t);
}
```

Create `yoyopod_rs/ui-host/src/lvgl/native_backend.rs`:

```rust
use std::path::Path;

use anyhow::{bail, Result};

use crate::lvgl::{LvglFacade, WidgetId};

pub struct NativeLvglFacade;

impl NativeLvglFacade {
    pub fn open(explicit_source: Option<&Path>) -> Result<Self> {
        if let Some(path) = explicit_source {
            if !path.exists() {
                bail!("LVGL source path not found at {}", path.display());
            }
        }
        unsafe {
            crate::lvgl::sys::lv_init();
        }
        Ok(Self)
    }
}

impl LvglFacade for NativeLvglFacade {
    fn root(&self) -> WidgetId {
        WidgetId(0)
    }

    fn container(&mut self, _parent: WidgetId, _key: &'static str) -> WidgetId {
        WidgetId(1)
    }

    fn label(&mut self, _parent: WidgetId, _key: &'static str) -> WidgetId {
        WidgetId(1)
    }

    fn set_text(&mut self, _widget: WidgetId, _key: &'static str, _value: &str) {}
    fn set_accent(&mut self, _widget: WidgetId, _rgb: u32) {}
    fn set_selected(&mut self, _widget: WidgetId, _selected: bool) {}
    fn set_progress(&mut self, _widget: WidgetId, _permille: i32) {}
    fn set_visible(&mut self, _widget: WidgetId, _visible: bool) {}
    fn clear_children(&mut self, _widget: WidgetId) {}
    fn flush(&mut self) -> Result<()> {
        Ok(())
    }
}
```

- [ ] **Step 5: Expose the default facade factory and remove the shim bridge**

Update `yoyopod_rs/ui-host/src/lvgl/mod.rs`:

```rust
#[cfg(feature = "native-lvgl")]
pub mod native_backend;
#[cfg(feature = "native-lvgl")]
pub mod sys;

use anyhow::{bail, Result};
use std::path::Path;

#[cfg(feature = "native-lvgl")]
pub fn open_default_facade(explicit_source: Option<&Path>) -> Result<Box<dyn LvglFacade>> {
    Ok(Box::new(native_backend::NativeLvglFacade::open(explicit_source)?))
}

#[cfg(not(feature = "native-lvgl"))]
pub fn open_default_facade(_explicit_source: Option<&Path>) -> Result<Box<dyn LvglFacade>> {
    bail!("native-lvgl feature is disabled for this build")
}
```

Update `yoyopod_rs/ui-host/src/render/lvgl.rs` so production construction uses:

```rust
pub fn open_default() -> Result<(Self, Box<dyn LvglFacade>)> {
    let facade = crate::lvgl::open_default_facade(None)?;
    Ok((Self::new(), facade))
}
```

Delete `yoyopod_rs/ui-host/src/lvgl_bridge.rs`.

In `yoyopod_rs/ui-host/src/lib.rs`, delete:

```rust
pub mod lvgl_bridge;
```

Update `yoyopod_rs/ui-host/BUILD.bazel` test list to replace `lvgl_bridge` with `lvgl_runtime`.

- [ ] **Step 6: Run native-feature tests and commit the direct backend cutover**

Run:

```bash
cargo fmt --manifest-path yoyopod_rs/Cargo.toml
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host lvgl_runtime --locked
$env:YOYOPOD_LVGL_SOURCE_DIR = "C:\\path\\to\\lvgl"
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host --features native-lvgl --locked
bazel test //yoyopod_rs/ui-host/...
```

Commit:

```bash
git add yoyopod_rs/ui-host/build.rs yoyopod_rs/ui-host/Cargo.toml yoyopod_rs/ui-host/src/lvgl yoyopod_rs/ui-host/src/render/lvgl.rs yoyopod_rs/ui-host/src/lib.rs yoyopod_rs/ui-host/BUILD.bazel yoyopod_rs/ui-host/tests/lvgl_runtime.rs yoyopod_rs/ui-host/src/lvgl_bridge.rs
git commit -m "feat: replace rust ui shim bridge with native lvgl backend"
```

## Task 6: Clean Up Python Smoke/Contract Surfaces And Validate The Artifact

**Files:**
- Modify: `yoyopod_cli/pi/rust_ui_host.py`
- Modify: `tests/cli/test_pi_rust_ui_host.py`
- Modify: `tests/core/test_rust_ui_worker_contract.py`
- Modify: `docs/RUST_UI_HOST.md`

- [ ] **Step 1: Write failing Python-side tests for generic snapshot smoke flow**

In `tests/cli/test_pi_rust_ui_host.py`, replace the static-hub assertion test with:

```python
def test_rust_ui_host_sends_generic_runtime_snapshot(monkeypatch, tmp_path: Path) -> None:
    worker = tmp_path / "yoyopod-ui-host"
    worker.write_text("fake", encoding="utf-8")
    _FakeSupervisor.instances.clear()
    monkeypatch.setattr(rust_ui_host, "RustUiHostSupervisor", _FakeSupervisor)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["rust-ui-host", "--worker", str(worker), "--frames", "1", "--screen", "hub"],
    )

    assert result.exit_code == 0
    sent = _FakeSupervisor.instances[-1].sent[0]
    assert sent.type == "ui.runtime_snapshot"
    assert sent.payload["hub"]["cards"][0]["title"] == "Listen"
```

In `tests/core/test_rust_ui_worker_contract.py`, replace `test_rust_ui_worker_accepts_static_hub_command` with:

```python
def test_rust_ui_worker_accepts_generic_runtime_snapshot_command() -> None:
    if shutil.which("cargo") is None:
        pytest.skip("cargo toolchain not available")

    command = {
        "schema_version": 1,
        "kind": "command",
        "type": "ui.runtime_snapshot",
        "request_id": "runtime-contract",
        "timestamp_ms": 1,
        "deadline_ms": 1000,
        "payload": {
            "hub": {
                "cards": [
                    {"key": "listen", "title": "Listen", "subtitle": "", "accent": 65416}
                ]
            }
        },
    }
    health = {
        "schema_version": 1,
        "kind": "command",
        "type": "ui.health",
        "request_id": "health",
        "timestamp_ms": 2,
        "deadline_ms": 1000,
        "payload": {},
    }
    shutdown = {
        "schema_version": 1,
        "kind": "command",
        "type": "ui.shutdown",
        "request_id": "shutdown",
        "timestamp_ms": 3,
        "deadline_ms": 1000,
        "payload": {},
    }

    result = subprocess.run(
        [
            "cargo",
            "run",
            "--manifest-path",
            RUST_UI_MANIFEST.as_posix(),
            "--quiet",
            "--bin",
            "yoyopod-ui-host",
            "--",
            "--hardware",
            "mock",
        ],
        input="\\n".join(json.dumps(item) for item in (command, health, shutdown)) + "\\n",
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    envelopes = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert envelopes[0]["type"] == "ui.ready"
    assert envelopes[-1]["type"] == "ui.health"
```

- [ ] **Step 2: Run the Python tests and verify they fail**

Run:

```bash
uv run pytest -q tests/cli/test_pi_rust_ui_host.py tests/core/test_rust_ui_worker_contract.py
```

Expected: failure because the CLI still sends `ui.show_hub` and the worker contract test still assumes the shim-era command.

- [ ] **Step 3: Switch the smoke CLI to generic snapshot payloads**

In `yoyopod_cli/pi/rust_ui_host.py`, replace:

```python
from yoyopod.ui.rust_host.hub import HubRenderer, RustHubSnapshot
```

with:

```python
from yoyopod.ui.rust_host.snapshot import RustUiRuntimeSnapshot
```

Replace the `hub` branch:

```python
if selected_screen == "hub":
    supervisor.send(
        UiEnvelope.command(
            "ui.runtime_snapshot",
            RustUiRuntimeSnapshot().to_payload(),
            request_id=f"snapshot-{counter}",
        )
    )
```

Delete the `--hub-renderer` option, delete `_hub_renderer`, and update the help text so `--screen hub` means "send a generic hub-focused runtime snapshot".

- [ ] **Step 4: Update docs and run the full validation matrix**

In `docs/RUST_UI_HOST.md`, add:

```text
Rust UI Host render contract:
- Python sends generic `ui.runtime_snapshot` payloads only.
- The Rust host no longer accepts `ui.show_hub`.
- Direct LVGL builds require `YOYOPOD_LVGL_SOURCE_DIR` to point at an LVGL 9.5 checkout.
```

Run:

```bash
cargo fmt --manifest-path yoyopod_rs/Cargo.toml
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host --locked
bazel test //yoyopod_rs/ui-host/...
uv run python scripts/quality.py gate
uv run pytest -q
```

- [ ] **Step 5: Validate the CI-built artifact on Whisplay hardware**

After pushing the branch, use the exact artifact for the commit under test.

Run:

```bash
git push origin <branch>
```

Wait for the `ui-rust` artifact named:

```text
yoyopod-ui-host-<sha>
```

Copy it to the Pi:

```bash
ssh tifo@rpi-zero "mkdir -p /opt/yoyopod-dev/checkout/yoyopod_rs/ui-host/build"
scp <downloaded-yoyopod-ui-host> tifo@rpi-zero:/opt/yoyopod-dev/checkout/yoyopod_rs/ui-host/build/yoyopod-ui-host
ssh tifo@rpi-zero "chmod +x /opt/yoyopod-dev/checkout/yoyopod_rs/ui-host/build/yoyopod-ui-host"
```

Run:

```bash
yoyopod pi rust-ui-host --worker yoyopod_rs/ui-host/build/yoyopod-ui-host --frames 10 --screen hub
```

Expected:

- `ui.ready` emitted once.
- generic `ui.runtime_snapshot` renders the hub.
- no `yoyopod_lvgl_*` shim dependency is needed by the Rust host binary.
- input still produces `ui.input`.
- incoming/active/idle call snapshots still preempt and unwind correctly.

- [ ] **Step 6: Commit the protocol cleanup and document validation**

Run:

```bash
git add yoyopod_cli/pi/rust_ui_host.py tests/cli/test_pi_rust_ui_host.py tests/core/test_rust_ui_worker_contract.py docs/RUST_UI_HOST.md
git commit -m "chore: align rust ui host smoke flow with generic snapshots"
```

## Final Verification Before PR Ready State

Run locally:

```bash
cargo fmt --manifest-path yoyopod_rs/Cargo.toml
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host --locked
bazel test //yoyopod_rs/ui-host/...
uv run python scripts/quality.py gate
uv run pytest -q
```

Run locally with direct LVGL enabled:

```bash
$env:YOYOPOD_LVGL_SOURCE_DIR = "C:\\path\\to\\lvgl"
cargo test --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host --features native-lvgl --locked
cargo build --manifest-path yoyopod_rs/Cargo.toml -p yoyopod-ui-host --release --features "whisplay-hardware,native-lvgl" --locked
```

Run on hardware only with the CI artifact:

```bash
yoyopod pi rust-ui-host --worker yoyopod_rs/ui-host/build/yoyopod-ui-host --frames 10 --screen hub
```

Do not mark the PR ready until:

- the Rust host no longer references `lvgl_bridge.rs`
- `ui.show_hub` is gone from the Rust worker contract
- generic snapshots remain the only Python-to-Rust render input
- the CI artifact has been validated on Whisplay hardware
