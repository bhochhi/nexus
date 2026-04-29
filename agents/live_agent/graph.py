"""
Live Agent Support — LangGraph StateGraph definition.

Implements: blueprints/live_agent/graph.spec.md
"""
from langgraph.graph import END, START, StateGraph

from .state import LiveAgentState


def build_graph():
    """Build the Live Agent Support state graph.

    Graph: START → process → END
    """
    graph = StateGraph(LiveAgentState)

    graph.add_node("process", process_node)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)

    return graph.compile()


def process_node(state: LiveAgentState) -> dict:
    """Process member input.

    TODO: Implement agent-specific logic.
    """
    return {"response": "", "reasoning": ""}
