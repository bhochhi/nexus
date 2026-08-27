"""Agentic Member Assistant proof of concept."""

from typing import Any

__all__ = ["AgentRuntime", "AssistantEvent", "AssistantReply"]


def __getattr__(name: str) -> Any:
    """Avoid importing LangGraph when a lightweight utility module is used."""

    if name == "AssistantEvent":
        from .events import AssistantEvent

        return AssistantEvent
    if name in {"AgentRuntime", "AssistantReply"}:
        from .runtime import AgentRuntime, AssistantReply

        return {"AgentRuntime": AgentRuntime, "AssistantReply": AssistantReply}[name]
    raise AttributeError(name)
