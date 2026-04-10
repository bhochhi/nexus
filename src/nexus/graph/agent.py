import functools
import logging

from langgraph.graph import END, StateGraph

from nexus.graph.edges import needs_tool_execution, route_by_intent
from nexus.graph.nodes.banking import banking_node
from nexus.graph.nodes.entry import entry_node
from nexus.graph.nodes.escalation import escalation_node
from nexus.graph.nodes.faq import faq_node
from nexus.graph.nodes.insurance import insurance_node
from nexus.graph.nodes.respond import respond_node
from nexus.graph.nodes.router import router_node
from nexus.graph.state import AgentState
from nexus.llm.base import BaseLLM
from nexus.memory.store import SessionStore
from nexus.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def _tool_execute_node(state: AgentState, *, registry: ToolRegistry) -> dict:
    """Execute the tool specified in state and return the result."""
    tool_name = state.get("tool_name", "")
    tool_args = state.get("tool_args", {})

    if not tool_name:
        return {"tool_result": {}, "tool_error": "No tool specified"}

    try:
        tool = registry.get(tool_name)
        result = tool.execute(tool_args)
        return {"tool_result": result, "tool_error": ""}
    except KeyError:
        return {"tool_result": {}, "tool_error": f"Tool not found: {tool_name}"}
    except Exception as e:
        logger.exception("Tool execution failed: %s", tool_name)
        return {"tool_result": {}, "tool_error": str(e)}


def build_graph(
    llm: BaseLLM,
    store: SessionStore,
    registry: ToolRegistry,
) -> StateGraph:
    """Build and compile the conversational agent LangGraph."""
    graph = StateGraph(AgentState)

    # Bind dependencies to node functions using functools.partial
    graph.add_node("entry", functools.partial(entry_node, store=store))
    graph.add_node("router", functools.partial(router_node, llm=llm))
    graph.add_node("banking", functools.partial(banking_node, llm=llm, registry=registry))
    graph.add_node("insurance", functools.partial(insurance_node, llm=llm, registry=registry))
    graph.add_node("faq", functools.partial(faq_node, llm=llm))
    graph.add_node("escalation", escalation_node)
    graph.add_node("tool_execute", functools.partial(_tool_execute_node, registry=registry))
    graph.add_node("respond", functools.partial(respond_node, llm=llm, store=store))

    # Entry point
    graph.set_entry_point("entry")

    # Edges
    graph.add_edge("entry", "router")
    graph.add_conditional_edges(
        "router",
        route_by_intent,
        {"banking": "banking", "insurance": "insurance", "faq": "faq", "escalation": "escalation"},
    )

    # Each domain handler -> conditional: tool_execute or respond
    for domain in ["banking", "insurance", "faq"]:
        graph.add_conditional_edges(
            domain,
            needs_tool_execution,
            {"tool_execute": "tool_execute", "respond": "respond"},
        )

    graph.add_edge("escalation", "respond")
    graph.add_edge("tool_execute", "respond")
    graph.add_edge("respond", END)

    return graph.compile()
