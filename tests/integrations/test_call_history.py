"""Focused tests for the Talk call-history persistence layer."""

from __future__ import annotations

from pathlib import Path

from yoyopod.integrations.call import (
    CallHistoryEntry,
    CallHistoryStore,
    CallSessionTracker,
    CallState,
)


def test_call_history_store_persists_and_restores_entries(tmp_path: Path) -> None:
    """Call history should survive a save/load round-trip."""

    history_file = tmp_path / "call_history.json"
    store = CallHistoryStore(history_file)
    store.add_entry(
        CallHistoryEntry.create(
            direction="incoming",
            display_name="Hagar",
            sip_address="sip:hagar@example.com",
            outcome="missed",
        )
    )

    reloaded = CallHistoryStore(history_file)
    recent = reloaded.list_recent()

    assert len(recent) == 1
    assert recent[0].display_name == "Hagar"
    assert recent[0].outcome == "missed"
    assert reloaded.missed_count() == 1


def test_call_history_store_marks_missed_calls_seen(tmp_path: Path) -> None:
    """Opening recents should clear the unseen missed-call badge count."""

    history_file = tmp_path / "call_history.json"
    store = CallHistoryStore(history_file)
    store.add_entry(
        CallHistoryEntry.create(
            direction="incoming",
            display_name="Mama",
            sip_address="sip:mama@example.com",
            outcome="missed",
        )
    )

    assert store.missed_count() == 1
    store.mark_all_seen()

    assert store.missed_count() == 0
    assert store.list_recent()[0].seen is True


def test_call_session_tracker_classifies_terminal_outcomes(tmp_path: Path) -> None:
    """Session tracking should persist call outcomes using the canonical rules."""

    history_file = tmp_path / "call_history.json"
    store = CallHistoryStore(history_file)
    tracker = CallSessionTracker(store)

    tracker.begin_incoming_call("sip:mama@example.com", "Mama")
    tracker.mark_terminal_state(CallState.END, local_end_action="reject")
    tracker.finalize()

    tracker.ensure_outgoing_call(
        {"address": "sip:dad@example.com", "display_name": "Dad"},
    )
    tracker.mark_terminal_state(CallState.ERROR)
    tracker.finalize()

    tracker.ensure_outgoing_call(
        {"address": "sip:friend@example.com", "display_name": "Friend"},
    )
    tracker.mark_answered()
    tracker.mark_terminal_state(CallState.RELEASED)
    tracker.finalize(call_duration_seconds=42)

    recent = store.list_recent(3)

    assert recent[0].outcome == "completed"
    assert recent[0].duration_seconds == 42
    assert recent[1].outcome == "failed"
    assert recent[2].outcome == "rejected"


def test_call_session_tracker_keeps_pending_incoming_metadata_until_cleared() -> None:
    """Incoming caller metadata should stay available until the UI dismisses it."""

    tracker = CallSessionTracker()

    tracker.begin_incoming_call("sip:mama@example.com", "Mama")
    assert tracker.pending_incoming_call == ("sip:mama@example.com", "Mama")

    tracker.clear_pending_incoming_call()
    assert tracker.pending_incoming_call is None
