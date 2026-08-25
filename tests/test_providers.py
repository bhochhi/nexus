import json
from types import SimpleNamespace

import pytest

from member_assistant.providers import ProviderError
from member_assistant.providers.openai_provider import OpenAIProvider


class _FakeResponses:
    def __init__(self, output_text="", error=None):
        self.output_text = output_text
        self.error = error
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(
            usage=SimpleNamespace(
                input_tokens=25, output_tokens=18, total_tokens=43
            ),
            output_text=self.output_text,
        )


def _provider(responses, model_id="gpt-5.6-luna"):
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider._client = SimpleNamespace(responses=responses)
    provider._model_id = model_id
    provider._reasoning_effort = "low"
    provider.model_id = model_id
    provider.name = "openai"
    provider._last_call_metadata = {
        "provider": "openai",
        "model": model_id,
        "api_endpoint": "responses",
        "reasoning_effort": "low",
        "fallback_used": False,
    }
    return provider


def test_openai_analysis_uses_responses_api_and_returns_skill_gap(runtime_factory):
    runtime = runtime_factory()
    responses = _FakeResponses(
        json.dumps(
            {
                "goals": [],
                "skill_gap": {
                    "objective": "recover your online ID",
                    "category": "online_id_recovery",
                    "confidence": 0.97,
                },
            }
        )
    )
    provider = _provider(responses)

    analysis = provider.analyze_message(
        "recover my online id", runtime.catalog.list(), {}
    )

    assert analysis.goals == []
    assert analysis.skill_gap.objective == "recover your online ID"
    assert analysis.skill_gap.category == "online_id_recovery"
    assert analysis.skill_gap.confidence == 0.97
    assert len(responses.requests) == 1
    request = responses.requests[0]
    assert request["model"] == "gpt-5.6-luna"
    assert request["reasoning"] == {"effort": "low"}
    assert request["text"] == {"format": {"type": "json_object"}}
    assert request["store"] is False
    assert "temperature" not in request
    assert "messages" not in request
    metadata = provider.observability_metadata()
    assert metadata["operation"] == "analyze_message"
    assert metadata["api_endpoint"] == "responses"
    assert metadata["reasoning_effort"] == "low"
    assert metadata["input_tokens"] == 25
    assert metadata["output_tokens"] == 18


def test_openai_response_generation_uses_responses_output_text():
    responses = _FakeResponses("Here is the grounded answer.")
    provider = _provider(responses)

    result = provider.generate_response("Explain the result.", {"status": "mock"})

    assert result == "Here is the grounded answer."
    request = responses.requests[0]
    assert request["reasoning"] == {"effort": "low"}
    assert request["store"] is False
    assert "text" not in request
    assert provider.observability_metadata()["operation"] == "generate_response"


def test_non_reasoning_openai_model_omits_reasoning_parameter():
    responses = _FakeResponses("Done.")
    provider = _provider(responses, model_id="gpt-4o-mini")

    provider.generate_response("Respond.", {})

    assert "reasoning" not in responses.requests[0]
    assert provider.observability_metadata()["reasoning_effort"] == "not_applicable"


def test_openai_error_preserves_safe_api_diagnostics_and_redacts_key(runtime_factory):
    class _ApiError(Exception):
        status_code = 400
        body = {
            "error": {
                "code": "unsupported_parameter",
                "param": "temperature",
                "message": "Bad request with sk-secret-value",
            }
        }

    runtime = runtime_factory()
    provider = _provider(_FakeResponses(error=_ApiError("unsafe sk-other-secret")))

    with pytest.raises(ProviderError) as caught:
        provider.analyze_message("hello", runtime.catalog.list(), {})

    assert caught.value.status_code == 400
    assert caught.value.error_code == "unsupported_parameter"
    assert caught.value.parameter == "temperature"
    assert "sk-secret-value" not in str(caught.value)
    assert "[redacted]" in str(caught.value)
