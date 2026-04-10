import logging

from nexus.graph.state import AgentState

logger = logging.getLogger(__name__)


def escalation_node(state: AgentState) -> dict:
    """Handle escalation to a human agent."""
    response = (
        "I'd like to connect you with a human agent who can better assist you. "
        "Let me transfer you now. Your estimated wait time is under 2 minutes."
    )

    return {
        "response_text": response,
        "tool_name": "",
        "tool_args": {},
    }
