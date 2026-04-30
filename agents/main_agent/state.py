"""
Main Agent — LangGraph state schema.

Implements: blueprints/main_agent/graph.spec.md
"""
from typing import Any, Dict, List, Optional

from core.types import Message

from typing_extensions import TypedDict


class MainAgentState(TypedDict, total=False):
    """State schema for the Main Agent graph."""

    user_input: str                     # Current member message
    messages: List[Message]             # Provider-agnostic conversation messages
    system_prompt: str                  # Assembled system prompt
    tools: List                         # Available @tool objects
    response: str                       # Final response text
    reasoning: str                      # LLM reasoning for debug panel
    tool_call: Optional[Dict[str, Any]] # Pending tool call
    delegation_result: Optional[str]    # Response from delegated sub-agent
    delegated_to: Optional[str]         # The target agent that handled the turn
    delegation_occurred: bool           # Whether delegation happened
