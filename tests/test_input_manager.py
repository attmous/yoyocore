"""Tests for input-manager activity callbacks."""

from __future__ import annotations

from yoyopy.ui.input import InputAction, InputManager


def test_input_manager_notifies_activity_callbacks_for_each_action() -> None:
    """Every semantic action should also trigger registered activity listeners."""

    manager = InputManager()
    events: list[tuple[str, object | None]] = []

    manager.on_activity(lambda action, data: events.append((action.value, data)))

    manager.simulate_action(InputAction.SELECT, {"source": "test"})
    manager.simulate_action(InputAction.BACK)

    assert events == [
        ("select", {"source": "test"}),
        ("back", None),
    ]
