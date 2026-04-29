"""
Nexus — Shared types, enums, and data contracts.

All data models used across the platform. This module has zero external
dependencies (stdlib only).

Implements: blueprints/core/types.spec.md
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """A single conversation turn."""
    role: str               # "user" | "assistant" | "system" | "tool"
    content: str
    agent: str = ""         # Which agent produced this message
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Skill:
    """A capability advertised by an agent in its agent.md."""
    name: str               # e.g., "connect_to_live_agent"
    description: str        # e.g., "Connect member to a human representative"


@dataclass
class AgentCapability:
    """Full capability manifest for a discovered agent."""
    name: str               # e.g., "live_agent"
    display_name: str       # e.g., "Live Agent Support"
    description: str        # What this agent does
    skills: List[Skill] = field(default_factory=list)
    version: str = "1.0.0"
    status: str = "active"  # "active" | "beta" | "disabled"
    module_path: str = ""   # Filesystem path to the agent module


@dataclass
class ToolCall:
    """A tool invocation requested by the LLM."""
    name: str                       # Tool function name
    arguments: Dict[str, Any] = field(default_factory=dict)
    tool_use_id: str = ""           # Unique ID for this tool invocation


@dataclass
class LLMResponse:
    """Response from an LLM invocation."""
    text: str = ""                          # LLM's text response
    tool_call: Optional[ToolCall] = None    # Tool call request (if any)
    reasoning: str = ""                     # LLM's reasoning (for debug panel)
    raw_response: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DelegationRequest:
    """Sent from orchestrator to sub-agent when delegating."""
    source_agent: str
    target_agent: str
    user_input: str
    summary: str
    session_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DelegationResponse:
    """Returned from sub-agent to orchestrator."""
    agent_name: str
    response: str
    status: str = "complete"    # "complete" | "in_progress" | "needs_input" | "error"
    summary: str = ""
    session_updates: Dict[str, Any] = field(default_factory=dict)
    return_to_orchestrator: bool = True


@dataclass
class AgentResult:
    """Returned from any agent invocation to the app.py REPL loop."""
    response: str
    active_agent: str = ""
    llm_reasoning: str = ""
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    delegation_occurred: bool = False
