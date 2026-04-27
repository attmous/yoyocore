# Rust Whisplay UI I/O PoC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an opt-in Whisplay-only Rust sidecar proof that can render a test scene, decode one-button input, and be supervised by Python.

**Architecture:** Add a Rust worker under `workers/ui/rust` that speaks newline-delimited JSON over stdin/stdout and owns the PoC framebuffer/input loop. Add a small Python supervisor under `yoyopod/ui/rust_sidecar` plus CLI build and Pi validation commands. Keep the existing Python LVGL production path unchanged unless the PoC command is explicitly run.

**Tech Stack:** Rust 2021, Cargo, `serde`/`serde_json`, `clap`, `embedded-graphics`, optional Linux `rppal` hardware feature, Python 3.12, Typer, pytest.

---

## File Structure

- Create: `workers/ui/rust/Cargo.toml` - Rust crate manifest for the sidecar.
- Create: `workers/ui/rust/src/main.rs` - CLI entrypoint and hardware/mock mode selection.
- Create: `workers/ui/rust/src/protocol.rs` - newline JSON envelope types and validation.
- Create: `workers/ui/rust/src/input.rs` - one-button debounce/tap/hold state machine.
- Create: `workers/ui/rust/src/framebuffer.rs` - RGB565 framebuffer and pixel helpers.
- Create: `workers/ui/rust/src/render.rs` - deterministic test scene renderer.
- Create: `workers/ui/rust/src/worker.rs` - stdin/stdout worker loop.
- Create: `workers/ui/rust/src/hardware/mod.rs` - hardware traits.
- Create: `workers/ui/rust/src/hardware/mock.rs` - test display/input implementation.
- Create: `workers/ui/rust/src/hardware/whisplay.rs` - Linux Whisplay hardware implementation behind the `whisplay-hardware` feature.
- Modify: `.gitignore` - ignore Cargo target output.
- Create: `yoyopod/ui/rust_sidecar/__init__.py` - Python package export.
- Create: `yoyopod/ui/rust_sidecar/protocol.py` - Python envelope parser/encoder.
- Create: `yoyopod/ui/rust_sidecar/supervisor.py` - Python subprocess supervisor.
- Modify: `yoyopod_cli/build.py` - add `yoyopod build rust-ui-poc`.
- Create: `yoyopod_cli/pi/rust_ui_poc.py` - on-Pi PoC validation command.
- Modify: `yoyopod_cli/pi/__init__.py` - register `yoyopod pi rust-ui-poc`.
- Modify: `yoyopod_cli/remote_validate.py` - add remote validation flag that builds and runs the PoC on the Pi.
- Modify: `yoyopod_cli/main.py` - expose the top-level validate shortcut flag.
- Modify: `.github/workflows/ci.yml` - run Rust worker tests when Rust UI files change.
- Modify: `yoyopod_cli/COMMANDS.md` - regenerate command docs with `yoyopod dev docs`.
- Create: `tests/ui/test_rust_sidecar_protocol.py` - Python protocol tests.
- Create: `tests/ui/test_rust_sidecar_supervisor.py` - Python supervisor tests with fake process.
- Modify: `tests/cli/test_yoyopod_cli_build.py` - build command tests.
- Create: `tests/cli/test_pi_rust_ui_poc.py` - CLI validation command tests.
- Modify: `tests/cli/test_yoyopod_cli_remote_validate.py` - remote validation flag tests.
- Create: `tests/core/test_rust_ui_worker_contract.py` - host contract test that runs the Rust worker when Cargo is available.

The first implementation must not import or call the Python `WhisPlay` runtime path for rendering. A discovery command may read driver paths or environment variables, but the PoC output path is Rust-owned.

---

### Task 1: Scaffold Rust Worker Crate And Protocol

**Files:**
- Create: `workers/ui/rust/Cargo.toml`
- Create: `workers/ui/rust/src/main.rs`
- Create: `workers/ui/rust/src/protocol.rs`
- Modify: `.gitignore`

- [ ] **Step 1: Add Cargo target ignores**

Add these lines to `.gitignore` near the build/cache entries:

```gitignore
# Rust
target/
Cargo.lock
```

Do not ignore `workers/ui/rust/Cargo.lock` if the team decides to commit Rust lockfiles for application binaries. For this PoC, leave `Cargo.lock` ignored to match the current `uv.lock` policy.

- [ ] **Step 2: Create the Rust crate manifest**

Create `workers/ui/rust/Cargo.toml`:

```toml
[package]
name = "yoyopod-rust-ui-poc"
version = "0.1.0"
edition = "2021"
rust-version = "1.82"

[dependencies]
anyhow = "1.0"
clap = { version = "4.5", features = ["derive"] }
embedded-graphics = "0.8.2"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
thiserror = "2.0"

[target.'cfg(target_os = "linux")'.dependencies]
rppal = { version = "0.22.1", optional = true }

[features]
default = []
whisplay-hardware = ["dep:rppal"]
```

- [ ] **Step 3: Write protocol tests first**

Create `workers/ui/rust/src/protocol.rs` with the test module first:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn decode_accepts_spec_style_command_without_schema_version() {
        let line = br#"{"kind":"command","type":"ui.show_test_scene","payload":{"counter":7}}"#;

        let envelope = Envelope::decode(line).expect("decode");

        assert_eq!(envelope.schema_version, SUPPORTED_SCHEMA_VERSION);
        assert_eq!(envelope.kind, EnvelopeKind::Command);
        assert_eq!(envelope.message_type, "ui.show_test_scene");
        assert_eq!(envelope.payload["counter"], json!(7));
    }

    #[test]
    fn encode_ready_event_terminates_with_newline() {
        let encoded = Envelope::event("ui.ready", json!({"width": 240, "height": 280}))
            .encode()
            .expect("encode");

        assert!(encoded.ends_with(b"\n"));
        assert!(std::str::from_utf8(&encoded).unwrap().contains("\"type\":\"ui.ready\""));
    }

    #[test]
    fn rejects_unknown_kind() {
        let err = Envelope::decode(br#"{"kind":"bogus","type":"ui.ready","payload":{}}"#)
            .expect_err("must reject invalid kind");

        assert!(err.to_string().contains("invalid JSON UI envelope"));
    }
}
```

- [ ] **Step 4: Run protocol tests and verify failure**

Run:

```bash
cd workers/ui/rust
cargo test protocol::tests -- --nocapture
```

Expected: FAIL because `Envelope`, `EnvelopeKind`, and `SUPPORTED_SCHEMA_VERSION` are not defined.

- [ ] **Step 5: Implement protocol module**

Add the implementation above the test module in `workers/ui/rust/src/protocol.rs`:

```rust
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use thiserror::Error;

pub const SUPPORTED_SCHEMA_VERSION: u16 = 1;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EnvelopeKind {
    Command,
    Event,
    Error,
    Heartbeat,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Envelope {
    #[serde(default = "default_schema_version")]
    pub schema_version: u16,
    pub kind: EnvelopeKind,
    #[serde(rename = "type")]
    pub message_type: String,
    #[serde(default)]
    pub request_id: String,
    #[serde(default)]
    pub timestamp_ms: u64,
    #[serde(default)]
    pub deadline_ms: u64,
    #[serde(default = "empty_payload")]
    pub payload: Value,
}

#[derive(Debug, Error)]
pub enum ProtocolError {
    #[error("invalid JSON UI envelope: {0}")]
    InvalidJson(#[from] serde_json::Error),
    #[error("unsupported schema_version {actual}; expected {expected}")]
    UnsupportedSchema { actual: u16, expected: u16 },
    #[error("invalid envelope kind or payload: {0}")]
    InvalidEnvelope(String),
}

fn default_schema_version() -> u16 {
    SUPPORTED_SCHEMA_VERSION
}

fn empty_payload() -> Value {
    json!({})
}

impl Envelope {
    pub fn decode(line: &[u8]) -> Result<Self, ProtocolError> {
        let envelope: Envelope = serde_json::from_slice(line)?;
        envelope.validate()?;
        Ok(envelope)
    }

    pub fn encode(&self) -> Result<Vec<u8>, ProtocolError> {
        self.validate()?;
        let mut encoded = serde_json::to_vec(self)?;
        encoded.push(b'\n');
        Ok(encoded)
    }

    pub fn event(message_type: impl Into<String>, payload: Value) -> Self {
        Self {
            schema_version: SUPPORTED_SCHEMA_VERSION,
            kind: EnvelopeKind::Event,
            message_type: message_type.into(),
            request_id: String::new(),
            timestamp_ms: monotonic_millis(),
            deadline_ms: 0,
            payload,
        }
    }

    pub fn error(code: impl Into<String>, message: impl Into<String>) -> Self {
        Self::event(
            "ui.error",
            json!({
                "code": code.into(),
                "message": message.into(),
            }),
        )
    }

    pub fn validate(&self) -> Result<(), ProtocolError> {
        if self.schema_version != SUPPORTED_SCHEMA_VERSION {
            return Err(ProtocolError::UnsupportedSchema {
                actual: self.schema_version,
                expected: SUPPORTED_SCHEMA_VERSION,
            });
        }
        if self.message_type.trim().is_empty() {
            return Err(ProtocolError::InvalidEnvelope(
                "envelope type must be a non-empty string".to_string(),
            ));
        }
        if !self.payload.is_object() {
            return Err(ProtocolError::InvalidEnvelope(
                "payload must be a JSON object".to_string(),
            ));
        }
        Ok(())
    }
}

pub fn monotonic_millis() -> u64 {
    use std::sync::OnceLock;
    use std::time::Instant;

    static START: OnceLock<Instant> = OnceLock::new();
    START.get_or_init(Instant::now).elapsed().as_millis() as u64
}
```

- [ ] **Step 6: Create entrypoint shell**

Create `workers/ui/rust/src/main.rs`:

```rust
mod protocol;

use anyhow::Result;
use clap::{Parser, ValueEnum};

#[derive(Debug, Clone, Copy, ValueEnum)]
enum HardwareMode {
    Mock,
    Whisplay,
}

#[derive(Debug, Parser)]
#[command(name = "yoyopod-rust-ui-poc")]
#[command(about = "Whisplay-only Rust UI hardware I/O proof of concept")]
struct Args {
    #[arg(long, value_enum, default_value_t = HardwareMode::Mock)]
    hardware: HardwareMode,
}

fn main() -> Result<()> {
    let args = Args::parse();
    eprintln!("yoyopod-rust-ui-poc starting hardware={:?}", args.hardware);

    let ready = protocol::Envelope::event(
        "ui.ready",
        serde_json::json!({
            "width": 240,
            "height": 280,
            "hardware": format!("{:?}", args.hardware).to_lowercase(),
        }),
    );
    print!("{}", String::from_utf8(ready.encode()?)?);
    Ok(())
}
```

- [ ] **Step 7: Run Rust tests**

Run:

```bash
cd workers/ui/rust
cargo test
```

Expected: PASS.

- [ ] **Step 8: Commit scaffold**

Run:

```bash
git add .gitignore workers/ui/rust
git commit -m "feat(ui): scaffold rust whisplay poc worker"
```

---

### Task 2: Port The One-Button Input Grammar To Rust

**Files:**
- Create: `workers/ui/rust/src/input.rs`
- Modify: `workers/ui/rust/src/main.rs`

- [ ] **Step 1: Add module import**

Modify `workers/ui/rust/src/main.rs`:

```rust
mod input;
mod protocol;
```

- [ ] **Step 2: Write input state-machine tests**

Create `workers/ui/rust/src/input.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn machine() -> OneButtonMachine {
        OneButtonMachine::new(ButtonTiming::default())
    }

    #[test]
    fn single_tap_emits_advance_after_double_tap_window() {
        let mut machine = machine();

        assert!(machine.observe(false, 0).is_empty());
        assert!(machine.observe(true, 10).is_empty());
        assert!(machine.observe(false, 80).is_empty());
        let events = machine.tick(381);

        assert_eq!(events, vec![InputEvent::advance(80)]);
    }

    #[test]
    fn double_tap_emits_select() {
        let mut machine = machine();

        machine.observe(true, 10);
        machine.observe(false, 80);
        machine.observe(true, 180);
        machine.observe(false, 230);
        let events = machine.tick(280);

        assert_eq!(events, vec![InputEvent::select(50)]);
        assert!(machine.tick(600).is_empty());
    }

    #[test]
    fn long_hold_emits_back_once_at_threshold() {
        let mut machine = machine();

        machine.observe(true, 100);
        let first = machine.tick(900);
        let second = machine.tick(950);
        let release = machine.observe(false, 1000);

        assert_eq!(first, vec![InputEvent::back(800)]);
        assert!(second.is_empty());
        assert!(release.iter().all(|event| event.action != InputAction::Back));
    }

    #[test]
    fn debounce_filters_short_transition_noise() {
        let mut machine = machine();

        machine.observe(true, 10);
        machine.observe(false, 30);
        let events = machine.tick(400);

        assert!(events.is_empty());
    }
}
```

- [ ] **Step 3: Run input tests and verify failure**

Run:

```bash
cd workers/ui/rust
cargo test input::tests -- --nocapture
```

Expected: FAIL because the input types are not implemented.

- [ ] **Step 4: Implement input grammar**

Add this implementation above the tests in `workers/ui/rust/src/input.rs`:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InputAction {
    Advance,
    Select,
    Back,
    PttPress,
    PttRelease,
}

impl InputAction {
    pub fn as_str(self) -> &'static str {
        match self {
            InputAction::Advance => "advance",
            InputAction::Select => "select",
            InputAction::Back => "back",
            InputAction::PttPress => "ptt_press",
            InputAction::PttRelease => "ptt_release",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InputEvent {
    pub action: InputAction,
    pub method: &'static str,
    pub timestamp_ms: u64,
    pub duration_ms: u64,
}

impl InputEvent {
    pub fn advance(timestamp_ms: u64) -> Self {
        Self {
            action: InputAction::Advance,
            method: "single_tap",
            timestamp_ms,
            duration_ms: 0,
        }
    }

    pub fn select(duration_ms: u64) -> Self {
        Self {
            action: InputAction::Select,
            method: "double_tap",
            timestamp_ms: 0,
            duration_ms,
        }
    }

    pub fn back(duration_ms: u64) -> Self {
        Self {
            action: InputAction::Back,
            method: "long_hold",
            timestamp_ms: 0,
            duration_ms,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct ButtonTiming {
    pub debounce_ms: u64,
    pub double_tap_ms: u64,
    pub long_hold_ms: u64,
}

impl Default for ButtonTiming {
    fn default() -> Self {
        Self {
            debounce_ms: 50,
            double_tap_ms: 300,
            long_hold_ms: 800,
        }
    }
}

#[derive(Debug, Clone)]
pub struct OneButtonMachine {
    timing: ButtonTiming,
    debounced_pressed: bool,
    raw_pressed: bool,
    raw_transition_at_ms: Option<u64>,
    press_start_ms: Option<u64>,
    pending_single_tap_ms: Option<u64>,
    double_tap_candidate: bool,
    hold_back_fired: bool,
}

impl OneButtonMachine {
    pub fn new(timing: ButtonTiming) -> Self {
        Self {
            timing,
            debounced_pressed: false,
            raw_pressed: false,
            raw_transition_at_ms: None,
            press_start_ms: None,
            pending_single_tap_ms: None,
            double_tap_candidate: false,
            hold_back_fired: false,
        }
    }

    pub fn observe(&mut self, pressed: bool, now_ms: u64) -> Vec<InputEvent> {
        let events = self.advance(now_ms);
        if pressed != self.raw_pressed {
            self.raw_pressed = pressed;
            self.raw_transition_at_ms = Some(now_ms);
        }
        events
    }

    pub fn tick(&mut self, now_ms: u64) -> Vec<InputEvent> {
        self.advance(now_ms)
    }

    fn advance(&mut self, now_ms: u64) -> Vec<InputEvent> {
        let mut events = Vec::new();

        if let Some(transition_at_ms) = self.raw_transition_at_ms {
            if now_ms.saturating_sub(transition_at_ms) >= self.timing.debounce_ms {
                self.raw_transition_at_ms = None;
                if self.raw_pressed != self.debounced_pressed {
                    if self.raw_pressed {
                        events.extend(self.handle_press(transition_at_ms));
                    } else {
                        events.extend(self.handle_release(transition_at_ms));
                    }
                }
            }
        }

        if self.debounced_pressed && !self.hold_back_fired {
            if let Some(press_start_ms) = self.press_start_ms {
                let duration = now_ms.saturating_sub(press_start_ms);
                if duration >= self.timing.long_hold_ms {
                    self.hold_back_fired = true;
                    events.push(InputEvent::back(duration));
                }
            }
        }

        if !self.debounced_pressed {
            if let Some(pending_ms) = self.pending_single_tap_ms {
                if now_ms.saturating_sub(pending_ms) >= self.timing.double_tap_ms {
                    self.pending_single_tap_ms = None;
                    events.push(InputEvent::advance(pending_ms));
                }
            }
        }

        events
    }

    fn handle_press(&mut self, now_ms: u64) -> Vec<InputEvent> {
        let mut events = Vec::new();
        self.debounced_pressed = true;
        self.double_tap_candidate = self
            .pending_single_tap_ms
            .map(|pending| now_ms.saturating_sub(pending) < self.timing.double_tap_ms)
            .unwrap_or(false);
        if !self.double_tap_candidate {
            if let Some(pending) = self.pending_single_tap_ms.take() {
                events.push(InputEvent::advance(pending));
            }
        }
        self.press_start_ms = Some(now_ms);
        self.hold_back_fired = false;
        events
    }

    fn handle_release(&mut self, now_ms: u64) -> Vec<InputEvent> {
        self.debounced_pressed = false;
        let duration = self
            .press_start_ms
            .map(|started| now_ms.saturating_sub(started))
            .unwrap_or(0);
        self.press_start_ms = None;

        if self.hold_back_fired || duration >= self.timing.long_hold_ms {
            self.pending_single_tap_ms = None;
            self.double_tap_candidate = false;
            self.hold_back_fired = false;
            return Vec::new();
        }

        if self.double_tap_candidate {
            self.pending_single_tap_ms = None;
            self.double_tap_candidate = false;
            return vec![InputEvent::select(duration)];
        }

        self.pending_single_tap_ms = Some(now_ms);
        self.double_tap_candidate = false;
        Vec::new()
    }
}
```

- [ ] **Step 5: Run input tests**

Run:

```bash
cd workers/ui/rust
cargo test input::tests -- --nocapture
```

Expected: PASS.

- [ ] **Step 6: Commit input grammar**

Run:

```bash
git add workers/ui/rust/src/main.rs workers/ui/rust/src/input.rs
git commit -m "feat(ui): add rust one-button input grammar"
```

---

### Task 3: Add RGB565 Framebuffer And Test Renderer

**Files:**
- Create: `workers/ui/rust/src/framebuffer.rs`
- Create: `workers/ui/rust/src/render.rs`
- Modify: `workers/ui/rust/src/main.rs`

- [ ] **Step 1: Register modules**

Modify `workers/ui/rust/src/main.rs`:

```rust
mod framebuffer;
mod input;
mod protocol;
mod render;
```

- [ ] **Step 2: Write framebuffer tests**

Create `workers/ui/rust/src/framebuffer.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn packs_rgb888_to_rgb565_big_endian_bytes() {
        assert_eq!(rgb565(255, 0, 0), 0xF800);
        assert_eq!(rgb565(0, 255, 0), 0x07E0);
        assert_eq!(rgb565(0, 0, 255), 0x001F);
    }

    #[test]
    fn fills_rectangle_inside_bounds() {
        let mut fb = Framebuffer::new(4, 3);
        fb.clear(rgb565(0, 0, 0));
        fb.fill_rect(1, 1, 2, 1, rgb565(255, 0, 0));

        assert_eq!(fb.pixel(0, 1), rgb565(0, 0, 0));
        assert_eq!(fb.pixel(1, 1), rgb565(255, 0, 0));
        assert_eq!(fb.pixel(2, 1), rgb565(255, 0, 0));
        assert_eq!(fb.pixel(3, 1), rgb565(0, 0, 0));
    }
}
```

- [ ] **Step 3: Implement framebuffer**

Add above the tests in `workers/ui/rust/src/framebuffer.rs`:

```rust
pub fn rgb565(red: u8, green: u8, blue: u8) -> u16 {
    let r = ((red as u16) >> 3) & 0x1F;
    let g = ((green as u16) >> 2) & 0x3F;
    let b = ((blue as u16) >> 3) & 0x1F;
    (r << 11) | (g << 5) | b
}

#[derive(Debug, Clone)]
pub struct Framebuffer {
    width: usize,
    height: usize,
    pixels: Vec<u16>,
}

impl Framebuffer {
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            pixels: vec![0; width * height],
        }
    }

    pub fn width(&self) -> usize {
        self.width
    }

    pub fn height(&self) -> usize {
        self.height
    }

    pub fn clear(&mut self, color: u16) {
        self.pixels.fill(color);
    }

    pub fn pixel(&self, x: usize, y: usize) -> u16 {
        self.pixels[y * self.width + x]
    }

    pub fn set_pixel(&mut self, x: usize, y: usize, color: u16) {
        if x < self.width && y < self.height {
            self.pixels[y * self.width + x] = color;
        }
    }

    pub fn fill_rect(&mut self, x: usize, y: usize, width: usize, height: usize, color: u16) {
        let max_y = (y + height).min(self.height);
        let max_x = (x + width).min(self.width);
        for yy in y..max_y {
            for xx in x..max_x {
                self.set_pixel(xx, yy, color);
            }
        }
    }

    pub fn as_be_bytes(&self) -> Vec<u8> {
        let mut out = Vec::with_capacity(self.pixels.len() * 2);
        for pixel in &self.pixels {
            out.extend_from_slice(&pixel.to_be_bytes());
        }
        out
    }
}
```

- [ ] **Step 4: Write renderer tests**

Create `workers/ui/rust/src/render.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::framebuffer::{rgb565, Framebuffer};

    #[test]
    fn test_scene_changes_with_counter() {
        let mut first = Framebuffer::new(240, 280);
        let mut second = Framebuffer::new(240, 280);

        render_test_scene(&mut first, 1);
        render_test_scene(&mut second, 2);

        assert_ne!(first.as_be_bytes(), second.as_be_bytes());
        assert_eq!(first.pixel(0, 0), rgb565(8, 10, 14));
    }
}
```

- [ ] **Step 5: Implement deterministic renderer**

Add above the tests in `workers/ui/rust/src/render.rs`:

```rust
use crate::framebuffer::{rgb565, Framebuffer};

pub fn render_test_scene(framebuffer: &mut Framebuffer, counter: u64) {
    framebuffer.clear(rgb565(8, 10, 14));
    framebuffer.fill_rect(12, 16, 216, 52, rgb565(34, 48, 70));
    framebuffer.fill_rect(18, 24, 36, 36, rgb565(46, 204, 113));
    framebuffer.fill_rect(64, 28, 130, 8, rgb565(230, 236, 245));
    framebuffer.fill_rect(64, 44, 96, 6, rgb565(126, 140, 160));

    let bar_width = 24 + ((counter as usize * 17) % 168);
    framebuffer.fill_rect(18, 92, 204, 16, rgb565(30, 42, 58));
    framebuffer.fill_rect(18, 92, bar_width, 16, rgb565(255, 207, 64));

    let block = ((counter % 5) as usize) * 34;
    framebuffer.fill_rect(36 + block, 140, 28, 28, rgb565(99, 180, 255));
    framebuffer.fill_rect(36, 218, 168, 10, rgb565(72, 86, 104));
    framebuffer.fill_rect(36, 238, 92, 10, rgb565(72, 86, 104));
}
```

- [ ] **Step 6: Run framebuffer and renderer tests**

Run:

```bash
cd workers/ui/rust
cargo test framebuffer::tests render::tests -- --nocapture
```

Expected: PASS.

- [ ] **Step 7: Commit renderer**

Run:

```bash
git add workers/ui/rust/src/main.rs workers/ui/rust/src/framebuffer.rs workers/ui/rust/src/render.rs
git commit -m "feat(ui): add rust rgb565 test renderer"
```

---

### Task 4: Add Rust Worker Loop With Mock Hardware

**Files:**
- Create: `workers/ui/rust/src/hardware/mod.rs`
- Create: `workers/ui/rust/src/hardware/mock.rs`
- Create: `workers/ui/rust/src/worker.rs`
- Modify: `workers/ui/rust/src/main.rs`

- [ ] **Step 1: Register modules**

Modify `workers/ui/rust/src/main.rs`:

```rust
mod framebuffer;
mod hardware;
mod input;
mod protocol;
mod render;
mod worker;
```

- [ ] **Step 2: Define hardware traits**

Create `workers/ui/rust/src/hardware/mod.rs`:

```rust
pub mod mock;

#[cfg(all(target_os = "linux", feature = "whisplay-hardware"))]
pub mod whisplay;

use anyhow::Result;
use crate::framebuffer::Framebuffer;

pub trait DisplayDevice {
    fn width(&self) -> usize;
    fn height(&self) -> usize;
    fn flush_full_frame(&mut self, framebuffer: &Framebuffer) -> Result<()>;
    fn set_backlight(&mut self, brightness: f32) -> Result<()>;
}

pub trait ButtonDevice {
    fn pressed(&mut self) -> Result<bool>;
}
```

- [ ] **Step 3: Add mock hardware**

Create `workers/ui/rust/src/hardware/mock.rs`:

```rust
use anyhow::Result;

use crate::framebuffer::Framebuffer;
use crate::hardware::{ButtonDevice, DisplayDevice};

#[derive(Debug)]
pub struct MockDisplay {
    width: usize,
    height: usize,
    pub frames: usize,
}

impl MockDisplay {
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            frames: 0,
        }
    }
}

impl DisplayDevice for MockDisplay {
    fn width(&self) -> usize {
        self.width
    }

    fn height(&self) -> usize {
        self.height
    }

    fn flush_full_frame(&mut self, _framebuffer: &Framebuffer) -> Result<()> {
        self.frames += 1;
        Ok(())
    }

    fn set_backlight(&mut self, _brightness: f32) -> Result<()> {
        Ok(())
    }
}

#[derive(Debug, Default)]
pub struct MockButton {
    pressed: bool,
}

impl MockButton {
    pub fn new() -> Self {
        Self::default()
    }
}

impl ButtonDevice for MockButton {
    fn pressed(&mut self) -> Result<bool> {
        Ok(self.pressed)
    }
}
```

- [ ] **Step 4: Write worker tests**

Create `workers/ui/rust/src/worker.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::hardware::mock::{MockButton, MockDisplay};

    #[test]
    fn worker_emits_ready_and_health_for_mock_hardware() {
        let input = br#"{"kind":"command","type":"ui.show_test_scene","payload":{"counter":3}}
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
        assert!(stdout.contains("\"type\":\"ui.ready\""));
        assert!(stdout.contains("\"type\":\"ui.health\""));
        assert!(stdout.contains("\"frames\":1"));
    }
}
```

- [ ] **Step 5: Implement worker loop**

Add above the tests in `workers/ui/rust/src/worker.rs`:

```rust
use std::io::{BufRead, BufReader, Read, Write};

use anyhow::Result;
use serde_json::json;

use crate::framebuffer::Framebuffer;
use crate::hardware::{ButtonDevice, DisplayDevice};
use crate::input::{ButtonTiming, OneButtonMachine};
use crate::protocol::Envelope;
use crate::render::render_test_scene;

pub fn run_worker<R, W, E, D, B>(
    input: R,
    output: &mut W,
    errors: &mut E,
    mut display: D,
    mut button: B,
) -> Result<()>
where
    R: Read,
    W: Write,
    E: Write,
    D: DisplayDevice,
    B: ButtonDevice,
{
    let mut framebuffer = Framebuffer::new(display.width(), display.height());
    let mut frames = 0usize;
    let mut input_events = 0usize;
    let mut button_machine = OneButtonMachine::new(ButtonTiming::default());

    emit(
        output,
        Envelope::event(
            "ui.ready",
            json!({
                "display": {"width": display.width(), "height": display.height()},
            }),
        ),
    )?;

    let reader = BufReader::new(input);
    for line in reader.lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }

        match Envelope::decode(line.as_bytes()) {
            Ok(envelope) => {
                if envelope.kind != crate::protocol::EnvelopeKind::Command {
                    emit(output, Envelope::error("invalid_kind", "worker accepts commands only"))?;
                    continue;
                }

                match envelope.message_type.as_str() {
                    "ui.show_test_scene" => {
                        let counter = envelope
                            .payload
                            .get("counter")
                            .and_then(|value| value.as_u64())
                            .unwrap_or(frames as u64 + 1);
                        render_test_scene(&mut framebuffer, counter);
                        display.flush_full_frame(&framebuffer)?;
                        frames += 1;
                    }
                    "ui.set_backlight" => {
                        let brightness = envelope
                            .payload
                            .get("brightness")
                            .and_then(|value| value.as_f64())
                            .unwrap_or(0.8) as f32;
                        display.set_backlight(brightness.clamp(0.0, 1.0))?;
                    }
                    "ui.poll_input" => {
                        let pressed = button.pressed()?;
                        let now = crate::protocol::monotonic_millis();
                        for event in button_machine.observe(pressed, now) {
                            input_events += 1;
                            emit(
                                output,
                                Envelope::event(
                                    "ui.input",
                                    json!({
                                        "action": event.action.as_str(),
                                        "method": event.method,
                                        "timestamp_ms": event.timestamp_ms,
                                        "duration_ms": event.duration_ms,
                                    }),
                                ),
                            )?;
                        }
                    }
                    "ui.health" => {
                        emit(
                            output,
                            Envelope::event(
                                "ui.health",
                                json!({
                                    "frames": frames,
                                    "button_events": input_events,
                                }),
                            ),
                        )?;
                    }
                    "ui.shutdown" | "worker.stop" => break,
                    other => {
                        writeln!(errors, "unknown UI worker command: {other}")?;
                        emit(output, Envelope::error("unknown_command", other))?;
                    }
                }
            }
            Err(err) => {
                writeln!(errors, "protocol decode error: {err}")?;
                emit(output, Envelope::error("decode_error", err.to_string()))?;
            }
        }
    }

    Ok(())
}

fn emit<W: Write>(output: &mut W, envelope: Envelope) -> Result<()> {
    output.write_all(&envelope.encode()?)?;
    output.flush()?;
    Ok(())
}
```

- [ ] **Step 6: Wire main to mock worker**

Replace `workers/ui/rust/src/main.rs` with:

```rust
mod framebuffer;
mod hardware;
mod input;
mod protocol;
mod render;
mod worker;

use anyhow::Result;
use clap::{Parser, ValueEnum};

#[derive(Debug, Clone, Copy, ValueEnum)]
enum HardwareMode {
    Mock,
    Whisplay,
}

#[derive(Debug, Parser)]
#[command(name = "yoyopod-rust-ui-poc")]
#[command(about = "Whisplay-only Rust UI hardware I/O proof of concept")]
struct Args {
    #[arg(long, value_enum, default_value_t = HardwareMode::Mock)]
    hardware: HardwareMode,
}

fn main() -> Result<()> {
    let args = Args::parse();
    match args.hardware {
        HardwareMode::Mock => {
            let display = hardware::mock::MockDisplay::new(240, 280);
            let button = hardware::mock::MockButton::new();
            let stdin = std::io::stdin();
            let mut stdout = std::io::stdout();
            let mut stderr = std::io::stderr();
            worker::run_worker(stdin, &mut stdout, &mut stderr, display, button)
        }
        HardwareMode::Whisplay => {
            #[cfg(all(target_os = "linux", feature = "whisplay-hardware"))]
            {
                let (display, button) = hardware::whisplay::open_from_env()?;
                let stdin = std::io::stdin();
                let mut stdout = std::io::stdout();
                let mut stderr = std::io::stderr();
                return worker::run_worker(stdin, &mut stdout, &mut stderr, display, button);
            }
            #[cfg(not(all(target_os = "linux", feature = "whisplay-hardware")))]
            {
                anyhow::bail!("whisplay hardware mode requires Linux and the whisplay-hardware feature");
            }
        }
    }
}
```

- [ ] **Step 7: Run worker tests**

Run:

```bash
cd workers/ui/rust
cargo test worker::tests -- --nocapture
```

Expected: PASS.

- [ ] **Step 8: Commit worker loop**

Run:

```bash
git add workers/ui/rust/src
git commit -m "feat(ui): add rust ui worker loop"
```

---

### Task 5: Add Linux Whisplay Hardware Backend

**Files:**
- Create: `workers/ui/rust/src/hardware/whisplay.rs`

- [ ] **Step 1: Create hardware backend with explicit env configuration**

Create `workers/ui/rust/src/hardware/whisplay.rs`:

```rust
use anyhow::{Context, Result};
use rppal::gpio::{Gpio, InputPin, Level, OutputPin};
use rppal::spi::{Bus, Mode, SlaveSelect, Spi};

use crate::framebuffer::Framebuffer;
use crate::hardware::{ButtonDevice, DisplayDevice};

const WIDTH: usize = 240;
const HEIGHT: usize = 280;

pub struct WhisplayDisplay {
    spi: Spi,
    dc: OutputPin,
    reset: Option<OutputPin>,
    backlight: Option<OutputPin>,
}

pub struct WhisplayButton {
    pin: InputPin,
    active_low: bool,
}

pub fn open_from_env() -> Result<(WhisplayDisplay, WhisplayButton)> {
    let spi_bus = env_u8("YOYOPOD_WHISPLAY_SPI_BUS", 0)?;
    let spi_cs = env_u8("YOYOPOD_WHISPLAY_SPI_CS", 0)?;
    let spi_hz = env_u32("YOYOPOD_WHISPLAY_SPI_HZ", 32_000_000)?;
    let dc_gpio = required_env_u8("YOYOPOD_WHISPLAY_DC_GPIO")?;
    let reset_gpio = optional_env_u8("YOYOPOD_WHISPLAY_RESET_GPIO")?;
    let backlight_gpio = optional_env_u8("YOYOPOD_WHISPLAY_BACKLIGHT_GPIO")?;
    let button_gpio = env_u8("YOYOPOD_WHISPLAY_BUTTON_GPIO", 26)?;
    let button_active_low = env_bool("YOYOPOD_WHISPLAY_BUTTON_ACTIVE_LOW", true)?;

    let spi = Spi::new(spi_bus(spi_bus)?, spi_cs(spi_cs)?, spi_hz, Mode::Mode0)
        .context("opening Whisplay SPI")?;
    let gpio = Gpio::new().context("opening GPIO")?;
    let dc = gpio.get(dc_gpio)?.into_output();
    let reset = match reset_gpio {
        Some(pin) => Some(gpio.get(pin)?.into_output()),
        None => None,
    };
    let backlight = match backlight_gpio {
        Some(pin) => Some(gpio.get(pin)?.into_output()),
        None => None,
    };
    let button = gpio.get(button_gpio)?.into_input_pullup();

    let mut display = WhisplayDisplay {
        spi,
        dc,
        reset,
        backlight,
    };
    display.init_panel()?;

    Ok((
        display,
        WhisplayButton {
            pin: button,
            active_low: button_active_low,
        },
    ))
}

impl WhisplayDisplay {
    fn init_panel(&mut self) -> Result<()> {
        if let Some(reset) = self.reset.as_mut() {
            reset.set_low();
            std::thread::sleep(std::time::Duration::from_millis(30));
            reset.set_high();
            std::thread::sleep(std::time::Duration::from_millis(120));
        }

        self.command(0x01, &[])?; // software reset
        std::thread::sleep(std::time::Duration::from_millis(150));
        self.command(0x11, &[])?; // sleep out
        std::thread::sleep(std::time::Duration::from_millis(120));
        self.command(0x3A, &[0x55])?; // RGB565
        self.command(0x36, &[0x00])?; // memory access control, portrait baseline
        self.command(0x29, &[])?; // display on
        std::thread::sleep(std::time::Duration::from_millis(20));
        Ok(())
    }

    fn command(&mut self, command: u8, data: &[u8]) -> Result<()> {
        self.dc.set_low();
        self.spi.write(&[command])?;
        if !data.is_empty() {
            self.dc.set_high();
            self.spi.write(data)?;
        }
        Ok(())
    }

    fn set_address_window(&mut self, x0: u16, y0: u16, x1: u16, y1: u16) -> Result<()> {
        let mut x_data = [0u8; 4];
        x_data[0..2].copy_from_slice(&x0.to_be_bytes());
        x_data[2..4].copy_from_slice(&x1.to_be_bytes());
        self.command(0x2A, &x_data)?;

        let mut y_data = [0u8; 4];
        y_data[0..2].copy_from_slice(&y0.to_be_bytes());
        y_data[2..4].copy_from_slice(&y1.to_be_bytes());
        self.command(0x2B, &y_data)?;
        self.command(0x2C, &[])?;
        Ok(())
    }
}

impl DisplayDevice for WhisplayDisplay {
    fn width(&self) -> usize {
        WIDTH
    }

    fn height(&self) -> usize {
        HEIGHT
    }

    fn flush_full_frame(&mut self, framebuffer: &Framebuffer) -> Result<()> {
        self.set_address_window(0, 0, (WIDTH - 1) as u16, (HEIGHT - 1) as u16)?;
        self.dc.set_high();
        self.spi.write(&framebuffer.as_be_bytes())?;
        Ok(())
    }

    fn set_backlight(&mut self, brightness: f32) -> Result<()> {
        if let Some(pin) = self.backlight.as_mut() {
            if brightness > 0.0 {
                pin.set_high();
            } else {
                pin.set_low();
            }
        }
        Ok(())
    }
}

impl ButtonDevice for WhisplayButton {
    fn pressed(&mut self) -> Result<bool> {
        let is_low = self.pin.read() == Level::Low;
        Ok(if self.active_low { is_low } else { !is_low })
    }
}

fn required_env_u8(name: &str) -> Result<u8> {
    let value = std::env::var(name).with_context(|| format!("{name} is required"))?;
    value.parse::<u8>().with_context(|| format!("parsing {name}={value}"))
}

fn optional_env_u8(name: &str) -> Result<Option<u8>> {
    match std::env::var(name) {
        Ok(value) if !value.trim().is_empty() => Ok(Some(
            value.parse::<u8>().with_context(|| format!("parsing {name}={value}"))?,
        )),
        _ => Ok(None),
    }
}

fn env_u8(name: &str, default: u8) -> Result<u8> {
    match std::env::var(name) {
        Ok(value) if !value.trim().is_empty() => {
            value.parse::<u8>().with_context(|| format!("parsing {name}={value}"))
        }
        _ => Ok(default),
    }
}

fn env_u32(name: &str, default: u32) -> Result<u32> {
    match std::env::var(name) {
        Ok(value) if !value.trim().is_empty() => {
            value.parse::<u32>().with_context(|| format!("parsing {name}={value}"))
        }
        _ => Ok(default),
    }
}

fn env_bool(name: &str, default: bool) -> Result<bool> {
    match std::env::var(name) {
        Ok(value) if !value.trim().is_empty() => match value.to_ascii_lowercase().as_str() {
            "1" | "true" | "yes" | "on" => Ok(true),
            "0" | "false" | "no" | "off" => Ok(false),
            _ => anyhow::bail!("parsing {name}={value} as bool"),
        },
        _ => Ok(default),
    }
}

fn spi_bus(value: u8) -> Result<Bus> {
    match value {
        0 => Ok(Bus::Spi0),
        1 => Ok(Bus::Spi1),
        _ => anyhow::bail!("unsupported SPI bus {value}"),
    }
}

fn spi_cs(value: u8) -> Result<SlaveSelect> {
    match value {
        0 => Ok(SlaveSelect::Ss0),
        1 => Ok(SlaveSelect::Ss1),
        _ => anyhow::bail!("unsupported SPI chip select {value}"),
    }
}
```

- [ ] **Step 2: Build hardware feature on Linux**

On Linux or the Pi, run:

```bash
cd workers/ui/rust
cargo build --features whisplay-hardware
```

Expected: PASS. On Windows, this step is skipped because `rppal` hardware is Linux-specific.

- [ ] **Step 3: Run default tests on the host**

Run:

```bash
cd workers/ui/rust
cargo test
```

Expected: PASS without the `whisplay-hardware` feature.

- [ ] **Step 4: Commit hardware backend**

Run:

```bash
git add workers/ui/rust/src/hardware workers/ui/rust/Cargo.toml
git commit -m "feat(ui): add rust whisplay hardware backend"
```

---

### Task 6: Add Python Protocol And Supervisor

**Files:**
- Create: `yoyopod/ui/rust_sidecar/__init__.py`
- Create: `yoyopod/ui/rust_sidecar/protocol.py`
- Create: `yoyopod/ui/rust_sidecar/supervisor.py`
- Create: `tests/ui/test_rust_sidecar_protocol.py`
- Create: `tests/ui/test_rust_sidecar_supervisor.py`

- [ ] **Step 1: Write Python protocol tests**

Create `tests/ui/test_rust_sidecar_protocol.py`:

```python
from __future__ import annotations

import pytest

from yoyopod.ui.rust_sidecar.protocol import UiEnvelope, UiProtocolError


def test_parse_ready_event_defaults_schema_version() -> None:
    envelope = UiEnvelope.from_json_line(
        '{"kind":"event","type":"ui.ready","payload":{"display":{"width":240}}}'
    )

    assert envelope.schema_version == 1
    assert envelope.kind == "event"
    assert envelope.type == "ui.ready"
    assert envelope.payload["display"]["width"] == 240


def test_command_encoder_uses_ui_prefix() -> None:
    line = UiEnvelope.command("ui.health").to_json_line()

    assert line.endswith("\n")
    assert '"kind":"command"' in line
    assert '"type":"ui.health"' in line


def test_rejects_non_object_payload() -> None:
    with pytest.raises(UiProtocolError, match="payload"):
        UiEnvelope.from_json_line('{"kind":"event","type":"ui.ready","payload":[]}')
```

- [ ] **Step 2: Implement Python protocol**

Create `yoyopod/ui/rust_sidecar/protocol.py`:

```python
"""Line-delimited JSON protocol for the Rust UI PoC sidecar."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import time
from typing import Any

SUPPORTED_SCHEMA_VERSION = 1
VALID_KINDS = {"command", "event", "error", "heartbeat"}


class UiProtocolError(ValueError):
    """Raised when a Rust UI sidecar envelope is malformed."""


@dataclass(frozen=True, slots=True)
class UiEnvelope:
    kind: str
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    schema_version: int = SUPPORTED_SCHEMA_VERSION
    request_id: str = ""
    timestamp_ms: int = 0
    deadline_ms: int = 0

    @classmethod
    def command(
        cls,
        message_type: str,
        payload: dict[str, Any] | None = None,
        *,
        request_id: str = "",
    ) -> "UiEnvelope":
        return cls(
            kind="command",
            type=message_type,
            payload=payload or {},
            request_id=request_id,
            timestamp_ms=int(time.monotonic() * 1000),
        )

    @classmethod
    def from_json_line(cls, line: str) -> "UiEnvelope":
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise UiProtocolError(f"invalid JSON UI envelope: {exc}") from exc

        if not isinstance(raw, dict):
            raise UiProtocolError("UI envelope must be a JSON object")

        envelope = cls(
            schema_version=int(raw.get("schema_version", SUPPORTED_SCHEMA_VERSION)),
            kind=str(raw.get("kind", "")),
            type=str(raw.get("type", "")),
            request_id=str(raw.get("request_id", "")),
            timestamp_ms=int(raw.get("timestamp_ms", 0)),
            deadline_ms=int(raw.get("deadline_ms", 0)),
            payload=raw.get("payload", {}),
        )
        envelope.validate()
        return envelope

    def to_json_line(self) -> str:
        self.validate()
        return json.dumps(
            {
                "schema_version": self.schema_version,
                "kind": self.kind,
                "type": self.type,
                "request_id": self.request_id,
                "timestamp_ms": self.timestamp_ms,
                "deadline_ms": self.deadline_ms,
                "payload": self.payload,
            },
            separators=(",", ":"),
        ) + "\n"

    def validate(self) -> None:
        if self.schema_version != SUPPORTED_SCHEMA_VERSION:
            raise UiProtocolError(
                f"unsupported schema_version {self.schema_version}; "
                f"expected {SUPPORTED_SCHEMA_VERSION}"
            )
        if self.kind not in VALID_KINDS:
            raise UiProtocolError(f"invalid UI envelope kind {self.kind!r}")
        if not self.type:
            raise UiProtocolError("UI envelope type must be non-empty")
        if not isinstance(self.payload, dict):
            raise UiProtocolError("UI envelope payload must be an object")
```

- [ ] **Step 3: Export protocol types**

Create `yoyopod/ui/rust_sidecar/__init__.py`:

```python
"""Rust UI PoC sidecar integration helpers."""

from yoyopod.ui.rust_sidecar.protocol import UiEnvelope, UiProtocolError

__all__ = ["UiEnvelope", "UiProtocolError"]
```

- [ ] **Step 4: Run protocol tests**

Run:

```bash
uv run pytest -q tests/ui/test_rust_sidecar_protocol.py
```

Expected: PASS.

- [ ] **Step 5: Write supervisor tests**

Create `tests/ui/test_rust_sidecar_supervisor.py`:

```python
from __future__ import annotations

from io import StringIO
from pathlib import Path
from unittest.mock import Mock

from yoyopod.ui.rust_sidecar.protocol import UiEnvelope
from yoyopod.ui.rust_sidecar.supervisor import RustUiSidecarSupervisor


class _FakeProcess:
    def __init__(self) -> None:
        self.stdin = StringIO()
        self.stdout = StringIO(
            UiEnvelope(kind="event", type="ui.ready", payload={"display": {"width": 240}}).to_json_line()
        )
        self.stderr = StringIO()
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self.returncode = 0
        return 0

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9


def test_supervisor_starts_and_sends_shutdown(monkeypatch) -> None:
    fake = _FakeProcess()
    popen = Mock(return_value=fake)
    monkeypatch.setattr("yoyopod.ui.rust_sidecar.supervisor.subprocess.Popen", popen)

    supervisor = RustUiSidecarSupervisor(argv=[str(Path("worker"))])
    ready = supervisor.start()
    supervisor.send(UiEnvelope.command("ui.shutdown"))
    supervisor.stop()

    assert ready.type == "ui.ready"
    assert '"type":"ui.shutdown"' in fake.stdin.getvalue()
    assert fake.terminated
    popen.assert_called_once()
```

- [ ] **Step 6: Implement supervisor**

Create `yoyopod/ui/rust_sidecar/supervisor.py`:

```python
"""Subprocess supervisor for the Rust UI PoC sidecar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from yoyopod.ui.rust_sidecar.protocol import UiEnvelope, UiProtocolError


class RustUiSidecarError(RuntimeError):
    """Raised when the Rust UI sidecar cannot be controlled."""


@dataclass(slots=True)
class RustUiSidecarSupervisor:
    argv: list[str]
    cwd: Path | None = None
    ready_timeout_seconds: float = 5.0
    process: subprocess.Popen[str] | None = None

    def start(self) -> UiEnvelope:
        if self.process is not None and self.process.poll() is None:
            raise RustUiSidecarError("Rust UI sidecar is already running")

        self.process = subprocess.Popen(
            self.argv,
            cwd=str(self.cwd) if self.cwd is not None else None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        return self.read_event()

    def send(self, envelope: UiEnvelope) -> None:
        process = self._require_process()
        if process.stdin is None:
            raise RustUiSidecarError("Rust UI sidecar stdin is not available")
        process.stdin.write(envelope.to_json_line())
        process.stdin.flush()

    def read_event(self) -> UiEnvelope:
        process = self._require_process()
        if process.stdout is None:
            raise RustUiSidecarError("Rust UI sidecar stdout is not available")
        line = process.stdout.readline()
        if not line:
            raise RustUiSidecarError("Rust UI sidecar exited before emitting an event")
        try:
            return UiEnvelope.from_json_line(line)
        except UiProtocolError as exc:
            raise RustUiSidecarError(str(exc)) from exc

    def stop(self, timeout_seconds: float = 2.0) -> None:
        process = self.process
        if process is None:
            return
        if process.poll() is None:
            try:
                self.send(UiEnvelope.command("ui.shutdown"))
            except Exception:
                pass
            process.terminate()
            try:
                process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1.0)
        self.process = None

    def _require_process(self) -> subprocess.Popen[str]:
        if self.process is None:
            raise RustUiSidecarError("Rust UI sidecar is not running")
        return self.process
```

- [ ] **Step 7: Run supervisor tests**

Run:

```bash
uv run pytest -q tests/ui/test_rust_sidecar_protocol.py tests/ui/test_rust_sidecar_supervisor.py
```

Expected: PASS.

- [ ] **Step 8: Commit Python sidecar support**

Run:

```bash
git add yoyopod/ui/rust_sidecar tests/ui/test_rust_sidecar_protocol.py tests/ui/test_rust_sidecar_supervisor.py
git commit -m "feat(ui): add python rust ui sidecar supervisor"
```

---

### Task 7: Add Build Command For Rust UI PoC

**Files:**
- Modify: `yoyopod_cli/build.py`
- Modify: `tests/cli/test_yoyopod_cli_build.py`

- [ ] **Step 1: Add build command tests**

Append to `tests/cli/test_yoyopod_cli_build.py`:

```python
def test_rust_ui_poc_build_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["rust-ui-poc", "--help"])

    assert result.exit_code == 0
    assert "rust ui poc" in result.output.lower()


def test_build_rust_ui_poc_invokes_cargo(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], Path | None, dict[str, str] | None]] = []
    monkeypatch.setattr(
        build_cli,
        "_run",
        lambda command, cwd=None, env=None: calls.append((command, cwd, env)),
    )

    output = build_cli.build_rust_ui_poc()

    assert output.name.startswith("yoyopod-rust-ui-poc")
    assert calls[0][0][:4] == ["cargo", "build", "--release", "--features"]
    assert calls[0][1] == build_cli._REPO_ROOT / "workers" / "ui" / "rust"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
uv run pytest -q tests/cli/test_yoyopod_cli_build.py::test_rust_ui_poc_build_help tests/cli/test_yoyopod_cli_build.py::test_build_rust_ui_poc_invokes_cargo
```

Expected: FAIL because the command and builder do not exist.

- [ ] **Step 3: Add builder helpers**

In `yoyopod_cli/build.py`, add near the voice worker helpers:

```python
def _rust_ui_poc_dir() -> Path:
    return _REPO_ROOT / "workers" / "ui" / "rust"


def _rust_ui_poc_binary_path() -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return _rust_ui_poc_dir() / "build" / f"yoyopod-rust-ui-poc{suffix}"


def build_rust_ui_poc(*, hardware_feature: bool = True) -> Path:
    """Build the Rust Whisplay UI PoC sidecar and return the copied binary path."""

    worker_dir = _rust_ui_poc_dir()
    output = _rust_ui_poc_binary_path()
    output.parent.mkdir(parents=True, exist_ok=True)

    command = ["cargo", "build", "--release"]
    if hardware_feature:
        command.extend(["--features", "whisplay-hardware"])
    _run(command, cwd=worker_dir)

    suffix = ".exe" if os.name == "nt" else ""
    built_binary = worker_dir / "target" / "release" / f"yoyopod-rust-ui-poc{suffix}"
    shutil.copy2(built_binary, output)
    return output
```

- [ ] **Step 4: Add Typer command**

In `yoyopod_cli/build.py`, add near `voice-worker`:

```python
@app.command("rust-ui-poc")
def build_rust_ui_poc_command(
    no_hardware_feature: Annotated[
        bool,
        typer.Option(
            "--no-hardware-feature",
            help="Build without the Linux Whisplay hardware feature for host-only protocol tests.",
        ),
    ] = False,
) -> None:
    """Build the Rust UI PoC worker."""

    output = build_rust_ui_poc(hardware_feature=not no_hardware_feature)
    typer.echo(f"Built Rust UI PoC worker: {output}")
```

- [ ] **Step 5: Run build command tests**

Run:

```bash
uv run pytest -q tests/cli/test_yoyopod_cli_build.py::test_rust_ui_poc_build_help tests/cli/test_yoyopod_cli_build.py::test_build_rust_ui_poc_invokes_cargo
```

Expected: PASS.

- [ ] **Step 6: Commit build command**

Run:

```bash
git add yoyopod_cli/build.py tests/cli/test_yoyopod_cli_build.py
git commit -m "feat(cli): build rust ui poc worker"
```

---

### Task 8: Add Pi PoC Validation Command

**Files:**
- Create: `yoyopod_cli/pi/rust_ui_poc.py`
- Modify: `yoyopod_cli/pi/__init__.py`
- Create: `tests/cli/test_pi_rust_ui_poc.py`

- [ ] **Step 1: Write CLI tests**

Create `tests/cli/test_pi_rust_ui_poc.py`:

```python
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from yoyopod_cli.pi import app
import yoyopod_cli.pi.rust_ui_poc as rust_ui_poc
from yoyopod.ui.rust_sidecar.protocol import UiEnvelope


class _FakeSupervisor:
    def __init__(self, argv: list[str], cwd: Path | None = None) -> None:
        self.argv = argv
        self.cwd = cwd
        self.sent: list[UiEnvelope] = []

    def start(self) -> UiEnvelope:
        return UiEnvelope(kind="event", type="ui.ready", payload={"display": {"width": 240}})

    def send(self, envelope: UiEnvelope) -> None:
        self.sent.append(envelope)

    def read_event(self) -> UiEnvelope:
        return UiEnvelope(kind="event", type="ui.health", payload={"frames": 1, "button_events": 0})

    def stop(self) -> None:
        return None


def test_rust_ui_poc_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["rust-ui-poc", "--help"])

    assert result.exit_code == 0
    assert "rust ui poc" in result.output.lower()


def test_rust_ui_poc_runs_supervisor(monkeypatch, tmp_path: Path) -> None:
    worker = tmp_path / "yoyopod-rust-ui-poc"
    worker.write_text("fake", encoding="utf-8")
    monkeypatch.setattr(rust_ui_poc, "RustUiSidecarSupervisor", _FakeSupervisor)

    runner = CliRunner()
    result = runner.invoke(app, ["rust-ui-poc", "--worker", str(worker), "--frames", "1"])

    assert result.exit_code == 0
    assert "ready" in result.output.lower()
    assert "frames=1" in result.output
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
uv run pytest -q tests/cli/test_pi_rust_ui_poc.py
```

Expected: FAIL because the command module is not registered.

- [ ] **Step 3: Implement command**

Create `yoyopod_cli/pi/rust_ui_poc.py`:

```python
"""Whisplay-only Rust UI PoC validation command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from yoyopod.ui.rust_sidecar.protocol import UiEnvelope
from yoyopod.ui.rust_sidecar.supervisor import RustUiSidecarSupervisor


def _default_worker_path() -> Path:
    suffix = ".exe" if __import__("os").name == "nt" else ""
    return Path("workers") / "ui" / "rust" / "build" / f"yoyopod-rust-ui-poc{suffix}"


def rust_ui_poc(
    worker: Annotated[
        Path,
        typer.Option("--worker", help="Path to the Rust UI PoC worker binary."),
    ] = _default_worker_path(),
    frames: Annotated[
        int,
        typer.Option("--frames", min=1, help="Number of test scene frames to send."),
    ] = 10,
    hardware: Annotated[
        str,
        typer.Option("--hardware", help="Worker hardware mode: mock or whisplay."),
    ] = "whisplay",
) -> None:
    """Run the Rust UI PoC against Whisplay hardware."""

    argv = [str(worker), "--hardware", hardware]
    supervisor = RustUiSidecarSupervisor(argv=argv)
    ready = supervisor.start()
    typer.echo(f"Rust UI PoC ready: {ready.payload}")

    try:
        for counter in range(1, frames + 1):
            supervisor.send(
                UiEnvelope.command(
                    "ui.show_test_scene",
                    {"counter": counter},
                    request_id=f"frame-{counter}",
                )
            )
        supervisor.send(UiEnvelope.command("ui.health", request_id="health"))
        health = supervisor.read_event()
        typer.echo(
            "Rust UI PoC health: "
            f"frames={health.payload.get('frames')} "
            f"button_events={health.payload.get('button_events')}"
        )
    finally:
        supervisor.stop()
```

- [ ] **Step 4: Register command**

Modify `yoyopod_cli/pi/__init__.py`:

```python
from yoyopod_cli.pi import (
    network as _network,
    power as _power,
    rust_ui_poc as _rust_ui_poc,
    validate as _validate,
    voip as _voip,
)
```

Then add:

```python
app.command(name="rust-ui-poc")(_rust_ui_poc.rust_ui_poc)
```

- [ ] **Step 5: Run CLI tests**

Run:

```bash
uv run pytest -q tests/cli/test_pi_rust_ui_poc.py
```

Expected: PASS.

- [ ] **Step 6: Commit Pi command**

Run:

```bash
git add yoyopod_cli/pi/rust_ui_poc.py yoyopod_cli/pi/__init__.py tests/cli/test_pi_rust_ui_poc.py
git commit -m "feat(cli): add rust ui poc pi command"
```

---

### Task 9: Add Remote Validation Flag

**Files:**
- Modify: `yoyopod_cli/remote_validate.py`
- Modify: `yoyopod_cli/main.py`
- Modify: `tests/cli/test_yoyopod_cli_remote_validate.py`

- [ ] **Step 1: Add remote validation builder test**

Append to `tests/cli/test_yoyopod_cli_remote_validate.py`:

```python
def test_build_validate_with_rust_ui_poc() -> None:
    shell = _build_validate(
        branch="feature",
        venv_relpath="venv",
        sha="",
        with_music=False,
        with_voip=False,
        with_power=False,
        with_rtc=False,
        with_cloud_voice=False,
        with_lvgl_soak=False,
        with_navigation=False,
        with_rust_ui_poc=True,
    )

    assert "venv/bin/python -m yoyopod_cli.main build rust-ui-poc" in shell
    assert "venv/bin/python -m yoyopod_cli.main pi rust-ui-poc" in shell
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
uv run pytest -q tests/cli/test_yoyopod_cli_remote_validate.py::test_build_validate_with_rust_ui_poc
```

Expected: FAIL because `_build_validate` does not accept `with_rust_ui_poc`.

- [ ] **Step 3: Extend remote validation builder**

Modify `yoyopod_cli/remote_validate.py` so `_build_validate` accepts and uses the new flag:

```python
def _build_validate(
    *,
    branch: str,
    venv_relpath: str = ".venv",
    sha: str = "",
    with_music: bool,
    with_voip: bool,
    with_power: bool = False,
    with_rtc: bool = False,
    with_cloud_voice: bool = False,
    with_lvgl_soak: bool,
    with_navigation: bool,
    with_rust_ui_poc: bool = False,
) -> str:
```

Then add after the optional navigation stage:

```python
    if with_rust_ui_poc:
        steps.append(checkout_module_command(venv_relpath, "build", "rust-ui-poc"))
        steps.append(checkout_module_command(venv_relpath, "pi", "rust-ui-poc"))
```

Update existing `_build_validate(...)` calls in tests by adding:

```python
        with_rust_ui_poc=False,
```

- [ ] **Step 4: Add CLI options**

In `yoyopod_cli/remote_validate.py`, add the option to `validate(...)`:

```python
    with_rust_ui_poc: bool = typer.Option(
        False,
        "--with-rust-ui-poc",
        help="Build and run the Whisplay-only Rust UI hardware I/O PoC on the target.",
    ),
```

Pass it into `_build_validate(...)`:

```python
        with_rust_ui_poc=with_rust_ui_poc,
```

In `yoyopod_cli/main.py`, add the same top-level shortcut option next to the other `with_*` flags and pass it through to `_remote_validate.validate(...)`.

- [ ] **Step 5: Run remote validate tests**

Run:

```bash
uv run pytest -q tests/cli/test_yoyopod_cli_remote_validate.py
```

Expected: PASS.

- [ ] **Step 6: Commit remote validation flag**

Run:

```bash
git add yoyopod_cli/remote_validate.py yoyopod_cli/main.py tests/cli/test_yoyopod_cli_remote_validate.py
git commit -m "feat(cli): add rust ui poc remote validation"
```

---

### Task 10: Add Host Contract Test For Rust Worker

**Files:**
- Create: `tests/core/test_rust_ui_worker_contract.py`

- [ ] **Step 1: Write contract test**

Create `tests/core/test_rust_ui_worker_contract.py`:

```python
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


def test_rust_ui_worker_mock_contract() -> None:
    if shutil.which("cargo") is None:
        pytest.skip("cargo toolchain not available")

    worker_dir = Path("workers/ui/rust")
    command = {
        "schema_version": 1,
        "kind": "command",
        "type": "ui.show_test_scene",
        "request_id": "frame-contract",
        "timestamp_ms": 1,
        "deadline_ms": 1000,
        "payload": {"counter": 1},
    }
    shutdown = {
        "schema_version": 1,
        "kind": "command",
        "type": "ui.shutdown",
        "request_id": "shutdown",
        "timestamp_ms": 2,
        "deadline_ms": 1000,
        "payload": {},
    }

    result = subprocess.run(
        ["cargo", "run", "--quiet", "--", "--hardware", "mock"],
        input=json.dumps(command) + "\n" + json.dumps(shutdown) + "\n",
        cwd=worker_dir,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    envelopes = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert envelopes[0]["type"] == "ui.ready"
```

- [ ] **Step 2: Run contract test**

Run:

```bash
uv run pytest -q tests/core/test_rust_ui_worker_contract.py
```

Expected: PASS when Cargo is installed, SKIP when Cargo is unavailable.

- [ ] **Step 3: Commit contract test**

Run:

```bash
git add tests/core/test_rust_ui_worker_contract.py
git commit -m "test(ui): add rust ui worker contract"
```

---

### Task 11: Add CI Rust Worker Job

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add change detection for Rust UI worker**

In `.github/workflows/ci.yml`, update the `grep -Eq` pattern in the `changes` job to include `workers/ui/rust/`.

- [ ] **Step 2: Add Rust job**

Add this job next to `voice-go`:

```yaml
  ui-rust:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Run Rust UI worker tests
        working-directory: workers/ui/rust
        run: cargo test
```

- [ ] **Step 3: Gate slot job on Rust tests**

Modify the `slot-arm64` job:

```yaml
    needs: [changes, quality, test, voice-go, ui-rust]
```

- [ ] **Step 4: Run YAML-adjacent validation**

Run:

```bash
uv run pytest -q tests/core/test_rust_ui_worker_contract.py
```

Expected: PASS or SKIP depending on Cargo availability.

- [ ] **Step 5: Commit CI change**

Run:

```bash
git add .github/workflows/ci.yml
git commit -m "ci: test rust ui poc worker"
```

---

### Task 12: Update Command Docs And Hardware Notes

**Files:**
- Modify: `yoyopod_cli/COMMANDS.md`
- Create: `docs/RUST_UI_POC.md`

- [ ] **Step 1: Create PoC docs**

Create `docs/RUST_UI_POC.md`:

```markdown
# Rust UI PoC

The Rust UI PoC is an opt-in Whisplay-only hardware I/O test. It does not
replace the production Python LVGL UI.

## Build

```bash
yoyopod build rust-ui-poc
```

For host-only protocol tests:

```bash
yoyopod build rust-ui-poc --no-hardware-feature
```

## Required Whisplay Environment

The first hardware backend reads explicit GPIO/SPI settings:

- `YOYOPOD_WHISPLAY_SPI_BUS`
- `YOYOPOD_WHISPLAY_SPI_CS`
- `YOYOPOD_WHISPLAY_SPI_HZ`
- `YOYOPOD_WHISPLAY_DC_GPIO`
- `YOYOPOD_WHISPLAY_RESET_GPIO`
- `YOYOPOD_WHISPLAY_BACKLIGHT_GPIO`
- `YOYOPOD_WHISPLAY_BUTTON_GPIO`
- `YOYOPOD_WHISPLAY_BUTTON_ACTIVE_LOW`

The button default is GPIO 26, active low, matching the current Python fallback.

## Run On Pi

```bash
yoyopod pi rust-ui-poc --worker workers/ui/rust/build/yoyopod-rust-ui-poc --frames 10
```

Expected result:

- the Whisplay display shows changing test frames
- the command prints a `ui.ready` payload
- the command prints a `ui.health` payload
```

- [ ] **Step 2: Regenerate CLI docs**

Run:

```bash
uv run yoyopod dev docs
```

Expected: `yoyopod_cli/COMMANDS.md` includes `yoyopod build rust-ui-poc` and `yoyopod pi rust-ui-poc`.
It also includes the `yoyopod remote validate --with-rust-ui-poc` option in the generated help surface.

- [ ] **Step 3: Commit docs**

Run:

```bash
git add docs/RUST_UI_POC.md yoyopod_cli/COMMANDS.md
git commit -m "docs: document rust ui poc workflow"
```

---

### Task 13: Run Final Verification

**Files:**
- No file changes unless verification reveals a real issue.

- [ ] **Step 1: Run Rust tests**

Run:

```bash
cd workers/ui/rust
cargo test
```

Expected: PASS.

- [ ] **Step 2: Run Python quality gate**

Run:

```bash
uv run python scripts/quality.py gate
```

Expected: PASS.

- [ ] **Step 3: Run full Python test suite**

Run:

```bash
uv run pytest -q
```

Expected: PASS, except known Windows-only skips/failures already documented in `AGENTS.md`.

- [ ] **Step 4: Run Pi hardware validation**

On the Whisplay dev lane, run:

```bash
yoyopod remote mode activate dev
yoyopod remote validate --branch <branch> --sha <commit> --with-rust-ui-poc
```

Expected:

- Rust worker builds on the Pi.
- `ui.ready` is printed.
- the Whisplay panel shows changing test output.
- `ui.health` reports `frames=20`.
- process exits cleanly.

- [ ] **Step 5: Run final commit if verification changed files**

If fixes were needed during verification:

```bash
git add <changed-files>
git commit -m "fix(ui): stabilize rust ui poc"
```

Then rerun:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
```

---

## Self-Review

- Spec coverage:
  - Rust output ownership: Tasks 3, 4, and 5.
  - Rust one-button input: Task 2 and Task 5.
  - Python supervision: Task 6 and Task 8.
  - No real screen migration: renderer is a test scene only.
  - Whisplay-only hardware: Task 5 and Task 8 default to `--hardware whisplay`.
  - Remote Pi validation: Task 9.
  - Host and Pi validation: Tasks 10, 11, and 13.
- Red-flag scan:
  - The plan avoids vague terms and gives concrete files, commands, and expected results.
- Type consistency:
  - Rust uses `Envelope`, `EnvelopeKind`, `DisplayDevice`, `ButtonDevice`, `Framebuffer`, and `OneButtonMachine` consistently.
  - Python uses `UiEnvelope` and `RustUiSidecarSupervisor` consistently.

Implementation should proceed in task order. Do not start Task 5 hardware work before Tasks 1-4 are green in mock mode; that keeps hardware debugging isolated from protocol and renderer defects.
