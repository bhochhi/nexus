import logging

from nexus.graph.state import AgentState
from nexus.instructions.loader import load_instructions
from nexus.llm.base import BaseLLM
from nexus.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

INTENT_TO_TOOL = {
    "file_claim": "file_claim",
    "check_claim_status": "check_claim_status",
    "get_policy_details": "get_policy_details",
    "request_quote": "request_quote",
    "update_policy": None,
    "add_vehicle": None,
    "remove_vehicle": None,
    "renew_policy": None,
    "cancel_policy": None,
    "roadside_assistance": None,
}


def insurance_node(state: AgentState, *, llm: BaseLLM, registry: ToolRegistry) -> dict:
    """Handle insurance domain intents."""
    intent = state.get("current_intent", "")
    tool_name = INTENT_TO_TOOL.get(intent)

    if not tool_name:
        rules = load_instructions("insurance")
        rules_text = "\n".join(f"- {r}" for r in rules)
        prompt = (
            f"Insurance rules:\n{rules_text}\n\n"
            f"User intent: {intent}\n"
            f"User message: {state['user_message']}\n\n"
            "Provide a helpful response about this insurance topic."
        )
        response = llm.invoke(prompt)
        return {"response_text": response, "tool_name": "", "tool_args": {}}

    tool_args = {"user_id": state.get("user_id", "anonymous")}

    return {"tool_name": tool_name, "tool_args": tool_args}
