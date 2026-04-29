"""
Live Agent Support — Nexus Agent.

Connects members to live human agents in Banking, Insurance, or Investment Advice queues via real-time chat.

Implements: blueprints/live_agent/
"""
import logging
from typing import List

from core.base_agent import BaseAgent
from core.llm import LLMClient
from core.session import SessionState

logger = logging.getLogger(__name__)


class LiveAgent(BaseAgent):
    """Live Agent Support agent."""

    def __init__(self, llm_client: LLMClient, session: SessionState):
        super().__init__("live_agent", llm_client, session)

    def build_graph(self):
        """Live Agent Support graph — minimal for now.

        TODO: Replace with LangGraph StateGraph when implementing.
        """
        return None

    def get_tools(self) -> List:
        """Live Agent Support tools.

        TODO: Add @tool-decorated functions.
        """
        return []
