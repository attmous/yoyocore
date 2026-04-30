# Rust-Native LVGL Bridge - Design Spec

## Problem

YoYoPod's Rust UI host already owns the process boundary and generic runtime
snapshot intake, but it still depends on the YoYoPod LVGL C shim for rendering.
The current host loads `yoyopod_lvgl_*` symbols dynamically from the shim and
uses a scene-oriented C ABI that mirrors the legacy Python LVGL integration.

That leaves the Rust UI host with the wrong native boundary:

- Rust does not own the LVGL lifecycle directly.
- Rust screen rendering is still shaped around C-style
  `build/sync/destroy` functions.
- The host still depends on a YoYoPod-owned C facade instead of treating LVGL
  itself as the only native dependency.

The migration target for this slice is not to remove LVGL. The target is to
remove the YoYoPod-specific C shim from the Rust UI host path while preserving
upstream LVGL as the rendering library.

## Goal

Move the Rust UI host to a Rust-native typed LVGL bridge with these properties:

- Python sends one generic runtime snapshot and does not send screen-specific
  render payloads.
- Rust owns screen routing, preemption, focus, and typed screen view-model
  derivation.
- Rust owns the LVGL lifecycle directly: init, display registration, timer
  pumping, object creation, object mutation, and shutdown.
- The YoYoPod LVGL C shim is no longer used by the Rust UI host.
- Upstream LVGL remains an allowed C dependency underneath the Rust host.

This is a Rust ownership migration, not a visual redesign and not a UI toolkit
replacement.

## Non-Goals

- Do not replace LVGL with another toolkit.
- Do not rewrite the UI around a framebuffer-only renderer.
- Do not move Python to screen-specific payloads.
- Do not keep the old `build/sync/destroy` scene ABI as the Rust host's new
  internal API.
- Do not move music, VoIP, power, network, or other runtime services into Rust
  in this slice.
- Do not require building Rust on the Pi Zero 2W.
- Do not require deleting the Python LVGL shim in the same PR if the Python UI
  path still needs it.

## Current State

Today the Rust UI host under `yoyopod_rs/ui-host/` uses
`src/lvgl_bridge.rs` to load the YoYoPod LVGL shim dynamically and call a
scene-level C ABI:

- `yoyopod_lvgl_init`
- `yoyopod_lvgl_register_display`
- `yoyopod_lvgl_hub_build`
- `yoyopod_lvgl_hub_sync`
- `yoyopod_lvgl_hub_destroy`
- equivalent functions for `listen`, `playlist`, `now_playing`, `talk`,
  call screens, `ask`, and `power`

That contract is inherited from the Python LVGL path under
`yoyopod/ui/lvgl_binding/`. It is useful as a legacy reference but is the wrong
shape for the Rust-owned UI host.

## Target Boundary

The approved ownership split is:

### Python owns

- process supervision
- generic runtime snapshot assembly
- app services and domain actions
- handling `ui.intent`, `ui.input`, `ui.screen_changed`, `ui.health`, and
  `ui.error` events from the Rust host

### Rust owns

- route selection from generic runtime facts
- screen preemption and focus
- typed screen view-model derivation
- persistent LVGL screen controllers
- LVGL lifecycle and display registration
- LVGL object mutation and refresh timing
- hardware flush callbacks and input ownership already assigned to the Rust UI
  host path

Python sends facts. Rust decides the screen and render tree.

## Architecture

```text
Python runtime
  |- RustUiFacade
  |    `- sends ui.runtime_snapshot / ui.tick / ui.set_backlight
  `- handles ui.intent / ui.input / ui.screen_changed / ui.health / ui.error

Rust UI host
  |- protocol/
  |- runtime/
  |    |- route selection
  |    |- preemption
  |    `- focus and state machine
  |- screens/
  |    `- typed view-model derivation
  |- lvgl/
  |    |- sys.rs          (raw upstream LVGL FFI)
  |    |- runtime.rs      (init, timers, shutdown)
  |    |- display.rs      (display + flush registration)
  |    `- screens/        (persistent LVGL screen controllers)
  |- render/
  |    `- lvgl_renderer.rs
  `- hardware/
```

The only Rust code that touches LVGL C APIs or raw pointers lives under the new
`lvgl/` boundary. Runtime and screen logic must consume typed Rust models only.

## Renderer Shape

The Rust host should stop modeling rendering as external scene ABI calls and
move to persistent typed controllers.

Recommended structure:

- `lvgl/sys.rs`
  Declares the raw upstream LVGL FFI that the host needs.
- `lvgl/runtime.rs`
  Owns `lv_init`, timer pumping, and orderly shutdown.
- `lvgl/display.rs`
  Registers the display driver and flush callback into the Rust framebuffer or
  hardware target.
- `lvgl/screens/`
  Holds per-screen controllers such as `HubScreenController`,
  `ListenScreenController`, and `InCallScreenController`.
- `render/lvgl_renderer.rs`
  Accepts typed Rust view models and applies them to the active controller.

Per screen, the lifecycle is:

1. Build once when the screen becomes active.
2. Mutate existing LVGL objects in place when the view model changes.
3. Destroy on screen switch only when the controller should not be retained.

The Rust host must not expose or preserve a public
`hub_build/hub_sync/hub_destroy` style API.

## View-Model Direction

Rust derives typed screen models internally from the generic runtime snapshot.
Python remains intentionally generic.

Examples of the target shape:

- `HubViewModel`
- `ListenViewModel`
- `PlaylistViewModel`
- `NowPlayingViewModel`
- `TalkViewModel`
- `IncomingCallViewModel`
- `OutgoingCallViewModel`
- `InCallViewModel`
- `AskViewModel`
- `PowerViewModel`

These models are derived after routing and preemption logic, not sent directly
from Python.

This keeps ownership where it belongs:

- Python owns runtime facts.
- Rust owns UI interpretation.

## One-PR Migration Plan

This work should ship as one PR, but the branch should still be developed in a
safe sequence.

### Phase 1: Introduce the Rust-Native LVGL Boundary

- Add a new Rust `lvgl/` module that talks to upstream LVGL directly.
- Support init, shutdown, display registration, timer pumping, and flush
  callbacks.
- Keep the current `lvgl_bridge.rs` only as a temporary reference while the new
  path is built.

### Phase 2: Port Typed Screen Controllers

- Create typed view models and persistent LVGL screen controllers.
- Start with `Hub`, then port shared primitives, then port the remaining screen
  families.
- Screen families should be ported in this order:
  - navigation/music: `listen`, `playlist`, `now_playing`, `ask`
  - talk/call: `talk`, `incoming_call`, `outgoing_call`, `in_call`
  - system/power overlays

### Phase 3: Flip the Rust Host

- Make the Rust UI host use only the new typed LVGL renderer.
- Keep Python sending generic snapshots over the existing protocol.
- Keep route selection and screen ownership entirely inside Rust.

### Phase 4: Remove Shim Usage From the Rust Host

- Remove dynamic loading of `yoyopod_lvgl_*` symbols from the Rust host.
- Remove the Rust host dependency on the YoYoPod LVGL shim library.
- Keep the Python shim path only if the Python UI runtime still needs it.

This sequence still lands as one PR. The distinction is for implementation
discipline, not for splitting review units.

## Shared UI Primitives

Before porting all screens, the Rust LVGL layer should extract the common
building blocks that currently repeat across scene functions:

- status bar
- footer and action hint region
- accent and palette mapping
- battery, charging, and VoIP state indicators
- common list-row primitives

These should be reusable Rust-owned LVGL components, not recreated ad hoc in
every screen controller.

## Error Handling

Startup and runtime failures must remain explicit:

- missing LVGL library
- failed LVGL init
- failed display driver registration
- failed input registration if owned by the Rust LVGL boundary
- invalid object lifecycle transitions
- renderer/screen update failures that make UI ownership unsafe

The host must fail loudly rather than silently falling back to the old shim path
once the new renderer is selected.

## Testing

The migration must add or preserve tests for:

- generic runtime snapshot to route selection
- generic runtime snapshot to typed view-model derivation
- active-screen switching and controller lifecycle
- controller mutation behavior without full rebuilds on every update
- LVGL runtime lifecycle and init failure behavior
- protocol compatibility with Python's generic snapshot sender

Existing Rust host protocol, runtime, and worker tests should remain green.

## CI And Verification

The repo's pre-commit rule still applies. Before committing or pushing the PR,
run:

```text
uv run python scripts/quality.py gate
uv run pytest -q
```

Rust artifacts for Pi validation must still come from the existing CI artifact
flow. Do not build the production Rust host on the Pi Zero 2W unless the user
explicitly overrides that rule.

Hardware validation after artifact deploy should confirm:

- the Rust host no longer depends on YoYoPod shim symbols
- LVGL initializes once and stays persistent
- screen switches update the right controller
- Whisplay output remains correct
- input still drives the expected UI transitions
- call preemption and return-to-idle behavior still work

## Acceptance Criteria

This design is accepted when the final PR leaves the repo in a state where:

- the Rust UI host no longer loads or calls any `yoyopod_lvgl_*` shim symbols
- Python still sends one generic runtime snapshot
- Rust derives typed screen view models internally
- Rust owns route selection and screen rendering decisions
- the LVGL lifecycle is persistent in Rust
- `unsafe` stays isolated to the narrow Rust LVGL boundary
- the Rust UI host no longer depends on the YoYoPod LVGL shim for its render
  path
- the Python LVGL shim remains only if another runtime path still needs it

## Follow-Up Work

This migration intentionally leaves two later choices outside the current PR:

- whether to retire the Python LVGL shim entirely after the Python UI path is no
  longer needed
- whether the long-term renderer remains LVGL or changes only after the Rust UI
  host is stable and measured on hardware
