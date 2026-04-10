import json
import logging

from nexus.graph.state import AgentState
from nexus.intents.loader import format_intents_for_prompt, load_all_intents
from nexus.llm.base import BaseLLM
from nexus.memory.session import Session
from nexus.prompts.loader import load_prompt

logger = logging.getLogger(__name__)


def router_node(state: AgentState, *, llm: BaseLLM) -> dict:
    """Classify user intent using LLM-based routing."""
    intents = load_all_intents()
    intents_text = format_intents_for_prompt(intents)

    history = state.get("conversation_history", [])
    session = Session(user_id="", session_id="", history=history)
    history_text = session.format_history()

    prompt = load_prompt(
        "routing_prompt.txt",
        intents=intents_text,
        history=history_text,
        user_message=state["user_message"],
    )

    response = llm.invoke(prompt)

    try:
        parsed = json.loads(response)
        intent = parsed.get("intent", "unknown")
        domain = parsed.get("domain", "escalation")
        confidence = float(parsed.get("confidence", 0.0))
        missing_slots = parsed.get("missing_slots", [])
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse router response: %s", response)
        intent = "unknown"
        domain = "escalation"
        confidence = 0.0
        missing_slots = []

    should_escalate = confidence < 0.7

    return {
        "current_intent": intent,
        "intent_domain": "escalation" if should_escalate else domain,
        "routing_confidence": confidence,
        "should_escalate": should_escalate,
        "missing_slots": missing_slots,
    }
