from typing import TypedDict


class AgentState(TypedDict, total=False):
    """State that flows through every node in the LangGraph."""

    # Input
    user_message: str
    user_id: str
    session_id: str

    # Session context
    conversation_history: list[dict]
    preferences: dict
    last_intent: str

    # Routing
    current_intent: str
    intent_domain: str  # "banking" | "insurance" | "faq" | "escalation"
    routing_confidence: float

    # Tool execution
    tool_name: str
    tool_args: dict
    tool_result: dict
    tool_error: str

    # Response
    response_text: str
    needs_clarification: bool
    missing_slots: list[str]

    # Control
    error_count: int
    should_escalate: bool
