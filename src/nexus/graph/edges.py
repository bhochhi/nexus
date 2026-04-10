from nexus.graph.state import AgentState


def route_by_intent(state: AgentState) -> str:
    """Conditional edge from router to the appropriate domain handler."""
    if state.get("should_escalate"):
        return "escalation"
    domain = state.get("intent_domain", "escalation")
    if domain in ("banking", "insurance", "faq"):
        return domain
    return "escalation"


def needs_tool_execution(state: AgentState) -> str:
    """Conditional edge: does the domain handler need a tool call?"""
    if state.get("response_text"):
        return "respond"
    if state.get("tool_name"):
        return "tool_execute"
    return "respond"
