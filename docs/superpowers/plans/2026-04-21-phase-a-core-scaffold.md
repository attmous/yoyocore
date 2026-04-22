# Phase A — CLI Cleanup + Core Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the first slice of Phase A on the long-lived `arch/phase-a-spine-rewrite` branch: validate the already-merged CLI polish baseline, then build and test the `core/` primitives (`Bus`, `States`, `Services`, `MainThreadScheduler`, core events, log ring buffer, `YoyoPodApp` shell, and test helpers).

**Architecture:** Single long-lived branch off `main`. Two-phase structure: (1) CLI baseline verification / corrective cleanup; (2) TDD-driven construction of the `core/` package. Each primitive is its own module with its own unit-test file. The app shell composes the primitives but does no domain-specific work — that comes in later plans per integration.

**Tech Stack:** Python 3.12+, pytest, uv, Typer (existing), loguru (existing), `dataclasses.dataclass(frozen=True, slots=True)`, stdlib `threading`/`queue`/`collections`. No new runtime dependencies.

**Spec reference:** `docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md` §4 (Core primitives), §11.2 (steps 1-2).

## Current-main corrections

- CLI polish already merged on `main` in `5e2640f`; Task 2 is validation/corrective cleanup only.
- The live CLI package is `yoyopod_cli/`; there is no `src/yoyopod/cli/` on current `main`.
- `pyproject.toml` already points `yoyopod` at `yoyopod_cli.main:run`.
- `tests/test_no_yoyoctl_references.py` is the regression guard against re-introducing the old binary name.
- `src/yoyopod/core/` already exists as a compatibility package; add the new spine primitives there incrementally while the legacy app still runs.

---

## File Structure

### Files to create

- `src/yoyopod/core/__init__.py` — public surface of the core package
- `src/yoyopod/core/bus.py` — typed event bus
- `src/yoyopod/core/states.py` — entity state store
- `src/yoyopod/core/services.py` — command registry
- `src/yoyopod/core/scheduler.py` — main-thread scheduler
- `src/yoyopod/core/events.py` — `StateChangedEvent`, `LifecycleEvent`
- `src/yoyopod/core/logbuffer.py` — ring buffer for recent log entries
- `src/yoyopod/core/app_shell.py` — `YoyoPodApp`
- `src/yoyopod/core/testing.py` — `build_test_app`, `assert_events_contain`, `drain_all`
- `tests/core/__init__.py`
- `tests/core/test_bus.py`
- `tests/core/test_states.py`
- `tests/core/test_services.py`
- `tests/core/test_scheduler.py`
- `tests/core/test_events.py`
- `tests/core/test_logbuffer.py`
- `tests/core/test_app_shell.py`
- `tests/core/test_testing_helpers.py`

### Files to modify

- `pyproject.toml` — validation only; no script change expected on current `main`.
- `yoyopod_cli/main.py` plus related CLI docs/tests only if verification finds drift.
- `tests/test_no_yoyoctl_references.py` — update the allowlist only if a newly-added historical doc must retain `yoyoctl`.
- `src/yoyopod/core/__init__.py` and existing compatibility modules — export the new primitives while the legacy app keeps running.

### Files to delete

None in this plan.

---

## Task 1: Create the long-lived Phase A branch

**Files:** none (git state only)

- [ ] **Step 1.1: Verify clean working tree and current branch**

Run:
```bash
git status
git branch --show-current
```

Expected: `git status` shows clean (or only explicitly preserved local scratch files); current branch is either `main` or a clean feature branch created from current `origin/main`.

- [ ] **Step 1.2: Create and check out the long-lived Phase A branch**

Run:
```bash
git checkout -b arch/phase-a-spine-rewrite
```

Expected: `Switched to a new branch 'arch/phase-a-spine-rewrite'`.

- [ ] **Step 1.3: Confirm branch is off main**

Run:
```bash
git log --oneline -5
```

Expected: top commit is whatever `main` currently points at when execution starts; the important constraint is that `arch/phase-a-spine-rewrite` branches from up-to-date `origin/main`.

---

## Task 2: Validate the merged CLI baseline and clean only real stragglers

**Files:** `pyproject.toml`, `yoyopod_cli/`, `tests/test_no_yoyoctl_references.py`, and live docs/skills/rules only if verification finds drift.

- [ ] **Step 2.1: Enumerate current `yoyoctl` references**

Run:
```bash
git grep -l "yoyoctl"
```

Expected: historical planning/docs files plus `tests/test_no_yoyoctl_references.py`. Any live runtime file is a bug to fix, not proof that the broad rename still needs to be replayed.

- [ ] **Step 2.2: Confirm the merged CLI baseline**

Verify these current-main facts before editing anything:

```bash
grep -n "yoyopod =" pyproject.toml
grep -n 'name="yoyopod"' yoyopod_cli/main.py
```

Expected:
- `pyproject.toml` contains only `yoyopod = "yoyopod_cli.main:run"` under `[project.scripts]`
- the live Typer root app is already named `yoyopod`

- [ ] **Step 2.3: Fix only actual post-merge stragglers**

If `git grep -l "yoyoctl"` returns live files outside historical docs / planning files / `tests/test_no_yoyoctl_references.py`, update those files manually. Do **not** re-run the broad rename sweep from the draft plan; that work already landed via #298.

- [ ] **Step 2.4: Run the CLI regression tests**

Run:
```bash
uv run pytest tests/test_cli.py tests/test_pi_remote.py tests/test_setup_cli.py tests/test_no_yoyoctl_references.py -v
```

Expected: all passing.

- [ ] **Step 2.5: Run the full CI gate**

Run:
```bash
uv run python scripts/quality.py ci
```

Expected: all green. This step honours the user's pre-commit memory (`feedback_verify_ci_locally.md`).

- [ ] **Step 2.6: Commit only if verification required changes**

If Task 2 found real drift, commit that narrow cleanup. If verification was already clean, skip the commit and continue directly to Task 3.

- [ ] **Step 2.7: Confirm clean working tree**

Run:
```bash
git status
```

Expected: `nothing to commit, working tree clean` (ignoring explicitly preserved local scratch files).

---

## Task 3: Create core/ and tests/core/ scaffold

**Files:**
- Create: `src/yoyopod/core/__init__.py`
- Create: `tests/core/__init__.py`

- [ ] **Step 3.1: Create `src/yoyopod/core/` with an empty package marker**

Run:
```bash
mkdir -p src/yoyopod/core tests/core
```

- [ ] **Step 3.2: Populate `src/yoyopod/core/__init__.py`**

Create `src/yoyopod/core/__init__.py` with:

```python
"""Core primitives for YoyoPod's state-store + typed-bus + service-registry architecture.

See docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §4.
"""

from __future__ import annotations

# Explicit re-exports are added as primitives land.
```

- [ ] **Step 3.3: Populate `tests/core/__init__.py`**

Create `tests/core/__init__.py` with a single blank line (pytest package marker):

```python

```

- [ ] **Step 3.4: Commit the scaffold**

Run:
```bash
git add src/yoyopod/core/__init__.py tests/core/__init__.py
git commit -m "$(cat <<'EOF'
chore(core): scaffold core package and tests directory

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Build `Bus` with TDD

**Files:**
- Create: `tests/core/test_bus.py`
- Create: `src/yoyopod/core/bus.py`

- [ ] **Step 4.1: Write the failing test file `tests/core/test_bus.py`**

Create `tests/core/test_bus.py` with:

```python
"""Tests for yoyopod.core.bus.Bus."""

from __future__ import annotations

import threading
from dataclasses import dataclass

import pytest

from yoyopod.core.bus import Bus


@dataclass(frozen=True, slots=True)
class ExampleEvent:
    payload: str


@dataclass(frozen=True, slots=True)
class ChildEvent(ExampleEvent):
    pass


@dataclass(frozen=True, slots=True)
class UnrelatedEvent:
    count: int


def _make_bus(strict: bool = True) -> Bus:
    return Bus(main_thread_id=threading.get_ident(), strict=strict)


def test_subscribe_then_publish_invokes_handler_on_drain() -> None:
    bus = _make_bus()
    captured: list[str] = []
    bus.subscribe(ExampleEvent, lambda ev: captured.append(ev.payload))

    bus.publish(ExampleEvent(payload="hello"))
    processed = bus.drain()

    assert processed == 1
    assert captured == ["hello"]


def test_publish_before_drain_is_queued_not_dispatched() -> None:
    bus = _make_bus()
    captured: list[str] = []
    bus.subscribe(ExampleEvent, lambda ev: captured.append(ev.payload))

    bus.publish(ExampleEvent(payload="first"))
    bus.publish(ExampleEvent(payload="second"))

    assert captured == []
    assert bus.pending_count() == 2

    bus.drain()
    assert captured == ["first", "second"]
    assert bus.pending_count() == 0


def test_multiple_subscribers_all_invoked() -> None:
    bus = _make_bus()
    captured_a: list[str] = []
    captured_b: list[str] = []
    bus.subscribe(ExampleEvent, lambda ev: captured_a.append(ev.payload))
    bus.subscribe(ExampleEvent, lambda ev: captured_b.append(ev.payload))

    bus.publish(ExampleEvent(payload="x"))
    bus.drain()

    assert captured_a == ["x"]
    assert captured_b == ["x"]


def test_subclass_events_reach_parent_subscribers() -> None:
    bus = _make_bus()
    parent_captured: list[str] = []
    bus.subscribe(ExampleEvent, lambda ev: parent_captured.append(ev.payload))

    bus.publish(ChildEvent(payload="child"))
    bus.drain()

    assert parent_captured == ["child"]


def test_unrelated_events_do_not_reach_subscribers() -> None:
    bus = _make_bus()
    captured: list[str] = []
    bus.subscribe(ExampleEvent, lambda ev: captured.append(ev.payload))

    bus.publish(UnrelatedEvent(count=1))
    bus.drain()

    assert captured == []


def test_drain_limit_respected() -> None:
    bus = _make_bus()
    captured: list[str] = []
    bus.subscribe(ExampleEvent, lambda ev: captured.append(ev.payload))

    for i in range(5):
        bus.publish(ExampleEvent(payload=str(i)))

    first = bus.drain(limit=2)
    second = bus.drain()

    assert first == 2
    assert second == 3
    assert captured == ["0", "1", "2", "3", "4"]


def test_strict_mode_rejects_off_main_publish() -> None:
    bus = _make_bus(strict=True)
    error_captured: list[BaseException] = []

    def publish_from_thread() -> None:
        try:
            bus.publish(ExampleEvent(payload="bad"))
        except RuntimeError as exc:
            error_captured.append(exc)

    t = threading.Thread(target=publish_from_thread)
    t.start()
    t.join()

    assert len(error_captured) == 1
    assert "non-main thread" in str(error_captured[0])
    assert bus.pending_count() == 0


def test_permissive_mode_queues_off_main_publish() -> None:
    bus = _make_bus(strict=False)

    def publish_from_thread() -> None:
        bus.publish(ExampleEvent(payload="from-bg"))

    t = threading.Thread(target=publish_from_thread)
    t.start()
    t.join()

    assert bus.pending_count() == 1


def test_handler_exception_in_strict_mode_raises() -> None:
    bus = _make_bus(strict=True)

    def bad(_ev: ExampleEvent) -> None:
        raise ValueError("handler bug")

    bus.subscribe(ExampleEvent, bad)
    bus.publish(ExampleEvent(payload="x"))

    with pytest.raises(ValueError, match="handler bug"):
        bus.drain()


def test_handler_exception_in_permissive_mode_continues_to_next_handler() -> None:
    bus = _make_bus(strict=False)
    captured: list[str] = []

    def bad(_ev: ExampleEvent) -> None:
        raise ValueError("handler bug")

    bus.subscribe(ExampleEvent, bad)
    bus.subscribe(ExampleEvent, lambda ev: captured.append(ev.payload))

    bus.publish(ExampleEvent(payload="continues"))
    bus.drain()

    assert captured == ["continues"]
```

- [ ] **Step 4.2: Run the tests to confirm they fail (no `bus.py` yet)**

Run:
```bash
uv run pytest tests/core/test_bus.py -v
```

Expected: 10 ERRORS or FAILURES with `ModuleNotFoundError: No module named 'yoyopod.core.bus'`.

- [ ] **Step 4.3: Implement `src/yoyopod/core/bus.py`**

Create `src/yoyopod/core/bus.py` with:

```python
"""Typed event bus for YoyoPod core primitives.

Design: main-thread-only. Publishing from a non-main thread raises in
strict mode or logs a warning (and still queues) in permissive mode.
Backend threads route through the MainThreadScheduler instead of calling
publish() directly. See docs/superpowers/specs/2026-04-21-phase-a-spine-
rewrite-design.md §4.1.
"""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from typing import Any, Callable, DefaultDict, Deque

from loguru import logger


EventHandler = Callable[[Any], None]


class Bus:
    """Typed, main-thread-only event bus."""

    def __init__(self, main_thread_id: int, strict: bool = True) -> None:
        self._main_thread_id = main_thread_id
        self._strict = strict
        self._subscribers: DefaultDict[type, list[EventHandler]] = defaultdict(list)
        self._queue: Deque[Any] = deque()

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Register a handler for events of the given type (or subclasses)."""
        self._subscribers[event_type].append(handler)
        logger.trace("Bus subscribed to {}", event_type.__name__)

    def publish(self, event: Any) -> None:
        """Publish an event. Raises in strict mode if called off-main thread."""
        if threading.get_ident() != self._main_thread_id:
            if self._strict:
                raise RuntimeError(
                    "Bus.publish called from non-main thread "
                    f"(event: {event.__class__.__name__}). Route through scheduler.run_on_main."
                )
            logger.warning(
                "Bus.publish called from non-main thread: {}",
                event.__class__.__name__,
            )
        self._queue.append(event)

    def drain(self, limit: int | None = None) -> int:
        """Dispatch queued events to subscribers in FIFO order."""
        processed = 0
        while self._queue and (limit is None or processed < limit):
            event = self._queue.popleft()
            self._dispatch(event)
            processed += 1
        return processed

    def pending_count(self) -> int:
        """Return the number of events awaiting dispatch."""
        return len(self._queue)

    def _dispatch(self, event: Any) -> None:
        handlers: list[EventHandler] = []
        for event_type, subs in self._subscribers.items():
            if isinstance(event, event_type):
                handlers.extend(subs)

        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                if self._strict:
                    raise
                logger.error(
                    "Bus handler {!r} raised {}: {}",
                    handler,
                    exc.__class__.__name__,
                    exc,
                )
```

- [ ] **Step 4.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/core/test_bus.py -v
```

Expected: 10 passed.

- [ ] **Step 4.5: Format, lint, and type-check the new files**

Run:
```bash
uv run black src/yoyopod/core/bus.py tests/core/test_bus.py
uv run ruff check src/yoyopod/core/bus.py tests/core/test_bus.py
uv run mypy src/yoyopod/core/bus.py
```

Expected: black reports "reformatted" or "unchanged"; ruff reports no issues; mypy passes with no errors.

- [ ] **Step 4.6: Add `Bus` to `core/__init__.py` re-exports**

Edit `src/yoyopod/core/__init__.py` — append:

```python
from yoyopod.core.bus import Bus

__all__ = ["Bus"]
```

- [ ] **Step 4.7: Commit**

Run:
```bash
git add src/yoyopod/core/__init__.py src/yoyopod/core/bus.py tests/core/test_bus.py
git commit -m "$(cat <<'EOF'
feat(core): add typed Bus primitive

Main-thread-only by contract (strict mode raises on off-main publish).
Subclass events dispatch to parent subscribers via isinstance matching.
Handler exceptions in permissive mode are logged and dispatch continues;
strict mode re-raises (used in tests).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Build `States` with TDD

**Files:**
- Create: `tests/core/test_states.py`
- Create: `src/yoyopod/core/states.py`

- [ ] **Step 5.1: Write the failing test file `tests/core/test_states.py`**

Create `tests/core/test_states.py`:

```python
"""Tests for yoyopod.core.states.States."""

from __future__ import annotations

import threading

from yoyopod.core.bus import Bus
from yoyopod.core.events import StateChangedEvent
from yoyopod.core.states import States, StateValue


def _make_bus_and_states() -> tuple[Bus, States]:
    bus = Bus(main_thread_id=threading.get_ident(), strict=True)
    states = States(bus=bus)
    return bus, states


def test_get_missing_entity_returns_none() -> None:
    _, states = _make_bus_and_states()
    assert states.get("call.state") is None
    assert states.has("call.state") is False


def test_get_value_missing_returns_default() -> None:
    _, states = _make_bus_and_states()
    assert states.get_value("call.state", default="idle") == "idle"
    assert states.get_value("call.state") is None


def test_set_creates_entity_and_fires_state_changed() -> None:
    bus, states = _make_bus_and_states()
    captured: list[StateChangedEvent] = []
    bus.subscribe(StateChangedEvent, lambda ev: captured.append(ev))

    states.set("call.state", "incoming", attrs={"caller": "sip:bob@x"})
    bus.drain()

    sv = states.get("call.state")
    assert sv is not None
    assert sv.value == "incoming"
    assert sv.attrs == {"caller": "sip:bob@x"}
    assert sv.last_changed_at > 0.0

    assert len(captured) == 1
    assert captured[0].entity == "call.state"
    assert captured[0].old is None
    assert captured[0].new == sv


def test_set_no_op_when_value_and_attrs_unchanged() -> None:
    bus, states = _make_bus_and_states()
    captured: list[StateChangedEvent] = []
    bus.subscribe(StateChangedEvent, lambda ev: captured.append(ev))

    states.set("call.state", "idle", attrs={})
    bus.drain()
    captured.clear()

    states.set("call.state", "idle", attrs={})
    bus.drain()

    assert captured == []


def test_set_fires_event_when_attrs_change_but_value_same() -> None:
    bus, states = _make_bus_and_states()
    captured: list[StateChangedEvent] = []
    bus.subscribe(StateChangedEvent, lambda ev: captured.append(ev))

    states.set("call.state", "active", attrs={"caller": "a"})
    bus.drain()
    captured.clear()

    states.set("call.state", "active", attrs={"caller": "b"})
    bus.drain()

    assert len(captured) == 1
    assert captured[0].entity == "call.state"
    assert captured[0].old is not None
    assert captured[0].old.attrs == {"caller": "a"}
    assert captured[0].new.attrs == {"caller": "b"}


def test_set_without_attrs_defaults_to_empty_dict() -> None:
    _, states = _make_bus_and_states()
    states.set("music.state", "playing")
    sv = states.get("music.state")
    assert sv is not None
    assert sv.attrs == {}


def test_all_returns_snapshot() -> None:
    _, states = _make_bus_and_states()
    states.set("call.state", "idle")
    states.set("music.state", "paused")

    snap = states.all()
    assert set(snap.keys()) == {"call.state", "music.state"}
    assert snap["call.state"].value == "idle"
    assert snap["music.state"].value == "paused"


def test_state_changed_event_contains_old_state_value() -> None:
    bus, states = _make_bus_and_states()
    captured: list[StateChangedEvent] = []
    bus.subscribe(StateChangedEvent, lambda ev: captured.append(ev))

    states.set("power.battery_percent", 80)
    bus.drain()
    captured.clear()

    states.set("power.battery_percent", 75)
    bus.drain()

    assert len(captured) == 1
    ev = captured[0]
    assert ev.old is not None
    assert ev.old.value == 80
    assert ev.new.value == 75
```

- [ ] **Step 5.2: Write the corresponding events stub**

`StateChangedEvent` lives in `core/events.py` which doesn't exist yet — but the tests import it. Create a minimal stub at `src/yoyopod/core/events.py`:

```python
"""Core event types for YoyoPod's typed event bus.

Expands in Task 8. This minimal version covers only what States needs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yoyopod.core.states import StateValue


@dataclass(frozen=True, slots=True)
class StateChangedEvent:
    """Universal state-change notification published by States on every effective set()."""

    entity: str
    old: "StateValue | None"
    new: "StateValue"
```

- [ ] **Step 5.3: Run the test file to verify it fails**

Run:
```bash
uv run pytest tests/core/test_states.py -v
```

Expected: import error on `yoyopod.core.states` (ModuleNotFoundError) or on `States`/`StateValue`.

- [ ] **Step 5.4: Implement `src/yoyopod/core/states.py`**

Create `src/yoyopod/core/states.py`:

```python
"""Entity state store. Source of truth for domain state across integrations.

Writes fire StateChangedEvent on the bus. Reads return StateValue snapshots.
See docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §4.2.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from yoyopod.core.bus import Bus
from yoyopod.core.events import StateChangedEvent


@dataclass(frozen=True, slots=True)
class StateValue:
    """Snapshot of an entity's current state."""

    value: Any
    attrs: dict[str, Any] = field(default_factory=dict)
    last_changed_at: float = 0.0


class States:
    """Entity state store keyed by `domain.entity_name` strings."""

    def __init__(self, bus: Bus) -> None:
        self._bus = bus
        self._store: dict[str, StateValue] = {}

    def set(
        self,
        entity: str,
        value: Any,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        """Set an entity's value. No-op if (value, attrs) unchanged. Fires StateChangedEvent otherwise."""
        new_attrs = dict(attrs) if attrs is not None else {}
        current = self._store.get(entity)
        if current is not None and current.value == value and current.attrs == new_attrs:
            return

        new_sv = StateValue(value=value, attrs=new_attrs, last_changed_at=time.time())
        self._store[entity] = new_sv
        self._bus.publish(StateChangedEvent(entity=entity, old=current, new=new_sv))

    def get(self, entity: str) -> StateValue | None:
        """Return the StateValue for the given entity, or None if absent."""
        return self._store.get(entity)

    def get_value(self, entity: str, default: Any = None) -> Any:
        """Convenience: return the entity's value or default."""
        sv = self._store.get(entity)
        return sv.value if sv is not None else default

    def has(self, entity: str) -> bool:
        """Return True iff the entity has been set at least once."""
        return entity in self._store

    def all(self) -> dict[str, StateValue]:
        """Return a shallow snapshot of the full store (used by diagnostics)."""
        return dict(self._store)
```

- [ ] **Step 5.5: Run tests; all should pass**

Run:
```bash
uv run pytest tests/core/test_states.py -v
```

Expected: all passing.

- [ ] **Step 5.6: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/core/states.py src/yoyopod/core/events.py tests/core/test_states.py
uv run ruff check src/yoyopod/core/states.py src/yoyopod/core/events.py tests/core/test_states.py
uv run mypy src/yoyopod/core/states.py src/yoyopod/core/events.py
```

Expected: all green.

- [ ] **Step 5.7: Re-export from `core/__init__.py`**

Edit `src/yoyopod/core/__init__.py`:

```python
"""Core primitives for YoyoPod's state-store + typed-bus + service-registry architecture.

See docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §4.
"""

from __future__ import annotations

from yoyopod.core.bus import Bus
from yoyopod.core.events import StateChangedEvent
from yoyopod.core.states import States, StateValue

__all__ = ["Bus", "States", "StateValue", "StateChangedEvent"]
```

- [ ] **Step 5.8: Commit**

Run:
```bash
git add src/yoyopod/core/__init__.py src/yoyopod/core/states.py src/yoyopod/core/events.py tests/core/test_states.py
git commit -m "$(cat <<'EOF'
feat(core): add States entity store + StateChangedEvent

Writes fire StateChangedEvent on the bus; no-op when (value, attrs) unchanged.
Attrs-only changes still fire (attrs are carried in StateValue). Reads return
StateValue snapshots; all() returns a shallow snapshot for diagnostics.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Build `Services` with TDD

**Files:**
- Create: `tests/core/test_services.py`
- Create: `src/yoyopod/core/services.py`

- [ ] **Step 6.1: Write `tests/core/test_services.py`**

Create `tests/core/test_services.py`:

```python
"""Tests for yoyopod.core.services.Services."""

from __future__ import annotations

import threading
from dataclasses import dataclass

import pytest

from yoyopod.core.bus import Bus
from yoyopod.core.services import Services, ServiceNotRegisteredError


@dataclass(frozen=True, slots=True)
class PlayCommand:
    track_uri: str


@dataclass(frozen=True, slots=True)
class VolumeCommand:
    percent: int


def _make() -> tuple[Bus, Services]:
    bus = Bus(main_thread_id=threading.get_ident(), strict=True)
    services = Services(bus=bus)
    return bus, services


def test_register_then_call_invokes_handler_with_data() -> None:
    _, services = _make()
    captured: list[str] = []
    services.register("music", "play", lambda cmd: captured.append(cmd.track_uri))

    services.call("music", "play", PlayCommand(track_uri="local:test.mp3"))

    assert captured == ["local:test.mp3"]


def test_call_unregistered_raises_service_not_registered() -> None:
    _, services = _make()
    with pytest.raises(ServiceNotRegisteredError):
        services.call("music", "play", PlayCommand(track_uri="x"))


def test_register_twice_for_same_service_raises() -> None:
    _, services = _make()
    services.register("music", "play", lambda _cmd: None)
    with pytest.raises(ValueError, match="already registered"):
        services.register("music", "play", lambda _cmd: None)


def test_call_returns_handler_result() -> None:
    _, services = _make()
    services.register("contacts", "lookup", lambda _cmd: "Alice")

    result = services.call("contacts", "lookup", None)

    assert result == "Alice"


def test_call_propagates_handler_exception() -> None:
    _, services = _make()

    def bad(_cmd: None) -> None:
        raise RuntimeError("kaboom")

    services.register("music", "crash", bad)

    with pytest.raises(RuntimeError, match="kaboom"):
        services.call("music", "crash", None)


def test_registered_returns_sorted_list() -> None:
    _, services = _make()
    services.register("music", "play", lambda _: None)
    services.register("call", "dial", lambda _: None)
    services.register("music", "pause", lambda _: None)

    registered = services.registered()

    assert registered == [("call", "dial"), ("music", "pause"), ("music", "play")]


def test_data_can_be_none_for_arg_less_commands() -> None:
    _, services = _make()
    called: list[bool] = []
    services.register("call", "answer", lambda _cmd: called.append(True))

    services.call("call", "answer", None)

    assert called == [True]
```

- [ ] **Step 6.2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/core/test_services.py -v
```

Expected: import error on `yoyopod.core.services`.

- [ ] **Step 6.3: Implement `src/yoyopod/core/services.py`**

Create `src/yoyopod/core/services.py`:

```python
"""Typed command registry for YoyoPod core primitives.

Services are registered per (domain, service) pair. Callers invoke them via
`services.call(domain, service, data)` where data is a typed dataclass (or
None for argless commands). Handlers run synchronously on the main thread.
See docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §4.3.
"""

from __future__ import annotations

from typing import Any, Callable

from loguru import logger

from yoyopod.core.bus import Bus


Handler = Callable[[Any], Any]


class ServiceNotRegisteredError(LookupError):
    """Raised when Services.call is invoked for an unregistered (domain, service)."""


class Services:
    """Command registry keyed by (domain, service) tuples."""

    def __init__(self, bus: Bus) -> None:
        self._bus = bus
        self._handlers: dict[tuple[str, str], Handler] = {}

    def register(self, domain: str, service: str, handler: Handler) -> None:
        """Register a handler for (domain, service). Raises if already registered."""
        key = (domain, service)
        if key in self._handlers:
            raise ValueError(f"Service {domain}.{service} already registered")
        self._handlers[key] = handler
        logger.trace("Services registered {}.{}", domain, service)

    def call(self, domain: str, service: str, data: Any = None) -> Any:
        """Invoke a registered service synchronously on the main thread."""
        key = (domain, service)
        handler = self._handlers.get(key)
        if handler is None:
            raise ServiceNotRegisteredError(
                f"Service {domain}.{service} is not registered"
            )
        logger.trace("Services call {}.{} data={!r}", domain, service, data)
        return handler(data)

    def registered(self) -> list[tuple[str, str]]:
        """Return all registered (domain, service) pairs, sorted."""
        return sorted(self._handlers.keys())
```

- [ ] **Step 6.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/core/test_services.py -v
```

Expected: all passing.

- [ ] **Step 6.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/core/services.py tests/core/test_services.py
uv run ruff check src/yoyopod/core/services.py tests/core/test_services.py
uv run mypy src/yoyopod/core/services.py
```

Expected: all green.

- [ ] **Step 6.6: Re-export from `core/__init__.py`**

Append to `src/yoyopod/core/__init__.py`:

```python
from yoyopod.core.services import Services, ServiceNotRegisteredError
```

And extend `__all__`:

```python
__all__ = [
    "Bus",
    "States",
    "StateValue",
    "StateChangedEvent",
    "Services",
    "ServiceNotRegisteredError",
]
```

- [ ] **Step 6.7: Commit**

Run:
```bash
git add src/yoyopod/core/__init__.py src/yoyopod/core/services.py tests/core/test_services.py
git commit -m "$(cat <<'EOF'
feat(core): add Services command registry

Synchronous (domain, service) handler dispatch. Typed data arg (None allowed).
Double-registration raises; call on unregistered raises ServiceNotRegisteredError.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Build `MainThreadScheduler` with TDD

**Files:**
- Create: `tests/core/test_scheduler.py`
- Create: `src/yoyopod/core/scheduler.py`

- [ ] **Step 7.1: Write `tests/core/test_scheduler.py`**

Create `tests/core/test_scheduler.py`:

```python
"""Tests for yoyopod.core.scheduler.MainThreadScheduler."""

from __future__ import annotations

import threading
import time

from yoyopod.core.scheduler import MainThreadScheduler


def _make() -> MainThreadScheduler:
    return MainThreadScheduler(main_thread_id=threading.get_ident())


def test_run_on_main_same_thread_executes_immediately() -> None:
    scheduler = _make()
    captured: list[int] = []

    scheduler.run_on_main(lambda: captured.append(1))

    assert captured == [1]
    assert scheduler.pending_count() == 0


def test_run_on_main_from_background_thread_queues_task() -> None:
    scheduler = _make()
    captured: list[str] = []

    def from_bg() -> None:
        scheduler.run_on_main(lambda: captured.append("from-bg"))

    t = threading.Thread(target=from_bg)
    t.start()
    t.join()

    assert captured == []
    assert scheduler.pending_count() == 1

    processed = scheduler.drain()

    assert processed == 1
    assert captured == ["from-bg"]


def test_drain_runs_tasks_in_fifo_order() -> None:
    scheduler = _make()
    captured: list[int] = []

    def from_bg() -> None:
        for i in range(5):
            scheduler.run_on_main(lambda n=i: captured.append(n))

    t = threading.Thread(target=from_bg)
    t.start()
    t.join()

    scheduler.drain()

    assert captured == [0, 1, 2, 3, 4]


def test_drain_limit_respected() -> None:
    scheduler = _make()
    captured: list[int] = []

    def from_bg() -> None:
        for i in range(5):
            scheduler.run_on_main(lambda n=i: captured.append(n))

    t = threading.Thread(target=from_bg)
    t.start()
    t.join()

    first = scheduler.drain(limit=2)
    rest = scheduler.drain()

    assert first == 2
    assert rest == 3
    assert captured == [0, 1, 2, 3, 4]


def test_task_exception_is_swallowed_and_remaining_tasks_run() -> None:
    scheduler = _make()
    captured: list[str] = []

    def bad() -> None:
        raise RuntimeError("task bug")

    def from_bg() -> None:
        scheduler.run_on_main(bad)
        scheduler.run_on_main(lambda: captured.append("after-bad"))

    t = threading.Thread(target=from_bg)
    t.start()
    t.join()

    scheduler.drain()

    assert captured == ["after-bad"]


def test_pending_count_reports_queued_depth() -> None:
    scheduler = _make()

    def from_bg() -> None:
        for _ in range(3):
            scheduler.run_on_main(lambda: None)

    t = threading.Thread(target=from_bg)
    t.start()
    t.join()

    assert scheduler.pending_count() == 3
    scheduler.drain()
    assert scheduler.pending_count() == 0
```

- [ ] **Step 7.2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/core/test_scheduler.py -v
```

Expected: import error on `yoyopod.core.scheduler`.

- [ ] **Step 7.3: Implement `src/yoyopod/core/scheduler.py`**

Create `src/yoyopod/core/scheduler.py`:

```python
"""Main-thread task scheduler for YoyoPod core primitives.

Backend threads use this to marshal tasks back to the main thread so they
can safely publish events and mutate state. See docs/superpowers/specs/
2026-04-21-phase-a-spine-rewrite-design.md §4.4.
"""

from __future__ import annotations

import threading
from queue import Empty, Queue
from typing import Callable

from loguru import logger


class MainThreadScheduler:
    """Thread-safe FIFO queue of tasks drained on the main thread."""

    def __init__(self, main_thread_id: int) -> None:
        self._main_thread_id = main_thread_id
        self._queue: "Queue[Callable[[], None]]" = Queue()

    def run_on_main(self, fn: Callable[[], None]) -> None:
        """Run fn immediately if called on the main thread, else queue it."""
        if threading.get_ident() == self._main_thread_id:
            fn()
            return
        self._queue.put(fn)

    def drain(self, limit: int | None = None) -> int:
        """Run queued tasks in FIFO order. Returns number executed."""
        processed = 0
        while limit is None or processed < limit:
            try:
                fn = self._queue.get_nowait()
            except Empty:
                break
            try:
                fn()
            except Exception as exc:
                logger.error(
                    "Scheduler task {!r} raised {}: {}",
                    fn,
                    exc.__class__.__name__,
                    exc,
                )
            processed += 1
        return processed

    def pending_count(self) -> int:
        """Return the queued-task count (best-effort)."""
        return self._queue.qsize()
```

- [ ] **Step 7.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/core/test_scheduler.py -v
```

Expected: all passing.

- [ ] **Step 7.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/core/scheduler.py tests/core/test_scheduler.py
uv run ruff check src/yoyopod/core/scheduler.py tests/core/test_scheduler.py
uv run mypy src/yoyopod/core/scheduler.py
```

Expected: all green.

- [ ] **Step 7.6: Re-export from `core/__init__.py`**

Append to `src/yoyopod/core/__init__.py`:

```python
from yoyopod.core.scheduler import MainThreadScheduler
```

Extend `__all__`:

```python
__all__ = [
    "Bus",
    "States",
    "StateValue",
    "StateChangedEvent",
    "Services",
    "ServiceNotRegisteredError",
    "MainThreadScheduler",
]
```

- [ ] **Step 7.7: Commit**

Run:
```bash
git add src/yoyopod/core/__init__.py src/yoyopod/core/scheduler.py tests/core/test_scheduler.py
git commit -m "$(cat <<'EOF'
feat(core): add MainThreadScheduler

Backend threads call run_on_main(fn) to marshal fn onto the main thread.
Same-thread calls execute immediately. Task exceptions are logged and do
not interrupt subsequent tasks.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Build core/events.py (cross-cut events beyond StateChangedEvent)

**Files:**
- Modify: `src/yoyopod/core/events.py`
- Create: `tests/core/test_events.py`

- [ ] **Step 8.1: Write `tests/core/test_events.py` exercising all core event types**

Create `tests/core/test_events.py`:

```python
"""Tests for yoyopod.core.events."""

from __future__ import annotations

from yoyopod.core.events import (
    BackendStoppedEvent,
    LifecycleEvent,
    ResponsivenessLagEvent,
    ShutdownRequestedEvent,
    StateChangedEvent,
    UserActivityEvent,
)
from yoyopod.core.states import StateValue


def test_state_changed_event_is_frozen() -> None:
    ev = StateChangedEvent(
        entity="call.state",
        old=None,
        new=StateValue(value="idle", attrs={}, last_changed_at=0.0),
    )
    try:
        ev.entity = "other"  # type: ignore[misc]
    except Exception as exc:
        assert isinstance(exc, AttributeError) or "frozen" in str(exc).lower()


def test_user_activity_event_default_action_name() -> None:
    ev = UserActivityEvent()
    assert ev.action_name is None


def test_user_activity_event_with_action() -> None:
    ev = UserActivityEvent(action_name="button_select")
    assert ev.action_name == "button_select"


def test_backend_stopped_event_includes_domain_and_reason() -> None:
    ev = BackendStoppedEvent(domain="call", reason="register_failed")
    assert ev.domain == "call"
    assert ev.reason == "register_failed"


def test_shutdown_requested_event_defaults() -> None:
    ev = ShutdownRequestedEvent(reason="low_battery")
    assert ev.reason == "low_battery"
    assert ev.delay_seconds == 0.0


def test_lifecycle_event_phases() -> None:
    ev = LifecycleEvent(integration="call", phase="setup_complete")
    assert ev.integration == "call"
    assert ev.phase == "setup_complete"


def test_responsiveness_lag_event() -> None:
    ev = ResponsivenessLagEvent(duration_ms=250.0, context="bus_drain")
    assert ev.duration_ms == 250.0
    assert ev.context == "bus_drain"
```

- [ ] **Step 8.2: Run tests; most should fail on missing imports**

Run:
```bash
uv run pytest tests/core/test_events.py -v
```

Expected: ImportError for events not yet defined.

- [ ] **Step 8.3: Expand `src/yoyopod/core/events.py`**

Replace the contents of `src/yoyopod/core/events.py`:

```python
"""Core event types for YoyoPod's typed event bus.

Domain-specific events live in each integration's events.py file. This module
carries only the universal StateChangedEvent and cross-cutting signals that
any integration may publish or subscribe to. See docs/superpowers/specs/
2026-04-21-phase-a-spine-rewrite-design.md §6.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from yoyopod.core.states import StateValue


@dataclass(frozen=True, slots=True)
class StateChangedEvent:
    """Universal state-change notification."""

    entity: str
    old: "StateValue | None"
    new: "StateValue"


@dataclass(frozen=True, slots=True)
class UserActivityEvent:
    """User input activity detected (keep-awake trigger)."""

    action_name: str | None = None


@dataclass(frozen=True, slots=True)
class BackendStoppedEvent:
    """A backend adapter has stopped (crashed or gracefully exited)."""

    domain: str
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ShutdownRequestedEvent:
    """Graceful shutdown requested from any integration."""

    reason: str
    delay_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    """Integration setup/teardown boundary marker."""

    integration: str
    phase: Literal["setup_start", "setup_complete", "teardown_start", "teardown_complete"]


@dataclass(frozen=True, slots=True)
class ResponsivenessLagEvent:
    """Main-loop tick exceeded threshold."""

    duration_ms: float
    context: str = ""
```

- [ ] **Step 8.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/core/test_events.py -v
```

Expected: all passing.

- [ ] **Step 8.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/core/events.py tests/core/test_events.py
uv run ruff check src/yoyopod/core/events.py tests/core/test_events.py
uv run mypy src/yoyopod/core/events.py
```

Expected: all green.

- [ ] **Step 8.6: Re-export new events from `core/__init__.py`**

Append to `src/yoyopod/core/__init__.py`:

```python
from yoyopod.core.events import (
    BackendStoppedEvent,
    LifecycleEvent,
    ResponsivenessLagEvent,
    ShutdownRequestedEvent,
    UserActivityEvent,
)
```

Extend `__all__`:

```python
__all__ = [
    "Bus",
    "States",
    "StateValue",
    "StateChangedEvent",
    "Services",
    "ServiceNotRegisteredError",
    "MainThreadScheduler",
    "UserActivityEvent",
    "BackendStoppedEvent",
    "ShutdownRequestedEvent",
    "LifecycleEvent",
    "ResponsivenessLagEvent",
]
```

- [ ] **Step 8.7: Commit**

Run:
```bash
git add src/yoyopod/core/__init__.py src/yoyopod/core/events.py tests/core/test_events.py
git commit -m "$(cat <<'EOF'
feat(core): expand core events with cross-cut signals

Adds UserActivityEvent, BackendStoppedEvent, ShutdownRequestedEvent,
LifecycleEvent, and ResponsivenessLagEvent. Domain-specific events stay
in each integration's own events.py file.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Build log ring buffer with TDD

**Files:**
- Create: `tests/core/test_logbuffer.py`
- Create: `src/yoyopod/core/logbuffer.py`

- [ ] **Step 9.1: Write `tests/core/test_logbuffer.py`**

Create `tests/core/test_logbuffer.py`:

```python
"""Tests for yoyopod.core.logbuffer.LogBuffer."""

from __future__ import annotations

from yoyopod.core.logbuffer import LogBuffer, LogEntry


def test_append_and_recent_returns_all_entries_under_capacity() -> None:
    buf = LogBuffer(capacity=10)
    buf.append(LogEntry(ts=1.0, kind="event", payload={"a": 1}))
    buf.append(LogEntry(ts=2.0, kind="command", payload={"b": 2}))

    entries = buf.recent(10)

    assert len(entries) == 2
    assert entries[0].kind == "event"
    assert entries[1].kind == "command"


def test_recent_count_returns_last_n() -> None:
    buf = LogBuffer(capacity=10)
    for i in range(5):
        buf.append(LogEntry(ts=float(i), kind="event", payload={"i": i}))

    last_two = buf.recent(2)

    assert len(last_two) == 2
    assert last_two[0].payload == {"i": 3}
    assert last_two[1].payload == {"i": 4}


def test_append_beyond_capacity_drops_oldest() -> None:
    buf = LogBuffer(capacity=3)
    for i in range(5):
        buf.append(LogEntry(ts=float(i), kind="event", payload={"i": i}))

    all_entries = buf.recent(10)

    assert len(all_entries) == 3
    assert all_entries[0].payload == {"i": 2}
    assert all_entries[1].payload == {"i": 3}
    assert all_entries[2].payload == {"i": 4}


def test_recent_more_than_available_returns_all() -> None:
    buf = LogBuffer(capacity=10)
    buf.append(LogEntry(ts=1.0, kind="event", payload={}))

    assert len(buf.recent(100)) == 1


def test_empty_buffer_returns_empty_list() -> None:
    buf = LogBuffer(capacity=10)
    assert buf.recent(10) == []


def test_entries_are_frozen() -> None:
    entry = LogEntry(ts=1.0, kind="event", payload={})
    try:
        entry.kind = "command"  # type: ignore[misc]
    except Exception as exc:
        assert isinstance(exc, AttributeError) or "frozen" in str(exc).lower()
```

- [ ] **Step 9.2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/core/test_logbuffer.py -v
```

Expected: import error on `yoyopod.core.logbuffer`.

- [ ] **Step 9.3: Implement `src/yoyopod/core/logbuffer.py`**

Create `src/yoyopod/core/logbuffer.py`:

```python
"""In-memory ring buffer for recent log entries.

Used by the diagnostics integration (later plan) to provide `recent_events()`
access to the app shell. Kept small and dependency-free so it can be used in
tests without a diagnostics integration present. See docs/superpowers/specs/
2026-04-21-phase-a-spine-rewrite-design.md §4.5, §8.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Literal


LogKind = Literal["event", "command", "error", "lifecycle"]


@dataclass(frozen=True, slots=True)
class LogEntry:
    """One entry in the log ring buffer."""

    ts: float
    kind: LogKind
    payload: dict[str, Any]


class LogBuffer:
    """Fixed-capacity FIFO ring buffer of LogEntry."""

    def __init__(self, capacity: int = 500) -> None:
        if capacity <= 0:
            raise ValueError("LogBuffer capacity must be positive")
        self._entries: Deque[LogEntry] = deque(maxlen=capacity)

    def append(self, entry: LogEntry) -> None:
        """Append an entry, dropping oldest if at capacity."""
        self._entries.append(entry)

    def recent(self, count: int) -> list[LogEntry]:
        """Return up to `count` most recent entries, in chronological order."""
        if count <= 0:
            return []
        snapshot = list(self._entries)
        return snapshot[-count:]
```

- [ ] **Step 9.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/core/test_logbuffer.py -v
```

Expected: all passing.

- [ ] **Step 9.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/core/logbuffer.py tests/core/test_logbuffer.py
uv run ruff check src/yoyopod/core/logbuffer.py tests/core/test_logbuffer.py
uv run mypy src/yoyopod/core/logbuffer.py
```

Expected: all green.

- [ ] **Step 9.6: Re-export**

Append to `src/yoyopod/core/__init__.py`:

```python
from yoyopod.core.logbuffer import LogBuffer, LogEntry
```

Extend `__all__`:

```python
__all__ = [
    "Bus",
    "States",
    "StateValue",
    "StateChangedEvent",
    "Services",
    "ServiceNotRegisteredError",
    "MainThreadScheduler",
    "UserActivityEvent",
    "BackendStoppedEvent",
    "ShutdownRequestedEvent",
    "LifecycleEvent",
    "ResponsivenessLagEvent",
    "LogBuffer",
    "LogEntry",
]
```

- [ ] **Step 9.7: Commit**

Run:
```bash
git add src/yoyopod/core/__init__.py src/yoyopod/core/logbuffer.py tests/core/test_logbuffer.py
git commit -m "$(cat <<'EOF'
feat(core): add LogBuffer ring buffer for recent events

Fixed-capacity FIFO deque of LogEntry(ts, kind, payload). Used by the
diagnostics integration in a later plan; kept dependency-free so tests
can exercise it without a diagnostics stack.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Build `YoyoPodApp` shell with TDD

**Files:**
- Create: `tests/core/test_app_shell.py`
- Create: `src/yoyopod/core/app_shell.py`

- [ ] **Step 10.1: Write `tests/core/test_app_shell.py`**

Create `tests/core/test_app_shell.py`:

```python
"""Tests for yoyopod.core.app_shell.YoyoPodApp.

These tests construct the app shell with no integrations loaded; they
exercise the primitive wiring, drain() helper, recent_events() helper, and
teardown ordering. Config loading is NOT exercised here — that belongs in a
later plan when integrations actually need config.
"""

from __future__ import annotations

from yoyopod.core.app_shell import YoyoPodApp


def test_app_shell_exposes_core_primitives() -> None:
    app = YoyoPodApp()

    assert app.bus is not None
    assert app.states is not None
    assert app.services is not None
    assert app.scheduler is not None
    assert app.log_buffer is not None


def test_drain_runs_scheduler_then_bus_to_quiescence() -> None:
    app = YoyoPodApp()
    captured: list[str] = []

    def on_state_change(ev):
        captured.append(f"state:{ev.entity}")

    from yoyopod.core.events import StateChangedEvent

    app.bus.subscribe(StateChangedEvent, on_state_change)

    app.states.set("call.state", "idle")

    app.drain()

    assert captured == ["state:call.state"]


def test_recent_events_returns_empty_before_any_log_appends() -> None:
    app = YoyoPodApp()

    assert app.recent_events() == []


def test_recent_events_returns_appended_entries() -> None:
    app = YoyoPodApp()
    from yoyopod.core.logbuffer import LogEntry

    app.log_buffer.append(LogEntry(ts=1.0, kind="event", payload={"x": 1}))
    app.log_buffer.append(LogEntry(ts=2.0, kind="command", payload={"y": 2}))

    entries = app.recent_events(count=10)

    assert len(entries) == 2
    assert entries[0].payload == {"x": 1}


def test_register_integration_tracks_order() -> None:
    app = YoyoPodApp()
    order: list[str] = []

    app.register_integration("alpha", setup=lambda _a: order.append("alpha-setup"))
    app.register_integration("beta", setup=lambda _a: order.append("beta-setup"))

    app.setup()

    assert order == ["alpha-setup", "beta-setup"]


def test_teardown_runs_in_reverse_registration_order() -> None:
    app = YoyoPodApp()
    order: list[str] = []

    app.register_integration(
        "alpha",
        setup=lambda _a: None,
        teardown=lambda _a: order.append("alpha-teardown"),
    )
    app.register_integration(
        "beta",
        setup=lambda _a: None,
        teardown=lambda _a: order.append("beta-teardown"),
    )

    app.setup()
    app.stop()

    assert order == ["beta-teardown", "alpha-teardown"]


def test_stop_is_idempotent() -> None:
    app = YoyoPodApp()
    call_count = {"n": 0}

    app.register_integration(
        "alpha",
        setup=lambda _a: None,
        teardown=lambda _a: call_count.__setitem__("n", call_count["n"] + 1),
    )

    app.setup()
    app.stop()
    app.stop()

    assert call_count["n"] == 1


def test_setup_fires_lifecycle_events_on_bus() -> None:
    app = YoyoPodApp()
    from yoyopod.core.events import LifecycleEvent

    captured: list[LifecycleEvent] = []
    app.bus.subscribe(LifecycleEvent, lambda ev: captured.append(ev))

    app.register_integration("alpha", setup=lambda _a: None)

    app.setup()
    app.drain()

    phases = [(ev.integration, ev.phase) for ev in captured]
    assert ("alpha", "setup_start") in phases
    assert ("alpha", "setup_complete") in phases
```

- [ ] **Step 10.2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/core/test_app_shell.py -v
```

Expected: ModuleNotFoundError on `yoyopod.core.app_shell`.

- [ ] **Step 10.3: Implement `src/yoyopod/core/app_shell.py`**

Create `src/yoyopod/core/app_shell.py`:

```python
"""Main app shell for YoyoPod.

Owns the core primitives (bus, states, services, scheduler, log_buffer) and
the registration/setup/teardown lifecycle for integrations. Does NOT load
config or run the main loop in Phase A's initial slice — those are added in
the next plan when the first integration is migrated.
See docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §4.5.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable

from loguru import logger

from yoyopod.core.bus import Bus
from yoyopod.core.events import LifecycleEvent
from yoyopod.core.logbuffer import LogBuffer, LogEntry
from yoyopod.core.scheduler import MainThreadScheduler
from yoyopod.core.services import Services
from yoyopod.core.states import States


SetupFn = Callable[["YoyoPodApp"], None]
TeardownFn = Callable[["YoyoPodApp"], None]


@dataclass(slots=True)
class _Integration:
    name: str
    setup: SetupFn
    teardown: TeardownFn | None = None


class YoyoPodApp:
    """Composition root for YoyoPod's core primitives + integration registry."""

    bus: Bus
    states: States
    services: Services
    scheduler: MainThreadScheduler
    log_buffer: LogBuffer

    def __init__(self, log_capacity: int = 500) -> None:
        main_thread_id = threading.get_ident()
        self.bus = Bus(main_thread_id=main_thread_id, strict=True)
        self.scheduler = MainThreadScheduler(main_thread_id=main_thread_id)
        self.states = States(bus=self.bus)
        self.services = Services(bus=self.bus)
        self.log_buffer = LogBuffer(capacity=log_capacity)
        self._integrations: list[_Integration] = []
        self._setup_called = False
        self._stopped = False

    def register_integration(
        self,
        name: str,
        setup: SetupFn,
        teardown: TeardownFn | None = None,
    ) -> None:
        """Record an integration to be initialised in `setup()`."""
        if self._setup_called:
            raise RuntimeError(f"Cannot register integration '{name}' after setup()")
        self._integrations.append(_Integration(name=name, setup=setup, teardown=teardown))

    def setup(self) -> None:
        """Initialise all registered integrations in registration order."""
        if self._setup_called:
            return
        for integration in self._integrations:
            logger.debug("Integration {} setup_start", integration.name)
            self.bus.publish(LifecycleEvent(integration=integration.name, phase="setup_start"))
            try:
                integration.setup(self)
            except Exception:
                logger.exception("Integration {} setup failed", integration.name)
                raise
            self.bus.publish(LifecycleEvent(integration=integration.name, phase="setup_complete"))
            logger.debug("Integration {} setup_complete", integration.name)
        self._setup_called = True

    def stop(self) -> None:
        """Tear down integrations in reverse order. Idempotent."""
        if self._stopped:
            return
        for integration in reversed(self._integrations):
            if integration.teardown is None:
                continue
            logger.debug("Integration {} teardown_start", integration.name)
            self.bus.publish(LifecycleEvent(integration=integration.name, phase="teardown_start"))
            try:
                integration.teardown(self)
            except Exception:
                logger.exception("Integration {} teardown failed", integration.name)
            self.bus.publish(
                LifecycleEvent(integration=integration.name, phase="teardown_complete")
            )
            logger.debug("Integration {} teardown_complete", integration.name)
        self._stopped = True

    def drain(self) -> None:
        """Drain scheduler then bus until both are quiescent.

        Test-friendly; production run loop handles drains explicitly per tick.
        """
        while self.scheduler.pending_count() > 0 or self.bus.pending_count() > 0:
            self.scheduler.drain()
            self.bus.drain()

    def recent_events(self, count: int = 500) -> list[LogEntry]:
        """Return up to `count` most recent log entries."""
        return self.log_buffer.recent(count)
```

- [ ] **Step 10.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/core/test_app_shell.py -v
```

Expected: all passing.

- [ ] **Step 10.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/core/app_shell.py tests/core/test_app_shell.py
uv run ruff check src/yoyopod/core/app_shell.py tests/core/test_app_shell.py
uv run mypy src/yoyopod/core/app_shell.py
```

Expected: all green.

- [ ] **Step 10.6: Re-export `YoyoPodApp`**

Append to `src/yoyopod/core/__init__.py`:

```python
from yoyopod.core.app_shell import YoyoPodApp
```

Extend `__all__`:

```python
__all__ = [
    "Bus",
    "States",
    "StateValue",
    "StateChangedEvent",
    "Services",
    "ServiceNotRegisteredError",
    "MainThreadScheduler",
    "UserActivityEvent",
    "BackendStoppedEvent",
    "ShutdownRequestedEvent",
    "LifecycleEvent",
    "ResponsivenessLagEvent",
    "LogBuffer",
    "LogEntry",
    "YoyoPodApp",
]
```

- [ ] **Step 10.7: Commit**

Run:
```bash
git add src/yoyopod/core/__init__.py src/yoyopod/core/app_shell.py tests/core/test_app_shell.py
git commit -m "$(cat <<'EOF'
feat(core): add YoyoPodApp composition-root shell

Owns bus/states/services/scheduler/log_buffer. Integration registry with
registration-order setup and reverse-order teardown. Emits LifecycleEvent
around each setup/teardown. Idempotent stop(). drain() helper for tests.
Does NOT include run loop or config loading — those land in the next plan
when the first integration needs them.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Build `core/testing.py` helpers with TDD

**Files:**
- Create: `tests/core/test_testing_helpers.py`
- Create: `src/yoyopod/core/testing.py`

- [ ] **Step 11.1: Write `tests/core/test_testing_helpers.py`**

Create `tests/core/test_testing_helpers.py`:

```python
"""Tests for yoyopod.core.testing helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from yoyopod.core.testing import assert_events_contain, build_test_app, drain_all
from yoyopod.core.events import StateChangedEvent


@dataclass(frozen=True, slots=True)
class AlphaEvent:
    value: int


@dataclass(frozen=True, slots=True)
class BetaEvent:
    name: str


def test_build_test_app_returns_app_with_primitives() -> None:
    app = build_test_app()

    assert app.bus is not None
    assert app.states is not None
    assert app.services is not None
    assert app.scheduler is not None


def test_drain_all_drains_both_scheduler_and_bus() -> None:
    app = build_test_app()
    captured: list[int] = []

    app.bus.subscribe(AlphaEvent, lambda ev: captured.append(ev.value))

    app.bus.publish(AlphaEvent(value=1))
    app.bus.publish(AlphaEvent(value=2))

    drain_all(app)

    assert captured == [1, 2]


def test_assert_events_contain_passes_when_subsequence_present() -> None:
    events = [AlphaEvent(1), BetaEvent("b"), AlphaEvent(2)]

    assert_events_contain(events, [AlphaEvent(1), AlphaEvent(2)])


def test_assert_events_contain_passes_for_contiguous_match() -> None:
    events = [AlphaEvent(1), BetaEvent("b"), AlphaEvent(2)]

    assert_events_contain(events, [BetaEvent("b"), AlphaEvent(2)])


def test_assert_events_contain_raises_when_missing() -> None:
    events = [AlphaEvent(1), BetaEvent("b")]

    with pytest.raises(AssertionError, match="not found"):
        assert_events_contain(events, [AlphaEvent(99)])


def test_assert_events_contain_raises_when_order_wrong() -> None:
    events = [AlphaEvent(1), BetaEvent("b")]

    with pytest.raises(AssertionError):
        assert_events_contain(events, [BetaEvent("b"), AlphaEvent(1)])


def test_build_test_app_supports_drain_of_state_changes() -> None:
    app = build_test_app()
    captured: list[str] = []
    app.bus.subscribe(StateChangedEvent, lambda ev: captured.append(ev.entity))

    app.states.set("call.state", "idle")
    drain_all(app)

    assert captured == ["call.state"]
```

- [ ] **Step 11.2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/core/test_testing_helpers.py -v
```

Expected: ModuleNotFoundError on `yoyopod.core.testing`.

- [ ] **Step 11.3: Implement `src/yoyopod/core/testing.py`**

Create `src/yoyopod/core/testing.py`:

```python
"""Test helpers for the YoyoPod core primitives.

Used by unit tests and future integration/e2e tests. Keep this module
dependency-free so it does not pull in integrations. See docs/superpowers/
specs/2026-04-21-phase-a-spine-rewrite-design.md §12.4.
"""

from __future__ import annotations

from typing import Any

from yoyopod.core.app_shell import YoyoPodApp


def build_test_app(log_capacity: int = 500) -> YoyoPodApp:
    """Build a YoyoPodApp with no integrations, suitable for core unit tests.

    Later plans will add an integration-aware variant that preloads the
    integrations under test.
    """
    return YoyoPodApp(log_capacity=log_capacity)


def drain_all(app: YoyoPodApp) -> None:
    """Drain scheduler and bus until both are quiescent."""
    app.drain()


def assert_events_contain(events: list[Any], expected_subsequence: list[Any]) -> None:
    """Assert the expected events appear in the given order somewhere in events.

    Non-contiguous matches are allowed (events between expected items are OK);
    order must be preserved. Raises AssertionError with a readable diff on
    failure.
    """
    remaining = list(expected_subsequence)
    for ev in events:
        if remaining and ev == remaining[0]:
            remaining.pop(0)
    if remaining:
        raise AssertionError(
            "Expected event(s) not found in order:\n"
            f"  first unmatched: {remaining[0]!r}\n"
            f"  actual stream:   {events!r}\n"
            f"  expected stream: {expected_subsequence!r}"
        )
```

- [ ] **Step 11.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/core/test_testing_helpers.py -v
```

Expected: all passing.

- [ ] **Step 11.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/core/testing.py tests/core/test_testing_helpers.py
uv run ruff check src/yoyopod/core/testing.py tests/core/test_testing_helpers.py
uv run mypy src/yoyopod/core/testing.py
```

Expected: all green.

- [ ] **Step 11.6: Re-export**

Append to `src/yoyopod/core/__init__.py`:

```python
from yoyopod.core.testing import assert_events_contain, build_test_app, drain_all
```

Extend `__all__`:

```python
__all__ = [
    "Bus",
    "States",
    "StateValue",
    "StateChangedEvent",
    "Services",
    "ServiceNotRegisteredError",
    "MainThreadScheduler",
    "UserActivityEvent",
    "BackendStoppedEvent",
    "ShutdownRequestedEvent",
    "LifecycleEvent",
    "ResponsivenessLagEvent",
    "LogBuffer",
    "LogEntry",
    "YoyoPodApp",
    "build_test_app",
    "drain_all",
    "assert_events_contain",
]
```

- [ ] **Step 11.7: Commit**

Run:
```bash
git add src/yoyopod/core/__init__.py src/yoyopod/core/testing.py tests/core/test_testing_helpers.py
git commit -m "$(cat <<'EOF'
feat(core): add core.testing helpers (build_test_app, drain_all, assert_events_contain)

Dependency-free test helpers for core primitives. Integration-aware
variant will extend these in a later plan.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: End-to-end core integration smoke test

**Files:**
- Create: `tests/core/test_integration.py`

- [ ] **Step 12.1: Write an end-to-end smoke test exercising every core primitive together**

Create `tests/core/test_integration.py`:

```python
"""End-to-end smoke test for the core primitives working together."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from yoyopod.core.events import StateChangedEvent, UserActivityEvent
from yoyopod.core.testing import (
    assert_events_contain,
    build_test_app,
    drain_all,
)


@dataclass(frozen=True, slots=True)
class SetCallStateCommand:
    value: str


def test_full_round_trip_backend_to_state_to_subscriber() -> None:
    """Simulates: backend thread schedules a state update, main loop drains it,
    subscribers observe StateChangedEvent and chain an effect via services."""
    app = build_test_app()

    captured_state_changes: list[str] = []
    captured_activities: list[str | None] = []

    app.bus.subscribe(
        StateChangedEvent,
        lambda ev: captured_state_changes.append(f"{ev.entity}:{ev.new.value}"),
    )
    app.bus.subscribe(
        UserActivityEvent,
        lambda ev: captured_activities.append(ev.action_name),
    )

    def set_call_state(cmd: SetCallStateCommand) -> None:
        app.states.set("call.state", cmd.value)
        app.bus.publish(UserActivityEvent(action_name=f"call_{cmd.value}"))

    app.services.register("call", "set_state", set_call_state)

    def from_bg_thread() -> None:
        app.scheduler.run_on_main(
            lambda: app.services.call("call", "set_state", SetCallStateCommand(value="incoming"))
        )

    t = threading.Thread(target=from_bg_thread)
    t.start()
    t.join()

    drain_all(app)

    assert captured_state_changes == ["call.state:incoming"]
    assert captured_activities == ["call_incoming"]


def test_integration_lifecycle_events_and_teardown_reverse_order() -> None:
    """Integrations register, setup fires events in order, teardown reverses."""
    app = build_test_app()
    log: list[str] = []

    def setup_a(_app):
        log.append("setup-a")

    def teardown_a(_app):
        log.append("teardown-a")

    def setup_b(_app):
        log.append("setup-b")

    def teardown_b(_app):
        log.append("teardown-b")

    app.register_integration("a", setup=setup_a, teardown=teardown_a)
    app.register_integration("b", setup=setup_b, teardown=teardown_b)

    app.setup()
    app.stop()

    assert log == ["setup-a", "setup-b", "teardown-b", "teardown-a"]


def test_off_main_bus_publish_rejected() -> None:
    """The core bus rejects direct publishes from background threads."""
    app = build_test_app()
    errors: list[RuntimeError] = []

    def from_bg() -> None:
        try:
            app.bus.publish(UserActivityEvent(action_name="bad"))
        except RuntimeError as exc:
            errors.append(exc)

    t = threading.Thread(target=from_bg)
    t.start()
    t.join()

    assert len(errors) == 1
    assert "non-main thread" in str(errors[0])


def test_event_trace_assertion_works() -> None:
    """assert_events_contain composes cleanly with the app primitives."""
    app = build_test_app()
    captured_events: list = []
    app.bus.subscribe(StateChangedEvent, lambda ev: captured_events.append(ev))

    app.states.set("call.state", "idle")
    app.states.set("music.state", "playing")
    drain_all(app)

    changed_entities = [ev.entity for ev in captured_events]
    assert changed_entities == ["call.state", "music.state"]
    from yoyopod.core.states import StateValue
    # Direct object equality is feasible since StateValue is a frozen dataclass.
    # We only assert the entity names are present in order.
    entity_names_only = [ev.entity for ev in captured_events]
    assert entity_names_only == ["call.state", "music.state"]
    # And the assertion helper works on any event list:
    assert_events_contain(captured_events, [captured_events[0]])
```

- [ ] **Step 12.2: Run the smoke test**

Run:
```bash
uv run pytest tests/core/test_integration.py -v
```

Expected: all passing.

- [ ] **Step 12.3: Run the full core test suite to confirm nothing else regressed**

Run:
```bash
uv run pytest tests/core/ -v
```

Expected: all tests across `tests/core/` green.

- [ ] **Step 12.4: Format, lint, type-check**

Run:
```bash
uv run black tests/core/test_integration.py
uv run ruff check tests/core/test_integration.py
```

Expected: all green.

- [ ] **Step 12.5: Commit**

Run:
```bash
git add tests/core/test_integration.py
git commit -m "$(cat <<'EOF'
test(core): end-to-end smoke exercising all core primitives together

Covers backend-thread → scheduler → main-thread → state → bus → subscriber
round trip; integration setup/teardown order; strict off-main rejection;
event-trace assertion helper.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Update CLAUDE.md with the new core primitives reference

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 13.1: Add a "Core Primitives" section to CLAUDE.md**

Edit `CLAUDE.md`. Insert the following new section directly after the "Current Status" section (before "LVGL Status"):

```markdown
---

## Core Primitives (Phase A, in-progress)

Phase A of the architectural rewrite has introduced the `src/yoyopod/core/`
package: a state store + typed event bus + service registry that will host
every integration as domain-specific logic is migrated.

Primitives (all in `src/yoyopod/core/`):

- `Bus` (`bus.py`) — main-thread-only typed event bus; strict mode raises on off-main publish.
- `States` (`states.py`) — entity state store keyed by `domain.entity_name`. `set()` fires `StateChangedEvent`.
- `Services` (`services.py`) — command registry keyed by `(domain, service)`. `call(domain, service, data)` dispatches.
- `MainThreadScheduler` (`scheduler.py`) — backend threads use `run_on_main(fn)` to marshal tasks onto the main thread.
- `LogBuffer` / `LogEntry` (`logbuffer.py`) — fixed-capacity ring buffer consumed by the future diagnostics integration.
- `YoyoPodApp` (`app_shell.py`) — composition root. Integration registry, setup/teardown lifecycle, drain helper.
- `build_test_app`, `drain_all`, `assert_events_contain` (`testing.py`) — core test helpers.

See `docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md` for
the full architectural contract. Legacy modules (`src/yoyopod/fsm.py`,
`src/yoyopod/event_bus.py`, `src/yoyopod/coordinators/`, `src/yoyopod/runtime/`)
remain in place until each domain is migrated in subsequent Phase A plans.
```

- [ ] **Step 13.2: Commit**

Run:
```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs: document core/ primitives in CLAUDE.md

Added "Core Primitives (Phase A, in-progress)" section pointing
readers/agents at src/yoyopod/core/ and the Phase A design spec. Legacy
modules remain documented until their owning domain migrates.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Final verification

**Files:** none (verification only)

- [ ] **Step 14.1: Full CI gate**

Run:
```bash
uv run python scripts/quality.py ci
```

Expected: all green — format, lint, type, tests. This honours the user's pre-commit memory.

- [ ] **Step 14.2: Confirm all new files are tracked by git**

Run:
```bash
git status
```

Expected: `nothing to commit, working tree clean` (ignoring the untracked `.claude/settings.local.json`).

- [ ] **Step 14.3: Verify branch has the expected commit history**

Run:
```bash
git log --oneline arch/phase-a-spine-rewrite ^main
```

Expected commits (top-to-bottom, newest first):
```
docs: document core/ primitives in CLAUDE.md
test(core): end-to-end smoke exercising all core primitives together
feat(core): add core.testing helpers (build_test_app, drain_all, assert_events_contain)
feat(core): add YoyoPodApp composition-root shell
feat(core): add LogBuffer ring buffer for recent events
feat(core): expand core events with cross-cut signals
feat(core): add MainThreadScheduler
feat(core): add Services command registry
feat(core): add States entity store + StateChangedEvent
feat(core): add typed Bus primitive
chore(core): scaffold core package and tests directory
chore(cli): drop yoyoctl aliases across live code, docs, and rules
```

12 commits. If any are missing, find the task they came from and re-run the commit step for that task.

- [ ] **Step 14.4: Verify only preserved historical files still reference `yoyoctl`**

Run:
```bash
git grep -l "yoyoctl"
```

Expected: exactly these files (historical design/plan docs preserved in Task 2):
- `docs/superpowers/specs/2026-04-10-yoyoctl-cli-design.md`
- `docs/superpowers/specs/2026-04-20-cli-polish-design.md`
- `docs/superpowers/specs/2026-04-13-4g-connectivity-design.md`
- `docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md`
- `docs/superpowers/plans/2026-04-10-yoyoctl-cli.md`
- `docs/superpowers/plans/2026-04-20-cli-polish.md`
- `docs/superpowers/plans/2026-04-13-4g-connectivity.md`
- `docs/superpowers/plans/2026-04-13-cubie-pimoroni-driver.md`
- `docs/superpowers/plans/2026-04-21-phase-a-core-scaffold.md`

Any match outside this list is a bug — open the file, confirm whether it's a live reference (fix it) or genuinely historical (add to the PRESERVE list in a follow-up).

- [ ] **Step 14.5: Confirm the app still runs**

Run:
```bash
uv run python yoyopod.py --help
```

Expected: Typer help output — app still starts and the CLI still dispatches. (No integrations migrated yet, so full app run is not expected to do more than before.)

---

## Definition of Done

- Branch `arch/phase-a-spine-rewrite` exists with 12 commits on top of `main`.
- `src/yoyopod/core/` contains `bus.py`, `states.py`, `services.py`, `scheduler.py`, `events.py`, `logbuffer.py`, `app_shell.py`, `testing.py`, plus `__init__.py` re-exporting the public surface.
- `tests/core/` contains one test file per primitive plus `test_integration.py` smoke test — all passing.
- `uv run python scripts/quality.py ci` is green.
- No `yoyoctl` references outside git history / `docs/archive/` / historical plan docs.
- CLAUDE.md has a "Core Primitives (Phase A, in-progress)" section pointing to the core package and the design spec.
- The production Pi runtime (`yoyopod.py`) still starts without error — no integrations have been migrated yet, so behaviour is unchanged beyond the CLI rename cleanup.

---

## What's next (not this plan)

After this plan is executed and reviewed:

1. **Plan 2:** Power pilot integration. Migrate `PowerManager`/`PowerRuntimeService`/`PowerCoordinator` into `integrations/power/` end-to-end. Delete the old classes. Pattern validated.
2. **Plan 3:** Easy batch (network, location, contacts, cloud).
3. **Plan 4:** Focus + diagnostics + screen + voice.
4. **Plan 5:** Music.
5. **Plan 6:** Call.
6. **Plan 7:** Recovery + screen touch-up + dead-code removal + final sweep.

Each subsequent plan produces a clean, testable slice of the overall Phase A rewrite, building on the core primitives landed here.

---

*End of implementation plan.*
