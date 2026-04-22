# Phase A — Plan 2: Power Pilot Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the power subsystem to the new `core/` architecture as the pilot integration. Validate the A+3 pattern end-to-end on an isolated, well-understood domain before extending it to the other 10 integrations.

**Architecture:** Backend adapter (PiSugar) moves to `src/yoyopod/backends/power/`. The domain integration lives under `src/yoyopod/integrations/power/` with `setup(app)`, typed commands, and handlers that mirror backend events into the state store. Old `PowerManager`, `PowerRuntimeService`, `PowerCoordinator` classes are deleted at the end of this plan. A new main-loop integration point in `YoyoPodApp.run()` replaces the previous ad-hoc polling — `app.run()` now drains the scheduler, drains the bus, and ticks UI.

**Tech Stack:** Python 3.12+, pytest, uv, existing PiSugar socket/TCP backend + watchdog. No new runtime dependencies.

**Spec reference:** `docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md` §3.2 (directory layout), §5 (power entities), §7 (power commands), §9.2 (fate of PowerManager), §11.2 (step 3 — power pilot).

**Prerequisite:** Plan 1 (core scaffold) is executed — `src/yoyopod/core/` exists with tested primitives; branch `arch/phase-a-spine-rewrite` has the 12 Plan-1 commits.

---

## File Structure

### Files to create

- `src/yoyopod/backends/__init__.py` — backends package marker
- `src/yoyopod/backends/power/__init__.py` — power backend package marker + public surface
- `src/yoyopod/backends/power/pisugar.py` — moved from `src/yoyopod/power/backend.py`
- `src/yoyopod/backends/power/watchdog.py` — moved from `src/yoyopod/power/watchdog.py`
- `src/yoyopod/integrations/__init__.py` — integrations package marker
- `src/yoyopod/integrations/power/__init__.py` — `setup(app)` + `teardown(app)`
- `src/yoyopod/integrations/power/commands.py` — `ShutdownCommand`, `RebootCommand`, etc.
- `src/yoyopod/integrations/power/handlers.py` — state-update logic, low-battery policy
- `src/yoyopod/integrations/power/poller.py` — background thread that polls the backend
- `tests/integrations/__init__.py`
- `tests/integrations/test_power.py`

### Files to modify

- `src/yoyopod/core/app_shell.py` — add `run()` main loop; add `config` attribute
- `src/yoyopod/app.py` — stub — will be rewritten in Plan 8; for now point `main` at `YoyoPodApp`

### Files to move (git mv)

- `src/yoyopod/power/backend.py` → `src/yoyopod/backends/power/pisugar.py`
- `src/yoyopod/power/watchdog.py` → `src/yoyopod/backends/power/watchdog.py`

### Files to delete

- `src/yoyopod/power/manager.py` (PowerManager — replaced by `integrations/power/`)
- `src/yoyopod/power/policies.py` (logic folds into `handlers.py`)
- `src/yoyopod/power/events.py` (power-specific events become domain events under `integrations/power/`)
- `src/yoyopod/power/__init__.py` (package itself dies)
- `src/yoyopod/runtime/power.py` (PowerRuntimeService — delete class, runtime/ stays because other services still live there)
- `src/yoyopod/coordinators/power.py` (PowerCoordinator)

---

## Task 1: Branch state verification

**Files:** none (verification only)

- [ ] **Step 1.1: Confirm you're on the Phase A branch with Plan 1 committed**

Run:
```bash
git branch --show-current
git log --oneline -15
```

Expected: branch is `arch/phase-a-spine-rewrite`; the top commits include `docs: renumber Phase C -> Phase B in Phase A spec`, `docs: Phase A core scaffold implementation plan (14 tasks)`, and the 12 Plan-1 commits (`feat(core): …`, `test(core): …`, `chore(core): …`, `chore(cli): …`).

- [ ] **Step 1.2: Verify `core/` primitives are in place**

Run:
```bash
ls src/yoyopod/core/
uv run pytest tests/core/ -q
```

Expected: all 8 core modules present (`__init__.py`, `app_shell.py`, `bus.py`, `events.py`, `logbuffer.py`, `scheduler.py`, `services.py`, `states.py`, `testing.py`); all core tests green.

- [ ] **Step 1.3: Read the existing power implementation for context**

Read these files and skim to understand the shape (DO NOT edit them yet):
```
src/yoyopod/power/backend.py
src/yoyopod/power/watchdog.py
src/yoyopod/power/manager.py
src/yoyopod/power/policies.py
src/yoyopod/power/events.py
src/yoyopod/runtime/power.py
src/yoyopod/coordinators/power.py
```

Goal: understand the current `PiSugarBackend` interface (connection, poll, get_snapshot, shutdown, set_rtc_alarm, etc.) and the responsibilities that are about to be re-homed (polling cadence, low-battery policy, watchdog feeding).

---

## Task 2: Scaffold `backends/` and move the PiSugar backend

**Files:**
- Create: `src/yoyopod/backends/__init__.py`
- Create: `src/yoyopod/backends/power/__init__.py`
- Move: `src/yoyopod/power/backend.py` → `src/yoyopod/backends/power/pisugar.py`
- Move: `src/yoyopod/power/watchdog.py` → `src/yoyopod/backends/power/watchdog.py`

- [ ] **Step 2.1: Create `src/yoyopod/backends/` and `src/yoyopod/backends/power/`**

Run:
```bash
mkdir -p src/yoyopod/backends/power
```

Create `src/yoyopod/backends/__init__.py` with:

```python
"""Adapter layer for external systems (SIP, media, power, network, location, voice).

See docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §3.2.
Integrations under src/yoyopod/integrations/ construct these adapters during
setup() and wire their events through the main-thread scheduler onto the bus.
"""
```

Create `src/yoyopod/backends/power/__init__.py` with:

```python
"""PiSugar power + watchdog backend adapters."""

from __future__ import annotations

from yoyopod.backends.power.pisugar import PiSugarBackend, PowerSnapshot
from yoyopod.backends.power.watchdog import PiSugarWatchdog

__all__ = ["PiSugarBackend", "PowerSnapshot", "PiSugarWatchdog"]
```

- [ ] **Step 2.2: Move the two backend files with `git mv`**

Run:
```bash
git mv src/yoyopod/power/backend.py src/yoyopod/backends/power/pisugar.py
git mv src/yoyopod/power/watchdog.py src/yoyopod/backends/power/watchdog.py
```

- [ ] **Step 2.3: Update imports inside the moved files**

Open `src/yoyopod/backends/power/pisugar.py`. Any imports of the form `from yoyopod.power...` referencing other files in the old package must be fixed. Most likely the backend is self-contained, but check for cross-references like `from yoyopod.power.events import PowerSnapshotUpdated` (if such imports exist) — those need to be rewritten to not depend on the legacy `power/` package (move the referenced types inline or into `backends/power/pisugar.py` if they belong there).

Open `src/yoyopod/backends/power/watchdog.py` — same check.

Verify there are no `yoyopod.power.` imports lingering in the moved files:
```bash
grep -rn "from yoyopod.power" src/yoyopod/backends/power/
```

Expected: no output (all internal references have been resolved).

- [ ] **Step 2.4: Update the one in-tree import of the watchdog class, if any, to the new location**

Run:
```bash
grep -rn "from yoyopod.power.watchdog" src/ tests/
grep -rn "from yoyopod.power.backend" src/ tests/
```

For each result, rewrite the import to `from yoyopod.backends.power import PiSugarBackend, PowerSnapshot, PiSugarWatchdog`. (At this stage the old `src/yoyopod/power/__init__.py` may still be re-exporting these; leave it intact for now — Task 10 deletes the old package entirely once everything is migrated.)

- [ ] **Step 2.5: Run the existing test suite to confirm the move didn't break anything**

Run:
```bash
uv run pytest tests/ -q --ignore=tests/core
```

Expected: same pass/fail set as before the move. If a test fails because of an import it previously resolved through `src/yoyopod/power/backend.py`, update its import to the new path.

- [ ] **Step 2.6: Commit the backend move**

Run:
```bash
git add -A
git commit -m "$(cat <<'EOF'
refactor(power): move PiSugar backend and watchdog under src/yoyopod/backends/power/

Relocates the adapter layer per the Phase A target directory layout.
integrations/power/ in the next task will consume these from the new path.
No logic changes; imports updated in place.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Scaffold `integrations/` and `integrations/power/`

**Files:**
- Create: `src/yoyopod/integrations/__init__.py`
- Create: `src/yoyopod/integrations/power/__init__.py` (empty for now)
- Create: `tests/integrations/__init__.py`
- Create: `tests/integrations/test_power.py` (empty for now)

- [ ] **Step 3.1: Create the directory structure**

Run:
```bash
mkdir -p src/yoyopod/integrations/power tests/integrations
```

- [ ] **Step 3.2: Populate `src/yoyopod/integrations/__init__.py`**

Create `src/yoyopod/integrations/__init__.py`:

```python
"""Domain integrations for YoyoPod.

Each subpackage is a self-contained integration with a setup(app) function
that wires backends, registers commands, and subscribes to events. Integrations
read and write the state store (app.states) and publish/subscribe to the bus.

See docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §3.2.
"""
```

- [ ] **Step 3.3: Populate placeholder `src/yoyopod/integrations/power/__init__.py`**

Create a minimal placeholder that will grow through Tasks 4–8:

```python
"""Power integration: battery, charging, RTC, watchdog, shutdown policy.

See docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §5
(entities), §7 (commands), §9.2 (fate of PowerManager).
"""

from __future__ import annotations

# Extended in Task 7 with setup() and teardown().
```

- [ ] **Step 3.4: Populate `tests/integrations/__init__.py`**

Create `tests/integrations/__init__.py` as a one-line marker:

```python

```

- [ ] **Step 3.5: Commit the scaffold**

Run:
```bash
git add src/yoyopod/integrations/ tests/integrations/__init__.py
git commit -m "$(cat <<'EOF'
chore(integrations): scaffold integrations package + power placeholder

Empty skeleton; populated in subsequent tasks.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Write power commands (typed dataclasses) with TDD

**Files:**
- Create: `tests/integrations/test_power_commands.py`
- Create: `src/yoyopod/integrations/power/commands.py`

- [ ] **Step 4.1: Write the failing test**

Create `tests/integrations/test_power_commands.py`:

```python
"""Tests for yoyopod.integrations.power.commands."""

from __future__ import annotations

from yoyopod.integrations.power.commands import (
    DisableRtcAlarmCommand,
    RebootCommand,
    SetRtcAlarmCommand,
    SetWatchdogCommand,
    ShutdownCommand,
    SyncRtcFromSystemCommand,
    SyncRtcToSystemCommand,
)


def test_shutdown_command_default_delay() -> None:
    cmd = ShutdownCommand(reason="test")
    assert cmd.reason == "test"
    assert cmd.delay_seconds == 0.0


def test_shutdown_command_with_delay() -> None:
    cmd = ShutdownCommand(reason="low_battery", delay_seconds=30.0)
    assert cmd.delay_seconds == 30.0


def test_reboot_command_defaults() -> None:
    cmd = RebootCommand(reason="settings")
    assert cmd.reason == "settings"


def test_set_watchdog_command() -> None:
    cmd = SetWatchdogCommand(enabled=True, timeout_seconds=60.0)
    assert cmd.enabled is True
    assert cmd.timeout_seconds == 60.0


def test_set_rtc_alarm_command_accepts_seconds_from_now() -> None:
    cmd = SetRtcAlarmCommand(seconds_from_now=300)
    assert cmd.seconds_from_now == 300


def test_disable_rtc_alarm_is_argless() -> None:
    cmd = DisableRtcAlarmCommand()
    assert cmd is not None  # frozen dataclass with no fields is valid


def test_sync_rtc_to_system_is_argless() -> None:
    cmd = SyncRtcToSystemCommand()
    assert cmd is not None


def test_sync_rtc_from_system_is_argless() -> None:
    cmd = SyncRtcFromSystemCommand()
    assert cmd is not None


def test_commands_are_frozen() -> None:
    cmd = ShutdownCommand(reason="x")
    try:
        cmd.reason = "y"  # type: ignore[misc]
    except Exception as exc:
        assert isinstance(exc, AttributeError) or "frozen" in str(exc).lower()
```

- [ ] **Step 4.2: Run the test to verify it fails**

Run:
```bash
uv run pytest tests/integrations/test_power_commands.py -v
```

Expected: `ModuleNotFoundError: No module named 'yoyopod.integrations.power.commands'`.

- [ ] **Step 4.3: Implement `src/yoyopod/integrations/power/commands.py`**

Create:

```python
"""Typed command dataclasses for the power integration.

See docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §7.3.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShutdownCommand:
    """Graceful shutdown request."""

    reason: str
    delay_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class RebootCommand:
    """Reboot request."""

    reason: str


@dataclass(frozen=True, slots=True)
class SetWatchdogCommand:
    """Enable/disable the PiSugar hardware watchdog; set the feed timeout."""

    enabled: bool
    timeout_seconds: float = 60.0


@dataclass(frozen=True, slots=True)
class SetRtcAlarmCommand:
    """Arm the PiSugar RTC wake-up alarm."""

    seconds_from_now: int


@dataclass(frozen=True, slots=True)
class DisableRtcAlarmCommand:
    """Clear any pending PiSugar RTC wake-up alarm."""


@dataclass(frozen=True, slots=True)
class SyncRtcToSystemCommand:
    """Copy system time into the PiSugar RTC."""


@dataclass(frozen=True, slots=True)
class SyncRtcFromSystemCommand:
    """Copy PiSugar RTC time into the system clock."""
```

- [ ] **Step 4.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/integrations/test_power_commands.py -v
```

Expected: all passing.

- [ ] **Step 4.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/integrations/power/commands.py tests/integrations/test_power_commands.py
uv run ruff check src/yoyopod/integrations/power/commands.py tests/integrations/test_power_commands.py
uv run mypy src/yoyopod/integrations/power/commands.py
```

Expected: all green.

- [ ] **Step 4.6: Commit**

Run:
```bash
git add src/yoyopod/integrations/power/commands.py tests/integrations/test_power_commands.py
git commit -m "$(cat <<'EOF'
feat(integrations/power): add typed command dataclasses

7 frozen dataclasses: Shutdown, Reboot, SetWatchdog, SetRtcAlarm,
DisableRtcAlarm, SyncRtcToSystem, SyncRtcFromSystem.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Write power handlers (state-update logic + low-battery policy) with TDD

**Files:**
- Create: `tests/integrations/test_power_handlers.py`
- Create: `src/yoyopod/integrations/power/handlers.py`

- [ ] **Step 5.1: Write the failing test**

Create `tests/integrations/test_power_handlers.py`:

```python
"""Tests for yoyopod.integrations.power.handlers."""

from __future__ import annotations

from dataclasses import dataclass

from yoyopod.core.events import ShutdownRequestedEvent
from yoyopod.core.testing import build_test_app
from yoyopod.integrations.power.handlers import (
    PowerPolicy,
    apply_snapshot_to_state,
)


@dataclass(frozen=True, slots=True)
class _BatteryStub:
    percent: int | None
    voltage_volts: float
    temperature_celsius: float
    charging: bool
    external_power: bool


@dataclass(frozen=True, slots=True)
class _DeviceStub:
    model: str


@dataclass(frozen=True, slots=True)
class _RtcStub:
    time: str | None = None
    alarm_enabled: bool = False
    alarm_time: str | None = None


@dataclass(frozen=True, slots=True)
class _SnapshotStub:
    available: bool
    battery: _BatteryStub
    device: _DeviceStub = _DeviceStub(model="pisugar3")
    rtc: _RtcStub = _RtcStub()
    error: str | None = None


def _mk_snapshot(
    *,
    available: bool = True,
    percent: int | None = 80,
    charging: bool = False,
    external_power: bool = False,
) -> _SnapshotStub:
    return _SnapshotStub(
        available=available,
        battery=_BatteryStub(
            percent=percent,
            voltage_volts=3.7,
            temperature_celsius=25.0,
            charging=charging,
            external_power=external_power,
        ),
    )


def test_apply_snapshot_populates_state_entities() -> None:
    app = build_test_app()

    apply_snapshot_to_state(app, _mk_snapshot(percent=72, charging=True))

    assert app.states.get_value("power.battery_percent") == 72
    assert app.states.get_value("power.charging") is True
    assert app.states.get_value("power.external_power") is False
    assert app.states.get_value("power.backend_available") is True
    assert app.states.get_value("power.voltage_volts") == 3.7
    assert app.states.get_value("power.temperature_celsius") == 25.0


def test_apply_snapshot_handles_unavailable_backend() -> None:
    app = build_test_app()

    apply_snapshot_to_state(app, _mk_snapshot(available=False, percent=None))

    assert app.states.get_value("power.backend_available") is False
    assert app.states.get_value("power.battery_percent") is None


def test_low_battery_policy_below_warning_threshold_noops() -> None:
    app = build_test_app()
    policy = PowerPolicy(
        warning_percent=20,
        critical_percent=5,
        shutdown_delay_seconds=30.0,
    )
    apply_snapshot_to_state(app, _mk_snapshot(percent=15, charging=False))
    app.drain()

    captured: list[ShutdownRequestedEvent] = []
    app.bus.subscribe(ShutdownRequestedEvent, lambda ev: captured.append(ev))

    policy.observe(app)
    app.drain()

    # 15% > 5% critical threshold, so no shutdown request — just a warning state.
    assert captured == []
    assert app.states.get_value("power.low_battery_warned") is True


def test_low_battery_policy_critical_threshold_emits_shutdown() -> None:
    app = build_test_app()
    policy = PowerPolicy(
        warning_percent=20,
        critical_percent=5,
        shutdown_delay_seconds=30.0,
    )
    apply_snapshot_to_state(app, _mk_snapshot(percent=3, charging=False))
    app.drain()

    captured: list[ShutdownRequestedEvent] = []
    app.bus.subscribe(ShutdownRequestedEvent, lambda ev: captured.append(ev))

    policy.observe(app)
    app.drain()

    assert len(captured) == 1
    assert captured[0].reason == "battery_critical"
    assert captured[0].delay_seconds == 30.0


def test_low_battery_policy_skips_when_charging() -> None:
    app = build_test_app()
    policy = PowerPolicy(warning_percent=20, critical_percent=5, shutdown_delay_seconds=30.0)
    apply_snapshot_to_state(app, _mk_snapshot(percent=3, charging=True))
    app.drain()

    captured: list[ShutdownRequestedEvent] = []
    app.bus.subscribe(ShutdownRequestedEvent, lambda ev: captured.append(ev))

    policy.observe(app)
    app.drain()

    assert captured == []


def test_low_battery_policy_fires_only_once_per_descent() -> None:
    app = build_test_app()
    policy = PowerPolicy(warning_percent=20, critical_percent=5, shutdown_delay_seconds=30.0)

    captured: list[ShutdownRequestedEvent] = []
    app.bus.subscribe(ShutdownRequestedEvent, lambda ev: captured.append(ev))

    apply_snapshot_to_state(app, _mk_snapshot(percent=3, charging=False))
    policy.observe(app)
    app.drain()
    policy.observe(app)  # called again with same snapshot
    app.drain()

    assert len(captured) == 1  # not duplicated


def test_low_battery_policy_rearms_after_recovery() -> None:
    app = build_test_app()
    policy = PowerPolicy(warning_percent=20, critical_percent=5, shutdown_delay_seconds=30.0)

    captured: list[ShutdownRequestedEvent] = []
    app.bus.subscribe(ShutdownRequestedEvent, lambda ev: captured.append(ev))

    apply_snapshot_to_state(app, _mk_snapshot(percent=3, charging=False))
    policy.observe(app)
    app.drain()
    assert len(captured) == 1

    # battery recovers (plug in charger)
    apply_snapshot_to_state(app, _mk_snapshot(percent=50, charging=True))
    policy.observe(app)
    app.drain()

    # drops again
    apply_snapshot_to_state(app, _mk_snapshot(percent=3, charging=False))
    policy.observe(app)
    app.drain()

    assert len(captured) == 2
```

- [ ] **Step 5.2: Run the test to verify it fails**

Run:
```bash
uv run pytest tests/integrations/test_power_handlers.py -v
```

Expected: `ModuleNotFoundError` on `yoyopod.integrations.power.handlers`.

- [ ] **Step 5.3: Implement `src/yoyopod/integrations/power/handlers.py`**

Create:

```python
"""State-update and policy logic for the power integration.

Converts backend snapshots into app.states entries. Emits ShutdownRequestedEvent
when battery crosses the critical threshold while not charging. See
docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §5, §9.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from yoyopod.core.events import ShutdownRequestedEvent


def apply_snapshot_to_state(app: Any, snapshot: Any) -> None:
    """Mirror a PowerSnapshot into the state store.

    `snapshot` must expose `.available`, `.battery.percent`, `.battery.voltage_volts`,
    `.battery.temperature_celsius`, `.battery.charging`, `.battery.external_power`.
    Duck-typed to allow the real PiSugar snapshot and test stubs.
    """
    battery = snapshot.battery
    app.states.set("power.backend_available", bool(snapshot.available))
    app.states.set("power.battery_percent", battery.percent)
    app.states.set("power.charging", bool(battery.charging))
    app.states.set("power.external_power", bool(battery.external_power))
    app.states.set("power.voltage_volts", float(battery.voltage_volts))
    app.states.set("power.temperature_celsius", float(battery.temperature_celsius))


@dataclass(slots=True)
class PowerPolicy:
    """Low-battery policy. Emits ShutdownRequestedEvent when battery is critical."""

    warning_percent: int
    critical_percent: int
    shutdown_delay_seconds: float

    _warning_latched: bool = False
    _critical_latched: bool = False

    def observe(self, app: Any) -> None:
        """Observe current power state. May publish ShutdownRequestedEvent."""
        percent = app.states.get_value("power.battery_percent")
        charging = app.states.get_value("power.charging") is True
        available = app.states.get_value("power.backend_available") is True

        if not available or percent is None:
            return

        # Re-arm the latches once charging resumes OR battery climbs back above threshold.
        if charging or percent > self.warning_percent:
            self._warning_latched = False
            self._critical_latched = False

        if charging:
            return

        if percent <= self.critical_percent and not self._critical_latched:
            self._critical_latched = True
            app.bus.publish(
                ShutdownRequestedEvent(
                    reason="battery_critical",
                    delay_seconds=self.shutdown_delay_seconds,
                )
            )
            return

        if percent <= self.warning_percent and not self._warning_latched:
            self._warning_latched = True
            app.states.set("power.low_battery_warned", True)
```

- [ ] **Step 5.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/integrations/test_power_handlers.py -v
```

Expected: all passing.

- [ ] **Step 5.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/integrations/power/handlers.py tests/integrations/test_power_handlers.py
uv run ruff check src/yoyopod/integrations/power/handlers.py tests/integrations/test_power_handlers.py
uv run mypy src/yoyopod/integrations/power/handlers.py
```

Expected: all green.

- [ ] **Step 5.6: Commit**

Run:
```bash
git add src/yoyopod/integrations/power/handlers.py tests/integrations/test_power_handlers.py
git commit -m "$(cat <<'EOF'
feat(integrations/power): add snapshot-to-state handler + low-battery policy

apply_snapshot_to_state writes 6 power.* entities from a snapshot.
PowerPolicy latches warning/critical thresholds and emits
ShutdownRequestedEvent at critical while not charging; re-arms on recovery.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Write the background poller with TDD

**Files:**
- Create: `tests/integrations/test_power_poller.py`
- Create: `src/yoyopod/integrations/power/poller.py`

- [ ] **Step 6.1: Write the failing test**

Create `tests/integrations/test_power_poller.py`:

```python
"""Tests for yoyopod.integrations.power.poller."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from yoyopod.core.testing import build_test_app
from yoyopod.integrations.power.poller import PowerPoller


@dataclass
class _FakeBackend:
    snapshots_yielded: int = 0

    def get_snapshot(self):
        self.snapshots_yielded += 1

        @dataclass(frozen=True, slots=True)
        class _B:
            percent: int = 80
            voltage_volts: float = 3.7
            temperature_celsius: float = 25.0
            charging: bool = False
            external_power: bool = False

        @dataclass(frozen=True, slots=True)
        class _D:
            model: str = "pisugar3"

        @dataclass(frozen=True, slots=True)
        class _R:
            time: str | None = None
            alarm_enabled: bool = False
            alarm_time: str | None = None

        @dataclass(frozen=True, slots=True)
        class _S:
            available: bool = True
            battery: _B = _B()
            device: _D = _D()
            rtc: _R = _R()
            error: str | None = None

        return _S()


def test_poller_schedules_state_update_on_main_thread_each_tick() -> None:
    app = build_test_app()
    backend = _FakeBackend()
    poller = PowerPoller(app=app, backend=backend, interval_seconds=0.05)

    poller.start()
    time.sleep(0.2)
    poller.stop()

    app.drain()

    assert backend.snapshots_yielded >= 2
    assert app.states.get_value("power.battery_percent") == 80


def test_poller_is_idempotent() -> None:
    app = build_test_app()
    backend = _FakeBackend()
    poller = PowerPoller(app=app, backend=backend, interval_seconds=0.05)

    poller.start()
    poller.start()  # second start is a no-op
    time.sleep(0.1)
    poller.stop()
    poller.stop()  # second stop is a no-op


def test_poller_thread_exits_promptly_on_stop() -> None:
    app = build_test_app()
    backend = _FakeBackend()
    poller = PowerPoller(app=app, backend=backend, interval_seconds=1.0)

    poller.start()
    start = time.monotonic()
    poller.stop()
    elapsed = time.monotonic() - start

    assert elapsed < 0.5  # stop() signals, thread exits near-immediately
```

- [ ] **Step 6.2: Run the test to verify it fails**

Run:
```bash
uv run pytest tests/integrations/test_power_poller.py -v
```

Expected: `ModuleNotFoundError` on `yoyopod.integrations.power.poller`.

- [ ] **Step 6.3: Implement `src/yoyopod/integrations/power/poller.py`**

Create:

```python
"""Background poller: reads the PiSugar backend and schedules state updates on main.

Owned by the power integration. See docs/superpowers/specs/
2026-04-21-phase-a-spine-rewrite-design.md §4.4 (scheduler), §5 (entities).
"""

from __future__ import annotations

import threading
from typing import Any

from loguru import logger

from yoyopod.integrations.power.handlers import apply_snapshot_to_state


class PowerPoller:
    """Dedicated worker thread that polls the power backend at a fixed interval."""

    def __init__(self, app: Any, backend: Any, interval_seconds: float = 10.0) -> None:
        self._app = app
        self._backend = backend
        self._interval = max(0.01, float(interval_seconds))
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        """Start the poller thread (idempotent)."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="power-poller",
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal the poller to stop and wait briefly for the thread to exit."""
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=1.0)
        self._thread = None

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                snapshot = self._backend.get_snapshot()
            except Exception as exc:
                logger.error("PowerPoller.get_snapshot failed: {}", exc)
                self._stop.wait(self._interval)
                continue

            self._app.scheduler.run_on_main(
                lambda s=snapshot: apply_snapshot_to_state(self._app, s)
            )
            self._stop.wait(self._interval)
```

- [ ] **Step 6.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/integrations/test_power_poller.py -v
```

Expected: all passing.

- [ ] **Step 6.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/integrations/power/poller.py tests/integrations/test_power_poller.py
uv run ruff check src/yoyopod/integrations/power/poller.py tests/integrations/test_power_poller.py
uv run mypy src/yoyopod/integrations/power/poller.py
```

Expected: all green.

- [ ] **Step 6.6: Commit**

Run:
```bash
git add src/yoyopod/integrations/power/poller.py tests/integrations/test_power_poller.py
git commit -m "$(cat <<'EOF'
feat(integrations/power): add background poller

Dedicated worker thread reads backend.get_snapshot() at fixed interval
and marshals apply_snapshot_to_state onto the main thread via the
scheduler. Idempotent start/stop; exits within 500 ms of stop().

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Write the power integration `setup()` / `teardown()` with TDD

**Files:**
- Create: `tests/integrations/test_power_integration.py`
- Modify: `src/yoyopod/integrations/power/__init__.py`

- [ ] **Step 7.1: Write the integration test**

Create `tests/integrations/test_power_integration.py`:

```python
"""End-to-end test for the power integration using a mock backend."""

from __future__ import annotations

import time
from dataclasses import dataclass

import pytest

from yoyopod.core.events import ShutdownRequestedEvent
from yoyopod.core.testing import build_test_app
from yoyopod.integrations.power import setup as setup_power, teardown as teardown_power
from yoyopod.integrations.power.commands import (
    RebootCommand,
    ShutdownCommand,
)


@dataclass
class _FakePiSugarBackend:
    percent: int = 80
    charging: bool = False
    shutdown_called: list[str] = None
    reboot_called: list[str] = None

    def __post_init__(self):
        self.shutdown_called = []
        self.reboot_called = []

    def get_snapshot(self):
        @dataclass(frozen=True, slots=True)
        class _B:
            percent: int
            voltage_volts: float = 3.7
            temperature_celsius: float = 25.0
            charging: bool = False
            external_power: bool = False

        @dataclass(frozen=True, slots=True)
        class _D:
            model: str = "pisugar3"

        @dataclass(frozen=True, slots=True)
        class _R:
            time: str | None = None
            alarm_enabled: bool = False
            alarm_time: str | None = None

        @dataclass(frozen=True, slots=True)
        class _S:
            available: bool
            battery: _B
            device: _D = _D()
            rtc: _R = _R()
            error: str | None = None

        return _S(
            available=True,
            battery=_B(percent=self.percent, charging=self.charging),
        )

    def shutdown(self, reason: str = "") -> None:
        self.shutdown_called.append(reason)

    def reboot(self, reason: str = "") -> None:
        self.reboot_called.append(reason)

    def close(self) -> None:
        pass


@pytest.fixture
def app_with_power():
    app = build_test_app()
    backend = _FakePiSugarBackend()
    app.config = type("Config", (), {
        "power": type("PC", (), {
            "poll_interval_seconds": 0.05,
            "low_battery_warning_percent": 20,
            "critical_shutdown_percent": 5,
            "shutdown_delay_seconds": 30.0,
        })(),
    })()
    app.register_integration(
        "power",
        setup=lambda a: setup_power(a, backend=backend),
        teardown=lambda a: teardown_power(a),
    )
    app.setup()
    yield app, backend
    app.stop()


def test_power_setup_registers_all_commands(app_with_power) -> None:
    app, _ = app_with_power
    pairs = set(app.services.registered())
    for expected in [
        ("power", "shutdown"),
        ("power", "reboot"),
        ("power", "set_watchdog"),
        ("power", "set_rtc_alarm"),
        ("power", "disable_rtc_alarm"),
        ("power", "sync_rtc_to_system"),
        ("power", "sync_rtc_from_system"),
    ]:
        assert expected in pairs


def test_power_poller_eventually_sets_state(app_with_power) -> None:
    app, backend = app_with_power
    time.sleep(0.2)
    app.drain()
    assert app.states.get_value("power.battery_percent") == 80


def test_shutdown_command_invokes_backend(app_with_power) -> None:
    app, backend = app_with_power
    app.services.call("power", "shutdown", ShutdownCommand(reason="manual"))
    assert backend.shutdown_called == ["manual"]


def test_reboot_command_invokes_backend(app_with_power) -> None:
    app, backend = app_with_power
    app.services.call("power", "reboot", RebootCommand(reason="update"))
    assert backend.reboot_called == ["update"]


def test_low_battery_policy_triggers_shutdown_request(app_with_power) -> None:
    app, backend = app_with_power
    captured: list[ShutdownRequestedEvent] = []
    app.bus.subscribe(ShutdownRequestedEvent, lambda ev: captured.append(ev))

    backend.percent = 2
    backend.charging = False
    time.sleep(0.2)  # let poller tick + policy observe
    app.drain()

    assert any(ev.reason == "battery_critical" for ev in captured)
```

- [ ] **Step 7.2: Run the test to verify it fails**

Run:
```bash
uv run pytest tests/integrations/test_power_integration.py -v
```

Expected: ImportError on `setup`/`teardown` from `yoyopod.integrations.power`.

- [ ] **Step 7.3: Implement `src/yoyopod/integrations/power/__init__.py`**

Replace the placeholder contents with:

```python
"""Power integration: battery, charging, RTC, watchdog, shutdown policy.

See docs/superpowers/specs/2026-04-21-phase-a-spine-rewrite-design.md §5, §7, §9.2.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from yoyopod.integrations.power.commands import (
    DisableRtcAlarmCommand,
    RebootCommand,
    SetRtcAlarmCommand,
    SetWatchdogCommand,
    ShutdownCommand,
    SyncRtcFromSystemCommand,
    SyncRtcToSystemCommand,
)
from yoyopod.integrations.power.handlers import PowerPolicy
from yoyopod.integrations.power.poller import PowerPoller


_STATE_KEY = "_power_integration"


def setup(app: Any, backend: Any | None = None) -> None:
    """Wire the power integration: construct backend, register commands, start poller."""
    if backend is None:
        from yoyopod.backends.power import PiSugarBackend
        backend = PiSugarBackend(app.config.power)

    power_cfg = app.config.power
    policy = PowerPolicy(
        warning_percent=int(power_cfg.low_battery_warning_percent),
        critical_percent=int(power_cfg.critical_shutdown_percent),
        shutdown_delay_seconds=float(power_cfg.shutdown_delay_seconds),
    )
    poller = PowerPoller(
        app=app,
        backend=backend,
        interval_seconds=float(power_cfg.poll_interval_seconds),
    )

    # Re-evaluate policy on every state change touching power entities.
    from yoyopod.core.events import StateChangedEvent

    def on_state_changed(ev: StateChangedEvent) -> None:
        if ev.entity.startswith("power."):
            policy.observe(app)

    app.bus.subscribe(StateChangedEvent, on_state_changed)

    # Commands.
    def handle_shutdown(cmd: ShutdownCommand) -> None:
        logger.info("Power.shutdown(reason={}, delay={}s)", cmd.reason, cmd.delay_seconds)
        backend.shutdown(reason=cmd.reason)

    def handle_reboot(cmd: RebootCommand) -> None:
        logger.info("Power.reboot(reason={})", cmd.reason)
        backend.reboot(reason=cmd.reason)

    def handle_set_watchdog(cmd: SetWatchdogCommand) -> None:
        logger.info("Power.set_watchdog(enabled={}, timeout={})", cmd.enabled, cmd.timeout_seconds)
        backend.set_watchdog(cmd.enabled, cmd.timeout_seconds)

    def handle_set_rtc_alarm(cmd: SetRtcAlarmCommand) -> None:
        backend.set_rtc_alarm(cmd.seconds_from_now)

    def handle_disable_rtc_alarm(_cmd: DisableRtcAlarmCommand) -> None:
        backend.disable_rtc_alarm()

    def handle_sync_rtc_to_system(_cmd: SyncRtcToSystemCommand) -> None:
        backend.sync_rtc_to_system()

    def handle_sync_rtc_from_system(_cmd: SyncRtcFromSystemCommand) -> None:
        backend.sync_rtc_from_system()

    app.services.register("power", "shutdown", handle_shutdown)
    app.services.register("power", "reboot", handle_reboot)
    app.services.register("power", "set_watchdog", handle_set_watchdog)
    app.services.register("power", "set_rtc_alarm", handle_set_rtc_alarm)
    app.services.register("power", "disable_rtc_alarm", handle_disable_rtc_alarm)
    app.services.register("power", "sync_rtc_to_system", handle_sync_rtc_to_system)
    app.services.register("power", "sync_rtc_from_system", handle_sync_rtc_from_system)

    # Start polling.
    poller.start()

    # Stash state for teardown.
    setattr(app, _STATE_KEY, {"backend": backend, "poller": poller, "policy": policy})


def teardown(app: Any) -> None:
    """Stop the poller and close the backend."""
    state = getattr(app, _STATE_KEY, None)
    if state is None:
        return
    try:
        state["poller"].stop()
    except Exception as exc:
        logger.error("PowerPoller.stop failed: {}", exc)
    try:
        state["backend"].close()
    except Exception as exc:
        logger.error("PiSugarBackend.close failed: {}", exc)
    delattr(app, _STATE_KEY)
```

- [ ] **Step 7.4: Run tests; all should pass**

Run:
```bash
uv run pytest tests/integrations/test_power_integration.py -v
```

Expected: all passing.

- [ ] **Step 7.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/integrations/power/__init__.py tests/integrations/test_power_integration.py
uv run ruff check src/yoyopod/integrations/power/__init__.py tests/integrations/test_power_integration.py
uv run mypy src/yoyopod/integrations/power/__init__.py
```

Expected: all green.

- [ ] **Step 7.6: Commit**

Run:
```bash
git add src/yoyopod/integrations/power/__init__.py tests/integrations/test_power_integration.py
git commit -m "$(cat <<'EOF'
feat(integrations/power): setup/teardown wiring, commands, policy loop

setup() constructs backend (or accepts an injected one for tests),
registers 7 typed commands, subscribes PowerPolicy to power.* state
changes, starts the background poller. teardown() stops the poller and
closes the backend.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Add `run()` loop to `YoyoPodApp` with TDD

**Files:**
- Modify: `src/yoyopod/core/app_shell.py`
- Modify: `tests/core/test_app_shell.py`

- [ ] **Step 8.1: Extend `test_app_shell.py` with run-loop tests**

Append the following to `tests/core/test_app_shell.py`:

```python


def test_run_loop_drains_scheduler_and_bus_per_tick() -> None:
    """run() iterates until stop() is called, draining scheduler+bus each tick."""
    import threading
    import time

    app = YoyoPodApp()
    tick_counts = {"count": 0}

    from yoyopod.core.events import LifecycleEvent

    def on_lifecycle(_ev):
        tick_counts["count"] += 1

    app.bus.subscribe(LifecycleEvent, on_lifecycle)

    def stop_soon():
        time.sleep(0.1)
        app.stop()

    t = threading.Thread(target=stop_soon, daemon=True)
    t.start()

    app.register_integration("dummy", setup=lambda _a: None)
    app.setup()
    app.run(tick_interval_seconds=0.01)

    # Setup fired 2 lifecycle events (start + complete) — at least those dispatched.
    assert tick_counts["count"] >= 2


def test_run_exits_cleanly_after_stop() -> None:
    """stop() called before run() exits immediately."""
    app = YoyoPodApp()
    app.stop()
    app.run(tick_interval_seconds=0.01)  # no-op; returns immediately
```

- [ ] **Step 8.2: Run the tests; both should fail**

Run:
```bash
uv run pytest tests/core/test_app_shell.py::test_run_loop_drains_scheduler_and_bus_per_tick tests/core/test_app_shell.py::test_run_exits_cleanly_after_stop -v
```

Expected: `AttributeError: 'YoyoPodApp' object has no attribute 'run'`.

- [ ] **Step 8.3: Implement `run()` in `src/yoyopod/core/app_shell.py`**

Edit `src/yoyopod/core/app_shell.py`. Add this method inside `YoyoPodApp`:

```python
    def run(self, tick_interval_seconds: float = 0.005) -> None:
        """Main loop: drain scheduler, drain bus, tick UI, sleep, repeat.

        UI tick is a placeholder in Phase A; the screen integration will
        register a callback that this loop invokes once per tick.
        """
        import time

        while not self._stopped:
            self.scheduler.drain()
            self.bus.drain()
            self._tick_ui()
            time.sleep(tick_interval_seconds)

    def _tick_ui(self) -> None:
        """Call the UI tick callback if one has been registered.

        The screen integration in a later plan sets app._ui_tick_callback to a
        function. Until then, _tick_ui is a no-op.
        """
        callback = getattr(self, "_ui_tick_callback", None)
        if callback is not None:
            try:
                callback()
            except Exception as exc:
                from loguru import logger

                logger.error("UI tick callback raised: {}", exc)
```

- [ ] **Step 8.4: Run the tests; both should pass**

Run:
```bash
uv run pytest tests/core/test_app_shell.py -v
```

Expected: all passing (including the two new run-loop tests).

- [ ] **Step 8.5: Format, lint, type-check**

Run:
```bash
uv run black src/yoyopod/core/app_shell.py tests/core/test_app_shell.py
uv run ruff check src/yoyopod/core/app_shell.py tests/core/test_app_shell.py
uv run mypy src/yoyopod/core/app_shell.py
```

Expected: all green.

- [ ] **Step 8.6: Commit**

Run:
```bash
git add src/yoyopod/core/app_shell.py tests/core/test_app_shell.py
git commit -m "$(cat <<'EOF'
feat(core): add YoyoPodApp.run() main loop

4-line loop: drain scheduler, drain bus, tick UI, sleep. Exits when
stop() is called. UI tick is a placeholder callback that the screen
integration will set in a later plan.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Retire the legacy `PowerManager`, `PowerRuntimeService`, `PowerCoordinator`

**Files:**
- Delete: `src/yoyopod/power/manager.py`
- Delete: `src/yoyopod/power/policies.py`
- Delete: `src/yoyopod/power/events.py`
- Delete: `src/yoyopod/power/__init__.py`
- Delete: `src/yoyopod/runtime/power.py` (PowerRuntimeService)
- Delete: `src/yoyopod/coordinators/power.py`

- [ ] **Step 9.1: Enumerate remaining consumers of the old power classes**

Run:
```bash
grep -rn "from yoyopod.power" src/ tests/
grep -rn "PowerManager\|PowerRuntimeService\|PowerCoordinator" src/ tests/
```

Expected: some hits inside `src/yoyopod/app.py`, `src/yoyopod/runtime/`, maybe `src/yoyopod/cli/`, and in tests (`test_app_orchestration.py`, `test_fsm_runtime.py` if they haven't been deleted yet).

Triage:
- Consumers inside `src/yoyopod/app.py` — that file is being rewritten in Plan 8, but for this plan it needs to compile. Stub out the power references with a comment `# TODO: removed in Phase A plan 2; wired via integrations/power/` and either delete the import or leave a minimal no-op shim.
- Consumers inside `src/yoyopod/runtime/power.py` — delete the file. If the `runtime/__init__.py` re-exports `PowerRuntimeService`, remove that re-export too.
- Tests that reference `PowerManager` or `PowerRuntimeService` and are already marked for deletion in the Phase A spec (e.g., `test_fsm_runtime.py`, `test_app_orchestration.py`): delete them if they exist.

- [ ] **Step 9.2: Delete the files**

Run:
```bash
git rm src/yoyopod/power/manager.py
git rm src/yoyopod/power/policies.py
git rm src/yoyopod/power/events.py
git rm src/yoyopod/power/__init__.py
git rm src/yoyopod/runtime/power.py
git rm src/yoyopod/coordinators/power.py
```

If any of these files no longer exist (already moved/removed), the `git rm` will error; skip those and continue.

- [ ] **Step 9.3: Remove power-related imports and instance variables from `src/yoyopod/app.py`**

Open `src/yoyopod/app.py`. Remove:
- `from yoyopod.power import (PowerManager, PowerRuntimeService)` (or similar)
- `self.power_manager: Optional[PowerManager] = None`
- `self.power_runtime = PowerRuntimeService(self)`
- Any `self.power_manager.*` calls — replace with comments `# power is now an integration; see integrations/power/`
- Any `self._poll_power_status(...)` compatibility wrappers — remove

Do not try to make `app.py` pretty — it is being fully rewritten in Plan 8.

- [ ] **Step 9.4: Remove power re-exports from `src/yoyopod/runtime/__init__.py`**

Open `src/yoyopod/runtime/__init__.py`. Remove any line that imports or re-exports `PowerRuntimeService`.

- [ ] **Step 9.5: Run the full test suite**

Run:
```bash
uv run pytest tests/ -q
```

Expected: all tests green. Tests that used to reference `PowerManager` or `PowerRuntimeService` must already be migrated (new power-integration tests under `tests/integrations/test_power*.py`) or deleted.

- [ ] **Step 9.6: Run the full CI gate**

Run:
```bash
uv run python scripts/quality.py ci
```

Expected: all green.

- [ ] **Step 9.7: Commit**

Run:
```bash
git add -A
git commit -m "$(cat <<'EOF'
refactor(power): delete PowerManager, PowerRuntimeService, PowerCoordinator

Power is now a pure integration under src/yoyopod/integrations/power/.
The legacy manager/runtime/coordinator triple is gone; app.py is stubbed
to compile (will be rewritten in Plan 8's final sweep).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Final verification

**Files:** none (verification only)

- [ ] **Step 10.1: Verify no legacy `PowerManager` references remain**

Run:
```bash
git grep -l "PowerManager\|PowerRuntimeService\|PowerCoordinator"
```

Expected: matches only in the Phase A spec and plan files under `docs/superpowers/` (they legitimately reference the old names to explain what was removed). Any match outside those paths is a bug to fix.

- [ ] **Step 10.2: Verify the integration shape**

Run:
```bash
ls src/yoyopod/integrations/power/
ls src/yoyopod/backends/power/
```

Expected:
- `integrations/power/`: `__init__.py`, `commands.py`, `handlers.py`, `poller.py` (no `events.py` yet; later plans add domain events when needed).
- `backends/power/`: `__init__.py`, `pisugar.py`, `watchdog.py`.

- [ ] **Step 10.3: Run the full CI gate**

Run:
```bash
uv run python scripts/quality.py ci
```

Expected: all green.

- [ ] **Step 10.4: Confirm branch history**

Run:
```bash
git log --oneline arch/phase-a-spine-rewrite ^main
```

Expected (newest first), appended to the 12 Plan-1 commits:
```
refactor(power): delete PowerManager, PowerRuntimeService, PowerCoordinator
feat(core): add YoyoPodApp.run() main loop
feat(integrations/power): setup/teardown wiring, commands, policy loop
feat(integrations/power): add background poller
feat(integrations/power): add snapshot-to-state handler + low-battery policy
feat(integrations/power): add typed command dataclasses
chore(integrations): scaffold integrations package + power placeholder
refactor(power): move PiSugar backend and watchdog under src/yoyopod/backends/power/
docs: renumber Phase C -> Phase B in Phase A spec
```

9 commits on top of Plan 1. The overall branch now has 21 commits.

- [ ] **Step 10.5: Confirm the power integration is registered in some wiring**

For Phase A Plan 2 the integration is registered by the test fixture only — the main `src/yoyopod/app.py` is still the legacy shell. This is expected; subsequent integrations join a real wiring point in `app.py` which is rewritten in Plan 8.

---

## Definition of Done

- `src/yoyopod/backends/power/` contains `pisugar.py` and `watchdog.py`, both moved from the legacy `src/yoyopod/power/` package.
- `src/yoyopod/integrations/power/` contains `__init__.py` (setup/teardown), `commands.py`, `handlers.py`, `poller.py`.
- `tests/integrations/test_power_commands.py`, `test_power_handlers.py`, `test_power_poller.py`, `test_power_integration.py` all passing.
- `core/app_shell.py` has `run()` and `_tick_ui()` methods.
- `PowerManager`, `PowerRuntimeService`, `PowerCoordinator` deleted; no references outside docs/.
- `uv run python scripts/quality.py ci` green.

---

## What's next (Plan 3)

The "easy batch" — four integrations that share patterns and don't cross-cut:
1. `network` — cellular registration, PPP, signal (no GPS)
2. `location` — GPS fix (split out of the legacy `network/gps.py`)
3. `contacts` — people directory, SIP→name lookup
4. `cloud` — MQTT telemetry, HTTPS sync, remote commands

Each follows the same template as the power pilot: backend under `backends/<name>/`, integration under `integrations/<name>/` with `setup(app)`, typed commands, state-mirroring handlers.

---

*End of implementation plan.*
