"""
Auto-Insurance Agent — LangGraph StateGraph definition.
"""
from langgraph.graph import END, START, StateGraph

from .state import AutoInsuranceAgentState
from .nodes import process_node


def build_graph():
    """Build the Auto-Insurance Agent state graph.

    Graph: START → process → END
    """
    graph = StateGraph(AutoInsuranceAgentState)

    graph.add_node("process", process_node)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)

    return graph.compile()
