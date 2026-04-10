import json
import logging

from nexus.graph.state import AgentState
from nexus.llm.base import BaseLLM
from nexus.memory.session import Session
from nexus.memory.store import SessionStore
from nexus.prompts.loader import load_prompt

logger = logging.getLogger(__name__)


def respond_node(state: AgentState, *, llm: BaseLLM, store: SessionStore) -> dict:
    """Format the final response and save session."""
    # If we already have a response (from escalation or direct LLM), use it
    if state.get("response_text"):
        response_text = state["response_text"]
    else:
        # Generate response from tool result
        tool_result = state.get("tool_result", {})
        history = state.get("conversation_history", [])
        session = Session(user_id="", session_id="", history=history)

        prompt = load_prompt(
            "response_prompt.txt",
            tool_result=json.dumps(tool_result),
            user_message=state["user_message"],
            history=session.format_history(),
        )
        response_text = llm.invoke(prompt)

    # Save session
    user_id = state.get("user_id", "anonymous")
    session_id = state.get("session_id", "default")
    session = store.load(user_id, session_id)
    session.add_message("assistant", response_text)
    session.last_intent = state.get("current_intent", "")
    store.save(session)

    return {"response_text": response_text}
