import logging

from nexus.graph.state import AgentState
from nexus.instructions.loader import load_instructions
from nexus.llm.base import BaseLLM
from nexus.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

INTENT_TO_TOOL = {
    "check_balance": "get_account_balance",
    "transfer_money": "transfer_funds",
    "view_transactions": "get_transactions",
    "report_fraud": "report_fraud",
    "freeze_card": "freeze_card",
    "activate_card": None,
    "update_contact_info": None,
    "open_account": None,
    "close_account": None,
    "dispute_transaction": None,
}


def banking_node(state: AgentState, *, llm: BaseLLM, registry: ToolRegistry) -> dict:
    """Handle banking domain intents."""
    intent = state.get("current_intent", "")
    tool_name = INTENT_TO_TOOL.get(intent)

    if not tool_name:
        # No tool available — generate a direct LLM response
        rules = load_instructions("banking")
        rules_text = "\n".join(f"- {r}" for r in rules)
        prompt = (
            f"Banking rules:\n{rules_text}\n\n"
            f"User intent: {intent}\n"
            f"User message: {state['user_message']}\n\n"
            "Provide a helpful response about this banking topic."
        )
        response = llm.invoke(prompt)
        return {"response_text": response, "tool_name": "", "tool_args": {}}

    tool_args = {"user_id": state.get("user_id", "anonymous")}

    return {"tool_name": tool_name, "tool_args": tool_args}
