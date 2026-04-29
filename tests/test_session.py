"""
Tests for core/session.py

Acceptance criteria from blueprints/core/session.spec.md
Feature: F-001 (Member Greeting & Session Management)
"""
import uuid

from core.session import AgentState, SessionManager, SessionState
from core.types import Message


class TestSessionManager:
    def test_new_member_gets_new_session(self):
        mgr = SessionManager()
        session = mgr.get_or_create("M123")
        assert session.is_new_session is True
        assert session.member_id == "M123"
        assert session.current_agent == "main_agent"

    def test_session_id_is_valid_uuid(self):
        mgr = SessionManager()
        session = mgr.get_or_create("M123")
        # Should not raise
        uuid.UUID(session.session_id, version=4)

    def test_returning_member_gets_same_session(self):
        mgr = SessionManager()
        s1 = mgr.get_or_create("M123")
        s2 = mgr.get_or_create("M123")
        assert s2.is_new_session is False
        assert s1.session_id == s2.session_id

    def test_different_members_get_different_sessions(self):
        mgr = SessionManager()
        s1 = mgr.get_or_create("M123")
        s2 = mgr.get_or_create("M456")
        assert s1.session_id != s2.session_id
        assert s1.member_id == "M123"
        assert s2.member_id == "M456"

    def test_agent_states_empty_on_new_session(self):
        mgr = SessionManager()
        session = mgr.get_or_create("M123")
        assert session.agent_states == {}

    def test_get_by_session_id(self):
        mgr = SessionManager()
        s1 = mgr.get_or_create("M123")
        found = mgr.get(s1.session_id)
        assert found is not None
        assert found.session_id == s1.session_id

    def test_get_nonexistent_returns_none(self):
        mgr = SessionManager()
        assert mgr.get("nonexistent-id") is None

    def test_update_refreshes_last_active(self):
        mgr = SessionManager()
        session = mgr.get_or_create("M123")
        old_time = session.last_active
        import time
        time.sleep(0.01)
        mgr.update(session)
        assert session.last_active >= old_time


class TestSessionState:
    def test_get_agent_state_auto_creates(self):
        session = SessionState(session_id="test", member_id="M123")
        state = session.get_agent_state("main_agent")
        assert isinstance(state, AgentState)
        assert state.conversation_history == []
        assert state.delegation_summary is None
        # Should be stored
        assert "main_agent" in session.agent_states

    def test_get_agent_state_returns_existing(self):
        session = SessionState(session_id="test", member_id="M123")
        s1 = session.get_agent_state("main_agent")
        s1.data["key"] = "value"
        s2 = session.get_agent_state("main_agent")
        assert s2.data["key"] == "value"

    def test_add_message_to_correct_agent(self):
        session = SessionState(session_id="test", member_id="M123")
        msg1 = Message(role="user", content="hello", agent="main_agent")
        msg2 = Message(role="user", content="connect me", agent="live_agent")

        session.add_message("main_agent", msg1)
        session.add_message("live_agent", msg2)

        assert len(session.get_agent_state("main_agent").conversation_history) == 1
        assert len(session.get_agent_state("live_agent").conversation_history) == 1
        assert session.get_agent_state("main_agent").conversation_history[0].content == "hello"

    def test_set_delegation_summary(self):
        session = SessionState(session_id="test", member_id="M123")
        session.set_delegation_summary("live_agent", "Member wants banking help.")
        assert session.get_agent_state("live_agent").delegation_summary == "Member wants banking help."

    def test_agent_histories_are_isolated(self):
        session = SessionState(session_id="test", member_id="M123")
        session.add_message("main_agent", Message(role="user", content="a"))
        session.add_message("main_agent", Message(role="user", content="b"))
        session.add_message("live_agent", Message(role="user", content="c"))

        assert len(session.get_agent_state("main_agent").conversation_history) == 2
        assert len(session.get_agent_state("live_agent").conversation_history) == 1
