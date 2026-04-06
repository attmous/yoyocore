"""Focused tests for the reworked Talk flow screens."""

from __future__ import annotations

import pytest

from yoyopy.app_context import AppContext
from yoyopy.config import Contact
from yoyopy.ui.display import Display
from yoyopy.ui.screens import CallScreen, NavigationRequest, TalkContactScreen, VoiceNoteScreen


class FakeConfigManager:
    """Minimal contact source for Talk tests."""

    def __init__(self, contacts: list[Contact]) -> None:
        self._contacts = contacts

    def get_contacts(self) -> list[Contact]:
        return list(self._contacts)


class FakeVoIPManager:
    """Minimal VoIP manager double for Talk actions."""

    def __init__(self, *, make_call_result: bool = True) -> None:
        self.make_call_result = make_call_result
        self.make_calls: list[tuple[str, str | None]] = []

    def make_call(self, sip_address: str, contact_name: str | None = None) -> bool:
        self.make_calls.append((sip_address, contact_name))
        return self.make_call_result


@pytest.fixture
def display() -> Display:
    """Create a simulation display and clean it up after the test."""

    test_display = Display(simulate=True)
    try:
        yield test_display
    finally:
        test_display.cleanup()


def test_call_screen_builds_people_deck_from_contacts(display: Display) -> None:
    """Talk should show one person at a time with favorites first and notes as labels."""

    contacts = [
        Contact(name="Bob", sip_address="sip:bob@example.com", favorite=False, notes="Dad"),
        Contact(name="Alice", sip_address="sip:alice@example.com", favorite=True, notes="Mama"),
        Contact(name="Carol", sip_address="sip:carol@example.com", favorite=True),
    ]
    screen = CallScreen(
        display,
        AppContext(),
        voip_manager=FakeVoIPManager(),
        config_manager=FakeConfigManager(contacts),
    )

    screen.enter()

    assert [person.title for person in screen.people] == ["Mama", "Carol", "Dad"]


def test_call_screen_select_opens_selected_contact(display: Display) -> None:
    """Selecting from Talk should store the contact and route to the action screen."""

    contacts = [Contact(name="Alice", sip_address="sip:alice@example.com", favorite=True, notes="Mama")]
    context = AppContext()
    screen = CallScreen(
        display,
        context,
        voip_manager=FakeVoIPManager(),
        config_manager=FakeConfigManager(contacts),
    )

    screen.enter()
    screen.on_select()

    assert context.talk_contact_name == "Mama"
    assert context.talk_contact_address == "sip:alice@example.com"
    assert screen.consume_navigation_request() == NavigationRequest.route("open_contact")


def test_talk_contact_screen_calls_selected_person(display: Display) -> None:
    """The contact action screen should call the selected person when Call is chosen."""

    context = AppContext()
    context.set_talk_contact(name="Mama", sip_address="sip:alice@example.com")
    voip_manager = FakeVoIPManager()
    screen = TalkContactScreen(display, context, voip_manager=voip_manager)

    screen.enter()
    screen.on_select()

    assert voip_manager.make_calls == [("sip:alice@example.com", "Mama")]
    assert screen.consume_navigation_request() == NavigationRequest.route("call_started")


def test_talk_contact_screen_routes_to_voice_note(display: Display) -> None:
    """The second action should open the voice-note flow for the selected contact."""

    context = AppContext()
    context.set_talk_contact(name="Mama", sip_address="sip:alice@example.com")
    screen = TalkContactScreen(display, context, voip_manager=FakeVoIPManager())

    screen.enter()
    screen.on_advance()
    screen.on_select()

    assert context.voice_note_recipient_name == "Mama"
    assert context.voice_note_recipient_address == "sip:alice@example.com"
    assert screen.consume_navigation_request() == NavigationRequest.route("voice_note")


def test_voice_note_screen_cycles_record_review_and_queue_states(display: Display) -> None:
    """Voice notes should move through record, review, and queued states."""

    context = AppContext()
    context.set_voice_note_recipient(name="Mama", sip_address="sip:alice@example.com")
    screen = VoiceNoteScreen(display, context)

    screen.enter()
    assert screen.current_view_model()[0] == "Voice Note"

    screen.on_select()
    assert screen.current_view_model()[0] == "Recording"

    screen.on_select()
    assert screen.current_view_model()[0] == "Send"

    screen.on_select()
    assert screen.current_view_model()[0] == "Queued"
