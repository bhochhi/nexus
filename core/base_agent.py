"""
Nexus — Abstract base agent.

All agents extend BaseAgent. Provides: spec file loading (persona.md,
instruction.md), system prompt assembly, LangGraph pattern, and the
invoke interface.

Implements: blueprints/core/base_agent.spec.md
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from core.llm import LLMClient
from core.session import SessionState
from core.types import AgentResult, Message

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all Nexus agents."""

    def __init__(self, agent_name: str, llm_client: LLMClient, session: SessionState):
        self.agent_name = agent_name
        self.llm = llm_client
        self.session = session

        # Determine agent module directory
        self.module_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "agents",
            agent_name,
        )

        # Load spec files
        self.persona = self._load_md("persona.md")
        self.instructions = self._load_md("instruction.md")

        # Initialize tools and graph
        self.tools = self.get_tools()
        self.graph = self.build_graph()

    def _load_md(self, filename: str) -> str:
        """Read a markdown file from the agent's module directory."""
        filepath = os.path.join(self.module_dir, filename)
        try:
            with open(filepath, "r") as f:
                return f.read()
        except (IOError, OSError):
            logger.debug(f"Optional file not found: {filepath}")
            return ""

    def get_system_prompt(self, additional_context: str = "") -> str:
        """Combine persona + instructions + context into a single system prompt."""
        parts = []

        if self.persona:
            parts.append(f"## Persona\n{self.persona}")
        if self.instructions:
            parts.append(f"## Instructions\n{self.instructions}")
        if additional_context:
            parts.append(f"## Context\n{additional_context}")

        return "\n\n".join(parts)

    @abstractmethod
    def build_graph(self):
        """Each agent defines its own LangGraph StateGraph."""
        ...

    @abstractmethod
    def get_tools(self) -> List:
        """Each agent returns its list of tools."""
        ...

    def invoke(self, user_input: str) -> AgentResult:
        """Process user input and return a result.

        1. Add user message to this agent's conversation history
        2. Build system prompt with delegation context
        3. Call LLM
        4. Add assistant response to history
        5. Return AgentResult
        """
        # Add user message to this agent's history
        user_msg = Message(role="user", content=user_input, agent=self.agent_name)
        self.session.add_message(self.agent_name, user_msg)

        # Build system prompt with delegation context
        delegation_context = self._get_delegation_context()
        system_prompt = self.get_system_prompt(delegation_context)

        # Get conversation messages for this agent
        messages = self._get_conversation_messages()

        # Call LLM
        if self.tools:
            response = self.llm.invoke_with_tools(messages, system_prompt, self.tools)
        else:
            response = self.llm.invoke(messages, system_prompt)

        # Add assistant response to this agent's history
        assistant_msg = Message(
            role="assistant",
            content=response.text,
            agent=self.agent_name,
            metadata={"reasoning": response.reasoning},
        )
        self.session.add_message(self.agent_name, assistant_msg)

        # Build state snapshot for debug panel
        state_snapshot = {
            "current_agent": self.session.current_agent,
            "context": self.session.context,
        }

        return AgentResult(
            response=response.text,
            active_agent=self.agent_name,
            llm_reasoning=response.reasoning,
            state_snapshot=state_snapshot,
        )

    def _get_conversation_messages(self) -> List[Message]:
        """Retrieve this agent's conversation history from session."""
        agent_state = self.session.get_agent_state(self.agent_name)
        return agent_state.conversation_history

    def _get_delegation_context(self) -> str:
        """Get delegation summary context if present."""
        agent_state = self.session.get_agent_state(self.agent_name)
        if agent_state.delegation_summary:
            return f"Previous agent summary: {agent_state.delegation_summary}"
        return ""
