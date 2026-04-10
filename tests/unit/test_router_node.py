import json

from nexus.graph.nodes.router import router_node
from tests.conftest import MockLLM


def test_router_parses_valid_response():
    llm = MockLLM(responses={
        "routing engine": json.dumps({
            "intent": "check_balance",
            "domain": "banking",
            "confidence": 0.95,
            "missing_slots": [],
        })
    })

    state = {"user_message": "What is my balance?", "conversation_history": []}
    result = router_node(state, llm=llm)

    assert result["current_intent"] == "check_balance"
    assert result["intent_domain"] == "banking"
    assert result["routing_confidence"] == 0.95
    assert result["should_escalate"] is False


def test_router_low_confidence_escalates():
    llm = MockLLM(responses={
        "routing engine": json.dumps({
            "intent": "unknown",
            "domain": "faq",
            "confidence": 0.3,
            "missing_slots": [],
        })
    })

    state = {"user_message": "blah blah blah", "conversation_history": []}
    result = router_node(state, llm=llm)

    assert result["should_escalate"] is True
    assert result["intent_domain"] == "escalation"


def test_router_handles_invalid_json():
    llm = MockLLM(responses={"routing engine": "not valid json"})

    state = {"user_message": "hello", "conversation_history": []}
    result = router_node(state, llm=llm)

    assert result["current_intent"] == "unknown"
    assert result["should_escalate"] is True
