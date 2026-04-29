# Rust VoIP Session Ownership Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the Rust VoIP host domain state into focused modules while keeping Python-facing behavior and worker protocol unchanged.

**Architecture:** `VoipHost` remains the public facade used by `worker.rs`, but it delegates call/mute state, lifecycle state, message correlation, voice-note state, and snapshot rendering to small Rust modules under `yoyopod_rs/voip-host/src/`. Integration tests cover the new module APIs and existing host/worker tests prove protocol compatibility.

**Tech Stack:** Rust 2021, Cargo integration tests, Bazel Rust targets, Python adapter compatibility tests.

---

## Files

- Create `yoyopod_rs/voip-host/src/calls.rs` for call id, peer, call state, and mute ownership.
- Create `yoyopod_rs/voip-host/src/lifecycle.rs` for lifecycle state, recovery tracking, and lifecycle event draining.
- Create `yoyopod_rs/voip-host/src/messages.rs` for `MessageRecord`, last-message snapshots, outbound message id translation, and terminal delivery checks.
- Create `yoyopod_rs/voip-host/src/voice_notes.rs` for voice-note recording/sending state.
- Create `yoyopod_rs/voip-host/src/runtime_snapshot.rs` for canonical `voip.snapshot` payload assembly.
- Modify `yoyopod_rs/voip-host/src/lib.rs` to expose the new modules.
- Modify `yoyopod_rs/voip-host/src/host.rs` so `VoipHost` delegates to those modules without changing its public methods.
- Add integration tests under `yoyopod_rs/voip-host/tests/` for the new module APIs.

## Tasks

- [ ] Add failing integration tests for call session state transitions and mute reset behavior.
- [ ] Add failing integration tests for outbound message id translation and terminal cleanup.
- [ ] Add failing integration tests for voice-note state transitions and snapshot payload fields.
- [ ] Add failing integration tests for lifecycle recovery events and runtime snapshot composition.
- [ ] Implement the new Rust domain modules with small, readable APIs.
- [ ] Refactor `VoipHost` to use the new modules while preserving `VoipHost` method signatures.
- [ ] Run focused Rust tests for `yoyopod-voip-host`.
- [ ] Run full Rust, Bazel, quality, and pytest gates.
- [ ] Commit and push the stacked branch.

## Acceptance Criteria

- `host.rs` no longer directly owns low-level call, lifecycle, message, voice-note, or snapshot JSON internals.
- Existing worker messages and snapshot schema remain compatible.
- Rust module tests describe the domain behavior without relying on Python.
- Python tests remain green, proving the app facade still sees the same behavior.
- Code remains human-readable: small modules, explicit names, simple control flow, and `rustfmt` clean.
