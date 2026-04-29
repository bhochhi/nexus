"""
Tests for Main Agent — LangGraph, tools, and delegation.

Tests the orchestrator's graph routing, tool building, and delegation protocol.
"""
import unittest
from unittest.mock import MagicMock, patch

from core.session import SessionManager
from core.types import AgentCapability, AgentResult, LLMResponse, Skill, ToolCall


class TestBuildTools(unittest.TestCase):
    """Test tool building from discovered capabilities."""

    def test_builds_two_tools(self):
        """Tools list includes delegate_to_agent and show_capabilities."""
        from agents.main_agent.tools import build_tools

        caps = [
            AgentCapability(
                name="live_agent",
                display_name="Live Agent Support",
                description="Connects to live agents",
                skills=[Skill(name="connect_to_live_agent", description="Connect to human")],
            )
        ]
        tools_list, tools_map = build_tools(caps)
        tool_names = [t.name for t in tools_list]
        assert "delegate_to_agent" in tool_names
        assert "show_capabilities" in tool_names

    def test_show_capabilities_returns_skills(self):
        """show_capabilities tool returns formatted capability text."""
        from agents.main_agent.tools import build_tools

        caps = [
            AgentCapability(
                name="live_agent",
                display_name="Live Agent Support",
                description="Live support",
                skills=[Skill(name="connect_to_live_agent", description="Connect to human")],
            )
        ]
        _, tools_map = build_tools(caps)
        result = tools_map["show_capabilities"].invoke({})
        assert "Live Agent Support" in result
        assert "connect_to_live_agent" in result

    def test_excludes_main_agent_from_delegate(self):
        """delegate_to_agent description does not include main_agent."""
        from agents.main_agent.tools import build_tools

        caps = [
            AgentCapability(name="main_agent", display_name="Nexus", description="Orchestrator"),
            AgentCapability(
                name="live_agent",
                display_name="Live Agent",
                description="Live support",
                skills=[Skill(name="connect", description="Connect")],
            ),
        ]
        tools_list, _ = build_tools(caps)
        delegate_tool = [t for t in tools_list if t.name == "delegate_to_agent"][0]
        assert "main_agent" not in delegate_tool.description
        assert "live_agent" in delegate_tool.description

    def test_empty_capabilities(self):
        """Tools build with no sub-agents — shows no agents available."""
        from agents.main_agent.tools import build_tools

        tools_list, _ = build_tools([])
        assert len(tools_list) == 2  # Both tools still created


class TestMainAgentState(unittest.TestCase):
    """Test the MainAgentState TypedDict."""

    def test_state_creation(self):
        from agents.main_agent.state import MainAgentState

        state: MainAgentState = {
            "user_input": "hello",
            "messages": [],
            "system_prompt": "You are Nexus",
            "tools": [],
            "response": "",
            "reasoning": "",
            "tool_call": None,
            "delegation_result": None,
            "delegation_occurred": False,
        }
        assert state["user_input"] == "hello"
        assert state["delegation_occurred"] is False


class TestGraphRouting(unittest.TestCase):
    """Test the graph's conditional routing logic."""

    def test_route_to_delegate_on_tool_call(self):
        """When tool_call is delegate_to_agent, route to 'delegate'."""
        from agents.main_agent.agent import MainAgent

        # We test the routing function directly
        state = {
            "tool_call": {
                "name": "delegate_to_agent",
                "arguments": {"agent_name": "live_agent"},
            }
        }
        # Create a minimal mock agent to access the method
        with patch.object(MainAgent, "__init__", lambda self, *a, **kw: None):
            agent = MainAgent.__new__(MainAgent)
            result = agent._route_after_process(state)
            assert result == "delegate"

    def test_route_to_respond_on_no_tool(self):
        """When no tool_call, route to 'respond'."""
        from agents.main_agent.agent import MainAgent

        state = {"tool_call": None}
        with patch.object(MainAgent, "__init__", lambda self, *a, **kw: None):
            agent = MainAgent.__new__(MainAgent)
            result = agent._route_after_process(state)
            assert result == "respond"

    def test_route_to_respond_on_empty_state(self):
        """When tool_call key is missing, route to 'respond'."""
        from agents.main_agent.agent import MainAgent

        state = {}
        with patch.object(MainAgent, "__init__", lambda self, *a, **kw: None):
            agent = MainAgent.__new__(MainAgent)
            result = agent._route_after_process(state)
            assert result == "respond"


class TestRespondNode(unittest.TestCase):
    """Test the respond node assembles responses correctly."""

    def test_uses_delegation_result_when_present(self):
        from agents.main_agent.agent import MainAgent

        state = {
            "delegation_result": "Connected to banking queue.",
            "response": "direct response",
        }
        with patch.object(MainAgent, "__init__", lambda self, *a, **kw: None):
            agent = MainAgent.__new__(MainAgent)
            result = agent._respond_node(state)
            assert result["response"] == "Connected to banking queue."

    def test_uses_direct_response_when_no_delegation(self):
        from agents.main_agent.agent import MainAgent

        state = {"delegation_result": None, "response": "Hello!"}
        with patch.object(MainAgent, "__init__", lambda self, *a, **kw: None):
            agent = MainAgent.__new__(MainAgent)
            result = agent._respond_node(state)
            assert result == {}  # No override needed, response already in state


class TestNodeHelpers(unittest.TestCase):
    """Test helper functions from nodes.py."""

    def test_extract_reasoning_with_tags(self):
        from agents.main_agent.nodes import extract_reasoning

        text = "<reasoning>Member wants live help</reasoning>Let me connect you."
        reasoning, clean = extract_reasoning(text)
        assert reasoning == "Member wants live help"
        assert "Let me connect you" in clean
        assert "<reasoning>" not in clean

    def test_extract_reasoning_without_tags(self):
        from agents.main_agent.nodes import extract_reasoning

        text = "Hello! How can I help?"
        reasoning, clean = extract_reasoning(text)
        assert reasoning == ""
        assert clean == text


class TestMainAgentGraph(unittest.TestCase):
    """Test the compiled graph structure."""

    def test_graph_compiles(self):
        """Graph can be built and compiled without errors."""
        from agents.main_agent.graph import build_main_agent_graph

        # Dummy node functions
        def process(state):
            return {"response": "hi", "reasoning": ""}
        def delegate(state):
            return {}
        def respond(state):
            return {}
        def route(state):
            return "respond"

        graph = build_main_agent_graph(process, delegate, respond, route)
        assert graph is not None

    def test_graph_runs_direct_response(self):
        """Graph produces a response for direct (no-tool) path."""
        from agents.main_agent.graph import build_main_agent_graph

        def process(state):
            return {"response": "Welcome!", "reasoning": "greeting"}
        def delegate(state):
            return {}
        def respond(state):
            return {}
        def route(state):
            return "respond"

        graph = build_main_agent_graph(process, delegate, respond, route)
        result = graph.invoke({
            "user_input": "hello",
            "messages": [],
            "system_prompt": "",
            "tools": [],
            "response": "",
            "reasoning": "",
            "tool_call": None,
            "delegation_result": None,
            "delegation_occurred": False,
        })
        assert result["response"] == "Welcome!"
        assert result["reasoning"] == "greeting"


if __name__ == "__main__":
    unittest.main()
