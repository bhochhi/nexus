"""
Main Agent — LangGraph StateGraph definition.

Graph: START → process → [route] → delegate/respond → END

Implements: blueprints/main_agent/graph.spec.md
"""
from langgraph.graph import END, START, StateGraph

from .state import MainAgentState


def build_main_agent_graph(process_node, delegate_node, respond_node, route_fn):
    """Build the Main Agent state graph.

    Nodes are passed as callbacks so the graph is decoupled from the agent class.

    Args:
        process_node: LLM call with tools — handles show_capabilities internally
        delegate_node: Handles delegation to sub-agents
        respond_node: Assembles final response
        route_fn: Conditional routing function after process
    """
    graph = StateGraph(MainAgentState)

    graph.add_node("process", process_node)
    graph.add_node("delegate", delegate_node)
    graph.add_node("respond", respond_node)

    graph.add_edge(START, "process")
    graph.add_conditional_edges("process", route_fn, {
        "delegate": "delegate",
        "respond": "respond",
    })
    graph.add_edge("delegate", "respond")
    graph.add_edge("respond", END)

    return graph.compile()
