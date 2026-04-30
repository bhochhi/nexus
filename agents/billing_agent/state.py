"""
Billing Agent — Agent-specific LangGraph state schema.

Extends the base AgentGraphState with fields specific to this agent.
"""
from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class BillingAgentState(TypedDict):
    """State schema for the Billing Agent graph."""

    messages: List[Dict[str, Any]]      # Conversation messages
    system_prompt: str                   # Assembled system prompt
    tools: List                          # Available tools
    response: str                        # Final response text
    reasoning: str                       # LLM reasoning for debug
    # TODO: Add agent-specific state fields below
