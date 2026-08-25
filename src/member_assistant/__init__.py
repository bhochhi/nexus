"""Agentic Member Assistant proof of concept."""

from typing import Any

__all__ = ["AgentRuntime", "AssistantReply"]


def __getattr__(name: str) -> Any:
    """Avoid importing LangGraph when a lightweight utility module is used."""

    if name in __all__:
        from .runtime import AgentRuntime, AssistantReply

        return {"AgentRuntime": AgentRuntime, "AssistantReply": AssistantReply}[name]
    raise AttributeError(name)
