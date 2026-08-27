from datetime import datetime, timedelta, timezone

from member_assistant.models import new_conversation_state
from member_assistant.events import AssistantEvent
from member_assistant.state_store import SQLiteConversationStore


class _Clock:
    def __init__(self):
        self.value = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += timedelta(seconds=seconds)


def test_expired_conversation_is_deleted_but_audit_history_is_retained(tmp_path):
    clock = _Clock()
    store = SQLiteConversationStore(
        tmp_path / "ttl.db", session_ttl_seconds=600, clock=clock
    )
    try:
        state = new_conversation_state()
        state["turn_count"] = 3
        store.save("member-session", state)
        store.append_audit("member-session", "turn_completed", {"turn": 3})

        clock.advance(601)

        assert store.cleanup_expired() == 1
        assert store.load("member-session")["turn_count"] == 0
        assert store.audit_events("member-session")[0]["event_type"] == "turn_completed"
    finally:
        store.close()


def test_zero_ttl_disables_expiration(tmp_path):
    clock = _Clock()
    store = SQLiteConversationStore(
        tmp_path / "no-ttl.db", session_ttl_seconds=0, clock=clock
    )
    try:
        state = new_conversation_state()
        state["turn_count"] = 2
        store.save("persistent-session", state)

        clock.advance(3600)

        assert store.cleanup_expired() == 0
        assert store.load("persistent-session")["turn_count"] == 2
    finally:
        store.close()


def test_expired_sessions_are_cleaned_when_store_restarts(tmp_path):
    clock = _Clock()
    path = tmp_path / "restart-ttl.db"
    first = SQLiteConversationStore(path, session_ttl_seconds=600, clock=clock)
    state = new_conversation_state()
    state["turn_count"] = 1
    first.save("old-session", state)
    first.close()

    clock.advance(601)
    second = SQLiteConversationStore(path, session_ttl_seconds=600, clock=clock)
    try:
        assert second.load("old-session")["turn_count"] == 0
    finally:
        second.close()


def test_expiration_removes_replay_events_but_retains_audit_history(tmp_path):
    clock = _Clock()
    store = SQLiteConversationStore(
        tmp_path / "event-ttl.db", session_ttl_seconds=600, clock=clock
    )
    try:
        state = new_conversation_state()
        store.save("event-session", state)
        store.begin_turn("event-session", "message-1", "turn-1", "hello")
        store.append_event(
            AssistantEvent.create(
                session_id="event-session",
                turn_id="turn-1",
                sequence=1,
                event_type="turn.accepted",
            )
        )
        store.append_audit("event-session", "turn_started", {"turn": 1})

        clock.advance(601)
        assert store.cleanup_expired() == 1

        assert store.stream_events("event-session") == []
        assert store.audit_events("event-session")[0]["event_type"] == "turn_started"
    finally:
        store.close()
