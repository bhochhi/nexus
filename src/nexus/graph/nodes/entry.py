import logging

from nexus.graph.state import AgentState
from nexus.memory.store import SessionStore

logger = logging.getLogger(__name__)


def entry_node(state: AgentState, *, store: SessionStore) -> dict:
    """Load session and prepare context for the conversation."""
    user_id = state.get("user_id", "anonymous")
    session_id = state.get("session_id", "default")

    session = store.load(user_id, session_id)
    session.add_message("user", state["user_message"])

    return {
        "conversation_history": session.history,
        "preferences": session.preferences,
        "last_intent": session.last_intent,
        "error_count": 0,
        "should_escalate": False,
        "needs_clarification": False,
        "missing_slots": [],
    }
