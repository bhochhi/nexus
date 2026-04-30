"""
Agent Discovery Service.

Centralized registry for agent instantiation factories.
"""
import logging
from typing import Dict, Any

from core.llm import LLMClient
from core.session import SessionState

logger = logging.getLogger(__name__)


class AgentDiscoveryService:
    def __init__(self):
        self.registry: Dict[str, Any] = {}

    def register_agents(self):
        """Register the factory functions for all agents."""
        try:
            from agents.live_agent.agent import LiveAgent
            self.registry["live_agent"] = lambda llm, session: LiveAgent(llm, session)
        except ImportError:
            logger.warning("live_agent module not available for delegation")
            
        try:
            from agents.auto_insurance_agent.agent import AutoInsuranceAgent
            self.registry["auto_insurance_agent"] = lambda llm, session: AutoInsuranceAgent(llm, session)
        except ImportError:
            logger.warning("auto_insurance_agent module not available for delegation")
            
        try:
            from agents.billing_agent.agent import BillingAgent
            self.registry["billing_agent"] = lambda llm, session: BillingAgent(llm, session)
        except ImportError:
            logger.warning("billing_agent module not available for delegation")

    def get_agent(self, agent_name: str, llm_client: LLMClient, session: SessionState):
        """Instantiate and return an agent."""
        if agent_name not in self.registry:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        # Instantiate the agent using the registered lambda factory
        return self.registry[agent_name](llm_client, session)
