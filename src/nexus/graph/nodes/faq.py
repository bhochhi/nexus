import logging

from nexus.graph.state import AgentState
from nexus.llm.base import BaseLLM

logger = logging.getLogger(__name__)


def faq_node(state: AgentState, *, llm: BaseLLM) -> dict:
    """Handle FAQ intents."""
    return {
        "tool_name": "answer_faq",
        "tool_args": {"question": state["user_message"]},
    }
