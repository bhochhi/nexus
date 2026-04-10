import json

import pytest

from nexus.llm.base import BaseLLM
from nexus.memory.store import InMemoryStore
from nexus.tools.banking import register_banking_tools
from nexus.tools.faq import register_faq_tools
from nexus.tools.insurance import register_insurance_tools
from nexus.tools.registry import ToolRegistry


class MockLLM(BaseLLM):
    """Mock LLM that returns predetermined responses based on input patterns."""

    def __init__(self, responses: dict | None = None):
        super().__init__("mock-model")
        self.responses = responses or {}
        self.call_log: list[str] = []

    def invoke(self, prompt: str, system_prompt: str | None = None) -> str:
        self.call_log.append(prompt)

        # Check for pattern matches in responses dict
        for pattern, response in self.responses.items():
            if pattern.lower() in prompt.lower():
                return response

        # Default: return a routing response
        if "routing engine" in prompt.lower():
            return json.dumps({
                "intent": "check_balance",
                "domain": "banking",
                "confidence": 0.95,
                "missing_slots": [],
            })

        return "I can help you with that."

    def invoke_with_tools(
        self,
        prompt: str,
        tools: list[dict],
        system_prompt: str | None = None,
    ) -> dict:
        self.call_log.append(prompt)
        return {"text": "Tool response", "tool_calls": []}


@pytest.fixture
def mock_llm():
    return MockLLM()


@pytest.fixture
def store():
    return InMemoryStore()


@pytest.fixture
def registry():
    reg = ToolRegistry()
    register_banking_tools(reg)
    register_insurance_tools(reg)
    register_faq_tools(reg)
    return reg
