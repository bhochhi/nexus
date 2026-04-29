"""
Tests for core/types.py

Acceptance criteria from blueprints/core/types.spec.md
"""
from datetime import datetime

from core.types import (
    AgentCapability,
    AgentResult,
    DelegationRequest,
    DelegationResponse,
    LLMResponse,
    Message,
    Skill,
    ToolCall,
)


class TestMessage:
    def test_create_message(self):
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.agent == ""
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}

    def test_message_with_metadata(self):
        msg = Message(role="assistant", content="hi", agent="main_agent", metadata={"reasoning": "greeting"})
        assert msg.agent == "main_agent"
        assert msg.metadata["reasoning"] == "greeting"


class TestSkill:
    def test_create_skill(self):
        skill = Skill(name="connect_to_live_agent", description="Connect to human")
        assert skill.name == "connect_to_live_agent"
        assert skill.description == "Connect to human"


class TestAgentCapability:
    def test_create_capability(self):
        cap = AgentCapability(
            name="live_agent",
            display_name="Live Agent Support",
            description="Connects to live agents",
            skills=[Skill(name="connect", description="Connect to human")],
            version="1.0.0",
            status="active",
            module_path="/agents/live_agent",
        )
        assert cap.name == "live_agent"
        assert len(cap.skills) == 1
        assert cap.status == "active"

    def test_defaults(self):
        cap = AgentCapability(name="test", display_name="Test", description="Test agent")
        assert cap.skills == []
        assert cap.version == "1.0.0"
        assert cap.status == "active"
        assert cap.module_path == ""


class TestToolCall:
    def test_create_tool_call(self):
        tc = ToolCall(name="delegate", arguments={"agent": "live_agent"}, tool_use_id="123")
        assert tc.name == "delegate"
        assert tc.arguments["agent"] == "live_agent"


class TestLLMResponse:
    def test_text_response(self):
        resp = LLMResponse(text="Hello!", reasoning="greeting detected")
        assert resp.text == "Hello!"
        assert resp.tool_call is None
        assert resp.reasoning == "greeting detected"

    def test_tool_call_response(self):
        tc = ToolCall(name="delegate", arguments={"agent": "live"})
        resp = LLMResponse(tool_call=tc)
        assert resp.text == ""
        assert resp.tool_call.name == "delegate"


class TestDelegation:
    def test_delegation_request(self):
        req = DelegationRequest(source_agent="main", target_agent="live", user_input="help", summary="needs help")
        assert req.source_agent == "main"
        assert req.context == {}

    def test_delegation_response(self):
        resp = DelegationResponse(agent_name="live", response="connected", status="complete")
        assert resp.return_to_orchestrator is True
        assert resp.summary == ""


class TestAgentResult:
    def test_create_result(self):
        result = AgentResult(response="Hello!", active_agent="main_agent")
        assert result.response == "Hello!"
        assert result.delegation_occurred is False
        assert result.state_snapshot == {}
