from __future__ import annotations

from yoyopod_cli import _pi_validate_helpers as helpers


def test_wait_for_route_accepts_transition_completed_in_final_pump(
    monkeypatch,
) -> None:
    state = {"now": 0.0, "route": "hub"}

    def fake_monotonic() -> float:
        return float(state["now"])

    def fake_current_route(_app: object) -> str:
        return str(state["route"])

    def fake_pump_app(_app: object, duration_seconds: float) -> None:
        assert duration_seconds == 0.05
        state["route"] = "ask"
        state["now"] = 1.2

    monkeypatch.setattr(helpers.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(helpers, "_current_route", fake_current_route)
    monkeypatch.setattr(helpers, "_pump_app", fake_pump_app)

    helpers._wait_for_route(object(), "ask", timeout_seconds=1.0)
