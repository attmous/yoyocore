# Phase B — Plan B2: Input HAL Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move input adapters under `src/yoyopod/backends/input/`; create `src/yoyopod/integrations/input/` to own adapter selection, reader-thread lifecycle, and event publishing. Delete `src/yoyopod/ui/input/`.

**Architecture:** Input integration's `setup(app)` constructs the right adapter, starts its reader thread, maps low-level button events to typed domain events published via `scheduler.run_on_main(lambda: app.bus.publish(...))`. Also publishes `UserActivityEvent` for every input to drive screen wake.

**Tech Stack:** Python 3.12+, pytest, uv, existing GPIO reading (`gpiod` on Pi), `pynput` (dev keyboard).

**Spec reference:** `docs/superpowers/specs/2026-04-21-phase-b-hal-consolidation-design.md` §4.2, §5.

**Prerequisite:** Plan B1 executed.

## Current-main corrections

- The shared input surface currently lives in `src/yoyopod/ui/input/hal.py`, not `contracts.py`.
- The Whisplay adapter file is `src/yoyopod/ui/input/adapters/ptt_button.py`; there is also a `gpiod_buttons.py` helper that may move with it or remain as an implementation detail.

---

## File Structure

### Files to create

- `src/yoyopod/backends/input/__init__.py`
- `src/yoyopod/backends/input/api.py` — `InputBackend` protocol
- `src/yoyopod/backends/input/four_button.py` (moved)
- `src/yoyopod/backends/input/ptt.py` (moved from `src/yoyopod/ui/input/adapters/ptt_button.py`)
- `src/yoyopod/backends/input/keyboard.py` (moved)
- `src/yoyopod/integrations/input/__init__.py`
- `src/yoyopod/integrations/input/events.py`
- `src/yoyopod/integrations/input/commands.py`
- `tests/integrations/test_input.py`

### Files to delete

- `src/yoyopod/ui/input/` (entire directory)

---

## Task 1: Branch state verification

- [ ] **Step 1.1**

```bash
git log --oneline -10
ls src/yoyopod/backends/
ls src/yoyopod/integrations/
```

Expected: Plan B1 commits present; `backends/display/` populated; `integrations/display/` populated. On branch `arch/phase-b-hal-consolidation`.

---

## Task 2: Move input adapters

- [ ] **Step 2.1: Create directory and move adapters**

```bash
mkdir -p src/yoyopod/backends/input
git mv src/yoyopod/ui/input/adapters/four_button.py src/yoyopod/backends/input/four_button.py
git mv src/yoyopod/ui/input/adapters/ptt_button.py src/yoyopod/backends/input/ptt.py
git mv src/yoyopod/ui/input/adapters/keyboard.py src/yoyopod/backends/input/keyboard.py
```

- [ ] **Step 2.2: Move or fold the common interface**

The shared input contract currently lives in `src/yoyopod/ui/input/hal.py`; move or fold it:

```bash
git mv src/yoyopod/ui/input/hal.py src/yoyopod/backends/input/api.py
```

Inspect `api.py` — it should define an `InputBackend` protocol:

```python
class InputBackend(Protocol):
    """Common API for every input backend."""

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def set_event_callback(self, callback: Callable[[str], None]) -> None: ...
```

Where `callback` receives event names like `"select"`, `"up"`, `"down"`, `"back"`, `"ptt_held"`, `"ptt_released"`, etc. The exact vocabulary depends on the existing adapters — preserve it to avoid downstream churn.

- [ ] **Step 2.3: Create `src/yoyopod/backends/input/__init__.py`**

```python
"""Input backend adapters."""

from __future__ import annotations

from yoyopod.backends.input.api import InputBackend
from yoyopod.backends.input.four_button import FourButtonInputBackend
from yoyopod.backends.input.keyboard import KeyboardInputBackend
from yoyopod.backends.input.ptt import PttInputBackend

__all__ = [
    "InputBackend",
    "FourButtonInputBackend",
    "KeyboardInputBackend",
    "PttInputBackend",
]
```

- [ ] **Step 2.4: Rename classes to `*InputBackend`**

If existing classes are named `FourButtonAdapter` etc., rename to `FourButtonInputBackend` in place. Grep and rewrite:

```bash
grep -rn "FourButtonAdapter\|PttAdapter\|KeyboardAdapter" src/ tests/
```

- [ ] **Step 2.5: Delete `src/yoyopod/ui/input/factory.py` and `manager.py`**

```bash
git rm src/yoyopod/ui/input/factory.py
git rm src/yoyopod/ui/input/manager.py
```

Inspect and remove the `src/yoyopod/ui/input/` directory entirely:

```bash
git rm -r src/yoyopod/ui/input/
```

- [ ] **Step 2.6: Update imports everywhere**

```bash
grep -rn "from yoyopod.ui.input" src/ tests/
```

Rewrite to `from yoyopod.backends.input`.

- [ ] **Step 2.7: Commit**

```bash
git add -A
git commit -m "refactor(input): relocate adapters under backends/input/; delete ui/input/

FourButton, PTT, Keyboard backends now in backends/input/.
ui/input/factory.py and ui/input/manager.py deleted — selection
and reader-thread lifecycle move into the input integration.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Input integration events + commands

- [ ] **Step 3.1: Create `src/yoyopod/integrations/input/events.py`**

```python
"""Input domain events."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ButtonPressedEvent:
    """A button was pressed (short press)."""

    button: str  # "select", "up", "down", "back", etc.


@dataclass(frozen=True, slots=True)
class ButtonLongPressEvent:
    """A button was held for the long-press duration."""

    button: str


@dataclass(frozen=True, slots=True)
class PttHeldEvent:
    """Push-to-talk button is now held down."""


@dataclass(frozen=True, slots=True)
class PttReleasedEvent:
    """Push-to-talk button was released."""
```

- [ ] **Step 3.2: Create `src/yoyopod/integrations/input/commands.py`**

```python
"""Input integration commands."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulateButtonCommand:
    """Injects a synthetic button event — test-only helper."""

    button: str
```

---

## Task 4: Input integration setup

- [ ] **Step 4.1: Create `src/yoyopod/integrations/input/__init__.py`**

```python
"""Input integration: reader-thread lifecycle, event publishing."""

from __future__ import annotations

import os
from typing import Any

from loguru import logger

from yoyopod.core.events import UserActivityEvent
from yoyopod.integrations.input.commands import SimulateButtonCommand
from yoyopod.integrations.input.events import (
    ButtonLongPressEvent,
    ButtonPressedEvent,
    PttHeldEvent,
    PttReleasedEvent,
)


_STATE_KEY = "_input_integration"


def _select_backend_class():
    override = os.environ.get("YOYOPOD_INPUT", "").lower()
    if override == "four_button":
        from yoyopod.backends.input import FourButtonInputBackend
        return FourButtonInputBackend
    if override == "ptt":
        from yoyopod.backends.input import PttInputBackend
        return PttInputBackend
    if override == "keyboard":
        from yoyopod.backends.input import KeyboardInputBackend
        return KeyboardInputBackend
    return None


def setup(app: Any, backend: Any | None = None) -> None:
    if backend is None:
        cls = _select_backend_class()
        if cls is None:
            hardware = getattr(app.config, "device", None) or getattr(app.config, "hardware", None)
            name = getattr(hardware, "input", "keyboard") if hardware else "keyboard"
            from yoyopod.backends.input import (
                FourButtonInputBackend,
                KeyboardInputBackend,
                PttInputBackend,
            )
            cls = {
                "four_button": FourButtonInputBackend,
                "ptt": PttInputBackend,
                "keyboard": KeyboardInputBackend,
            }.get(name, KeyboardInputBackend)
        backend = cls(app.config)

    # Map low-level events to typed domain events.
    def on_event(event_name: str) -> None:
        def publish() -> None:
            if event_name == "ptt_held":
                app.bus.publish(PttHeldEvent())
            elif event_name == "ptt_released":
                app.bus.publish(PttReleasedEvent())
            elif event_name.endswith("_long"):
                app.bus.publish(ButtonLongPressEvent(button=event_name[:-5]))
            else:
                app.bus.publish(ButtonPressedEvent(button=event_name))
            app.bus.publish(UserActivityEvent(action_name=event_name))

        app.scheduler.run_on_main(publish)

    backend.set_event_callback(on_event)
    backend.start()

    # Command — test-only helper.
    def handle_simulate(cmd: SimulateButtonCommand) -> None:
        on_event(cmd.button)

    app.services.register("input", "simulate", handle_simulate)

    setattr(app, _STATE_KEY, {"backend": backend})


def teardown(app: Any) -> None:
    state = getattr(app, _STATE_KEY, None)
    if state is None:
        return
    try:
        state["backend"].stop()
    except Exception as exc:
        logger.error("Input.stop: {}", exc)
    delattr(app, _STATE_KEY)
```

- [ ] **Step 4.2: Register in `src/yoyopod/app.py` integration list**

Add `"yoyopod.integrations.input"` to `INTEGRATION_MODULES`, positioned before `screen` so `UserActivityEvent` reaches screen's subscription.

- [ ] **Step 4.3: Create `tests/integrations/test_input.py`**

```python
from dataclasses import dataclass, field
from typing import Callable

import pytest

from yoyopod.core.events import UserActivityEvent
from yoyopod.core.testing import build_test_app
from yoyopod.integrations.input import setup as setup_input, teardown as teardown_input
from yoyopod.integrations.input.commands import SimulateButtonCommand
from yoyopod.integrations.input.events import (
    ButtonLongPressEvent,
    ButtonPressedEvent,
    PttHeldEvent,
    PttReleasedEvent,
)


@dataclass
class _FakeInputBackend:
    callback: Callable[[str], None] | None = None
    started: bool = False
    stopped: bool = False

    def set_event_callback(self, cb):
        self.callback = cb

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


@pytest.fixture
def app_with_input():
    app = build_test_app()
    backend = _FakeInputBackend()
    app.register_integration(
        "input",
        setup=lambda a: setup_input(a, backend=backend),
        teardown=lambda a: teardown_input(a),
    )
    app.setup()
    yield app, backend
    app.stop()


def test_setup_starts_backend(app_with_input):
    _, backend = app_with_input
    assert backend.started is True


def test_button_event_publishes_button_pressed_and_user_activity(app_with_input):
    app, backend = app_with_input
    pressed: list[ButtonPressedEvent] = []
    activity: list[UserActivityEvent] = []
    app.bus.subscribe(ButtonPressedEvent, lambda ev: pressed.append(ev))
    app.bus.subscribe(UserActivityEvent, lambda ev: activity.append(ev))

    backend.callback("select")
    app.drain()

    assert pressed == [ButtonPressedEvent(button="select")]
    assert len(activity) == 1
    assert activity[0].action_name == "select"


def test_long_press_publishes_button_long_press(app_with_input):
    app, backend = app_with_input
    long_events: list[ButtonLongPressEvent] = []
    app.bus.subscribe(ButtonLongPressEvent, lambda ev: long_events.append(ev))

    backend.callback("select_long")
    app.drain()

    assert long_events == [ButtonLongPressEvent(button="select")]


def test_ptt_events(app_with_input):
    app, backend = app_with_input
    held: list[PttHeldEvent] = []
    released: list[PttReleasedEvent] = []
    app.bus.subscribe(PttHeldEvent, lambda ev: held.append(ev))
    app.bus.subscribe(PttReleasedEvent, lambda ev: released.append(ev))

    backend.callback("ptt_held")
    backend.callback("ptt_released")
    app.drain()

    assert len(held) == 1
    assert len(released) == 1


def test_simulate_command(app_with_input):
    app, _ = app_with_input
    pressed: list[ButtonPressedEvent] = []
    app.bus.subscribe(ButtonPressedEvent, lambda ev: pressed.append(ev))

    app.services.call("input", "simulate", SimulateButtonCommand(button="up"))
    app.drain()

    assert pressed == [ButtonPressedEvent(button="up")]


def test_teardown_stops_backend(app_with_input):
    app, backend = app_with_input
    app.stop()
    assert backend.stopped is True
```

- [ ] **Step 4.4: Run, commit**

```bash
uv run pytest tests/integrations/test_input.py -v
uv run black src/yoyopod/integrations/input/ tests/integrations/test_input.py
uv run ruff check src/yoyopod/integrations/input/ tests/integrations/test_input.py
uv run mypy src/yoyopod/integrations/input/
git add -A
git commit -m "feat(integrations/input): adapter selection + event publishing

setup() picks FourButton/PTT/Keyboard backend from env/config, starts
reader thread, maps events to ButtonPressed/ButtonLongPress/PttHeld/
PttReleased + publishes UserActivityEvent. Includes input.simulate
command for tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Update screens to subscribe to input events

Most screens in Phase A Plan 7 already subscribe through `self.app.bus.subscribe(...)` in their constructor. If any screen still references `self.input_manager.on_button(...)` or similar, update.

- [ ] **Step 5.1: Search for stragglers**

```bash
grep -rn "input_manager\|from yoyopod.ui.input" src/yoyopod/
```

Rewrite: screens subscribe to `ButtonPressedEvent` / `ButtonLongPressEvent` etc. from `yoyopod.integrations.input.events`.

- [ ] **Step 5.2: Commit**

```bash
git add -A
git commit -m "refactor(ui): screens subscribe to input events from integrations/input

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Validation

- [ ] **Step 6.1: CI gate**

```bash
uv run python scripts/quality.py ci
```

- [ ] **Step 6.2: Simulation smoke**

```bash
python yoyopod.py --simulate
```

Press keys; verify navigation works.

- [ ] **Step 6.3: Pi on-hardware**

```bash
yoyopod pi validate smoke
```

Press the real buttons / PTT. Verify events flow through to screens.

- [ ] **Step 6.4: No `ui/input` stragglers**

```bash
git grep -l "yoyopod.ui.input"
```

Expected: docs/ only.

---

## Task 7: Merge Phase B

- [ ] **Step 7.1: Rebase onto main**

```bash
git fetch origin
git rebase origin/main
```

- [ ] **Step 7.2: Push + PR**

```bash
git push -u origin arch/phase-b-hal-consolidation
gh pr create --title "Phase B: HAL consolidation (display + input backends+integrations)" --body "$(cat <<'EOF'
## Summary

Moves display and input HALs under the Phase A backends+integrations
pattern. LVGL binding relocated to backends/display/lvgl/, confined to
the Whisplay adapter. ui/display/ and ui/input/ deleted. Explicitly
skips the OVOS PHAL consolidation after evaluation (see spec §4.4).

## Test plan

- [ ] `uv run python scripts/quality.py ci` green
- [ ] `yoyopod pi validate smoke` green on Pimoroni + Whisplay
- [ ] `yoyopod pi validate lvgl-soak` green on Whisplay
- [ ] `python yoyopod.py --simulate` runs; home screen renders; keyboard nav works
- [ ] No raw LVGL imports outside backends/display/lvgl/ and backends/display/whisplay.py
- [ ] No yoyopod.ui.display or yoyopod.ui.input imports outside docs/

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 7.3: Merge when green**

```bash
gh pr merge --squash
```

---

## Definition of Done

- `src/yoyopod/backends/input/` and `src/yoyopod/integrations/input/` populated.
- `src/yoyopod/ui/input/` deleted.
- All adapters pass their tests; Pi validate smoke green on real hardware.
- Phase B spec marked `Status: Implemented`.
- Branch merged to main.

---

*End of implementation plan.*
