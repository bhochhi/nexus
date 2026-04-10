import json

from nexus.graph.agent import build_graph
from nexus.memory.store import InMemoryStore
from nexus.tools.banking import register_banking_tools
from nexus.tools.faq import register_faq_tools
from nexus.tools.insurance import register_insurance_tools
from nexus.tools.registry import ToolRegistry
from tests.conftest import MockLLM


def _create_test_graph(routing_response: dict | None = None):
    """Helper to build a graph with a mock LLM."""
    if routing_response is None:
        routing_response = {
            "intent": "check_balance",
            "domain": "banking",
            "confidence": 0.95,
            "missing_slots": [],
        }

    llm = MockLLM(responses={
        "routing engine": json.dumps(routing_response),
    })

    store = InMemoryStore()
    registry = ToolRegistry()
    register_banking_tools(registry)
    register_insurance_tools(registry)
    register_faq_tools(registry)

    graph = build_graph(llm=llm, store=store, registry=registry)
    return graph, store


def test_banking_balance_flow():
    graph, store = _create_test_graph({
        "intent": "check_balance",
        "domain": "banking",
        "confidence": 0.95,
        "missing_slots": [],
    })

    result = graph.invoke({
        "user_message": "What is my balance?",
        "user_id": "test-user",
        "session_id": "test-session",
    })

    assert result.get("response_text")
    assert result["current_intent"] == "check_balance"
    assert result["intent_domain"] == "banking"
    assert result["tool_result"]["status"] == "success"


def test_insurance_claim_flow():
    graph, store = _create_test_graph({
        "intent": "file_claim",
        "domain": "insurance",
        "confidence": 0.92,
        "missing_slots": [],
    })

    result = graph.invoke({
        "user_message": "I want to file a claim",
        "user_id": "test-user",
        "session_id": "test-session",
    })

    assert result.get("response_text")
    assert result["current_intent"] == "file_claim"
    assert result["intent_domain"] == "insurance"


def test_escalation_flow():
    graph, store = _create_test_graph({
        "intent": "unknown",
        "domain": "faq",
        "confidence": 0.3,
        "missing_slots": [],
    })

    result = graph.invoke({
        "user_message": "sdkfjhskdjfh",
        "user_id": "test-user",
        "session_id": "test-session",
    })

    assert result.get("response_text")
    assert "human agent" in result["response_text"].lower() or result["should_escalate"]


def test_faq_flow():
    graph, store = _create_test_graph({
        "intent": "hours_of_operation",
        "domain": "faq",
        "confidence": 0.88,
        "missing_slots": [],
    })

    result = graph.invoke({
        "user_message": "What are your hours of operation?",
        "user_id": "test-user",
        "session_id": "test-session",
    })

    assert result.get("response_text")
    assert result["current_intent"] == "hours_of_operation"


def test_session_persistence():
    graph, store = _create_test_graph()

    graph.invoke({
        "user_message": "What is my balance?",
        "user_id": "u1",
        "session_id": "s1",
    })

    session = store.load("u1", "s1")
    assert len(session.history) >= 2  # user + assistant messages
    assert session.last_intent == "check_balance"
