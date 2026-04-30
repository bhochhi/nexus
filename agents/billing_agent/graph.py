"""
Billing Agent — LangGraph StateGraph definition.

Implements: blueprints/billing_agent/graph.spec.md
"""
from langgraph.graph import END, START, StateGraph

from .state import BillingAgentState


def build_graph():
    """Build the Billing Agent state graph.

    Graph: START → process → END
    """
    graph = StateGraph(BillingAgentState)

    graph.add_node("process", process_node)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)

    return graph.compile()


def process_node(state: BillingAgentState) -> dict:
    """Process member input.

    TODO: Implement agent-specific logic.
    """
    return {"response": "", "reasoning": ""}
