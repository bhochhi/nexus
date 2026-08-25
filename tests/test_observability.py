from member_assistant.observability import (
    MemoryTraceSink,
    Observability,
    _pretty_console_event,
)
from member_assistant.providers import DeterministicProvider, GoalAnalysis, SkillGap


class _GapAwareProvider(DeterministicProvider):
    def analyze_message(self, message, catalog, context=None):
        return GoalAnalysis(
            goals=[],
            skill_gap=SkillGap(
                objective="recover your online ID",
                category="online_id_recovery",
                confidence=0.96,
            ),
        )


def _event(sink, name):
    return next(event for event in sink.events if event["name"] == name)


def test_runtime_emits_platform_traces_for_a_catalog_skill(runtime_factory):
    sink = MemoryTraceSink()
    observability = Observability([sink], include_content=False)
    runtime = runtime_factory(observability=observability)

    reply = runtime.chat("trace-member", "How does overdraft protection work?")

    names = [event["name"] for event in sink.events]
    assert reply.selected_skill == "approved_knowledge"
    assert "member-assistant.turn" in names
    assert "state.load" in names
    assert "graph.understand" in names
    assert "llm.goal_detection" in names
    assert "policy.evaluate" in names
    assert "skill.approved_knowledge" in names
    assert "workflow.call_tool" in names
    assert "tool.local_knowledge.search" in names
    assert "llm.grounded_response" in names
    assert "state.persist" in names

    goal = _event(sink, "llm.goal_detection")
    assert goal["metadata"]["provider"] == "deterministic"
    assert goal["output"]["candidates"][0]["confidence"] >= 0.5
    assert goal["input"]["content_redacted"] is True
    assert "overdraft" not in str(goal["input"]).lower()

    tool = _event(sink, "tool.local_knowledge.search")
    assert tool["input"] == {
        "argument_names": ["limit", "query"],
        "content_redacted": True,
    }
    assert "linked savings" not in str(tool["output"]).lower()

    turn = _event(sink, "member-assistant.turn")
    assert turn["trace"]["session_id"].startswith("sha256:")
    assert turn["trace"]["session_id"] != "trace-member"
    assert turn["metadata"]["selected_skill"] == "approved_knowledge"


def test_trace_content_is_explicitly_opt_in(runtime_factory):
    sink = MemoryTraceSink()
    observability = Observability(
        [sink], include_content=True, hash_session_id=False
    )
    runtime = runtime_factory(observability=observability)

    runtime.chat("visible-session", "What is my checking balance?")

    goal = _event(sink, "llm.goal_detection")
    tool = _event(sink, "tool.mock_accounts.list_eligible_balances")
    turn = _event(sink, "member-assistant.turn")
    assert goal["input"]["message"] == "What is my checking balance?"
    assert tool["output"][0]["available_balance"] == "2,450.75"
    assert turn["trace"]["session_id"] == "visible-session"


def test_unmatched_turn_traces_reception_generation(runtime_factory):
    sink = MemoryTraceSink()
    observability = Observability([sink], include_content=False)
    runtime = runtime_factory(observability=observability)

    runtime.chat("reception-trace", "purple clouds")

    reception = _event(sink, "llm.reception_response")
    assert reception["metadata"]["provider"] == "deterministic"
    assert reception["input"]["available_service_count"] == 3
    assert reception["input"]["content_redacted"] is True


def test_skill_gap_is_visible_as_a_structured_trace_event(runtime_factory):
    sink = MemoryTraceSink()
    observability = Observability([sink], include_content=False)
    runtime = runtime_factory(
        observability=observability, provider=_GapAwareProvider()
    )

    runtime.chat("gap-trace", "recover my online id")

    gap = _event(sink, "skill_gap.detected")
    assert gap["metadata"]["category"] == "online_id_recovery"
    assert gap["metadata"]["objective"] == "recover your online ID"
    assert gap["metadata"]["confidence"] == 0.96
    assert "member_message" not in gap["metadata"]
    assert "llm.reception_response" not in [event["name"] for event in sink.events]

    rendered = _pretty_console_event(gap, color=False)
    assert "GAP" in rendered
    assert "gap_category=online_id_recovery" in rendered


def test_pretty_console_trace_highlights_provider_and_fallback_status():
    rendered = _pretty_console_event(
        {
            "name": "llm.goal_detection",
            "status": "ok",
            "duration_ms": 123.4,
            "metadata": {
                "provider": "openai",
                "model": "demo-model",
                "api_endpoint": "responses",
                "reasoning_effort": "low",
                "fallback_used": False,
            },
            "output": {
                "candidates": [
                    {"skill": "approved_knowledge", "confidence": 0.92}
                ]
            },
        },
        color=False,
    )

    assert "LLM" in rendered
    assert "provider=openai" in rendered
    assert "model=demo-model" in rendered
    assert "endpoint=responses" in rendered
    assert "reasoning=low" in rendered
    assert "fallback=no" in rendered
    assert "approved_knowledge@0.92" in rendered
