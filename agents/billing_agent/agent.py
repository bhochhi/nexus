"""
Billing Agent — Nexus Agent.

Handles member billing inquiries, retrieves payment details, schedules payments, and answers standard FAQs

Implements: blueprints/billing_agent/
"""
import logging
from typing import List

from core.base_agent import BaseAgent
from core.llm import LLMClient
from core.session import SessionState

from .tools import TOOLS

logger = logging.getLogger(__name__)


class BillingAgent(BaseAgent):
    """Billing Agent agent."""

    def __init__(self, llm_client: LLMClient, session: SessionState):
        super().__init__("billing_agent", llm_client, session)

    def build_graph(self):
        """Billing Agent graph — minimal for now."""
        return None

    def get_tools(self) -> List:
        """Billing Agent tools."""
        return TOOLS

    def get_system_prompt(self, additional_context: str = "") -> str:
        member_id = "12345" # Hardcoded for POC based on mock service
        context = f"The current member ID is: {member_id}"
        if additional_context:
            context += f"\n{additional_context}"
        return super().get_system_prompt(context)
