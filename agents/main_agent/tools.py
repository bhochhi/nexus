"""
Main Agent — Tool definitions.

Tools the LLM can call: delegate_to_agent (routing) and show_capabilities (inquiry).
Tool schemas are auto-generated from type hints and docstrings.

Implements: blueprints/main_agent/tools.spec.md
"""
from typing import List

from langchain_core.tools import tool

from core.types import AgentCapability


def build_tools(capabilities: List[AgentCapability]) -> tuple:
    """Build Main Agent tools dynamically from discovered capabilities.

    Returns:
        (tools_list, tools_map) — tools for the LLM, and a name→function map
        for executing non-delegation tools.
    """
    # Build capability descriptions for the delegate tool
    agents_desc = []
    for cap in capabilities:
        if cap.name == "main_agent":
            continue
        skills = ", ".join(f"{s.name}: {s.description}" for s in cap.skills)
        agents_desc.append(f"- {cap.name} ({cap.display_name}): {skills}")

    available_agents = "\n".join(agents_desc) if agents_desc else "No sub-agents available."

    # Build capabilities text for show_capabilities
    caps_lines = []
    for cap in capabilities:
        if cap.name == "main_agent":
            continue
        caps_lines.append(f"• {cap.display_name}")
        for s in cap.skills:
            caps_lines.append(f"  - {s.name}: {s.description}")
    caps_text = "\n".join(caps_lines) if caps_lines else "No additional services available yet."

    @tool
    def delegate_to_agent(agent_name: str, skill: str, reason: str) -> str:
        """Route member to a specialized agent.

        Call this when the member's request matches a sub-agent's capability.
        The system will generate a conversation summary, hand it to the target
        agent, and transfer control.

        Available agents:
        {agents}

        Args:
            agent_name: Name of the agent to delegate to
            skill: The specific skill being requested
            reason: Brief explanation of why this delegation is appropriate
        """
        return f"Delegating to {agent_name} for skill '{skill}': {reason}"

    # Inject the dynamic agent list into the docstring
    delegate_to_agent.description = delegate_to_agent.description.replace(
        "{agents}", available_agents
    )

    @tool
    def show_capabilities() -> str:
        """List all available services across all agents.

        Call this when the member asks what you can do, what services are
        available, or similar capability inquiry questions.
        """
        return f"Available services:\n{caps_text}"

    tools_list = [delegate_to_agent, show_capabilities]
    tools_map = {
        "show_capabilities": show_capabilities,
    }

    return tools_list, tools_map
