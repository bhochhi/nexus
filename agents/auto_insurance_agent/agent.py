"""
Auto-Insurance Agent.

Implements: blueprints/auto_insurance_agent/agent.spec.md
"""
import logging
from typing import List

from core.base_agent import BaseAgent
from core.llm import LLMClient
from core.session import SessionState

from .tools import TOOLS

logger = logging.getLogger(__name__)


class AutoInsuranceAgent(BaseAgent):
    """Auto Insurance Support agent."""

    def __init__(self, llm_client: LLMClient, session: SessionState):
        super().__init__("auto_insurance_agent", llm_client, session)

    def build_graph(self):
        """Simple agent; doesn't use a complex graph."""
        return None

    def get_tools(self) -> List:
        return TOOLS

    def get_system_prompt(self, additional_context: str = "") -> str:
        context = f"The current member ID is: {self.session.member_id}"
        if additional_context:
            context += f"\n{additional_context}"
        return super().get_system_prompt(context)
