"""
Nexus — Session management with per-agent isolated state.

Each member has a unique session. Each agent maintains its own conversation
history within the session. Agents share context via session.context but
never read each other's conversation history.

Implements: blueprints/core/session.spec.md
Features: F-001 (Member Greeting & Session Management)
"""
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.types import Message, AgentResult

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """Per-agent isolated state bucket."""
    conversation_history: List[Message] = field(default_factory=list)
    delegation_summary: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    results: List[AgentResult] = field(default_factory=list)


@dataclass
class SessionState:
    """The shared session object — unique per member."""
    session_id: str = ""
    member_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_new_session: bool = True
    current_agent: str = "main_agent"
    agent_states: Dict[str, AgentState] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_agent_state(self, agent_name: str) -> AgentState:
        """Get or create the AgentState for the given agent."""
        if agent_name not in self.agent_states:
            self.agent_states[agent_name] = AgentState()
        return self.agent_states[agent_name]

    def add_message(self, agent_name: str, message: Message) -> None:
        """Append a message to the specified agent's conversation history."""
        state = self.get_agent_state(agent_name)
        state.conversation_history.append(message)

    def set_delegation_summary(self, agent_name: str, summary: str) -> None:
        """Set the delegation summary on the specified agent's state."""
        state = self.get_agent_state(agent_name)
        state.delegation_summary = summary


class SessionManager:
    """In-memory session store keyed by member_id."""

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def get_or_create(self, member_id: str) -> SessionState:
        """Get existing session or create a new one for the member."""
        now = datetime.now(timezone.utc)

        if member_id in self._sessions:
            session = self._sessions[member_id]
            session.is_new_session = False
            session.last_active = now
            logger.info(f"Returning session {session.session_id} for member {member_id}")
            return session

        session = SessionState(
            session_id=str(uuid.uuid4()),
            member_id=member_id,
            created_at=now,
            last_active=now,
            is_new_session=True,
            current_agent="main_agent",
        )
        self._sessions[member_id] = session
        logger.info(f"Created new session {session.session_id} for member {member_id}")
        return session

    def update(self, session: SessionState) -> None:
        """Persist the updated session state."""
        session.last_active = datetime.now(timezone.utc)
        self._sessions[session.member_id] = session

    def get(self, session_id: str) -> Optional[SessionState]:
        """Retrieve session by session_id."""
        for session in self._sessions.values():
            if session.session_id == session_id:
                return session
        return None
