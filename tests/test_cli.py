from types import SimpleNamespace

from member_assistant.cli import _provider_line
from member_assistant.config import Settings
from member_assistant.providers import DeterministicProvider


def test_mock_provider_is_not_reported_as_a_fallback():
    runtime = SimpleNamespace(provider=DeterministicProvider())
    line = _provider_line(Settings(provider_name="mock"), runtime)

    assert "requested=mock" in line
    assert "active=deterministic" in line
    assert "fallback=not used" in line
    assert "fallback_policy=not applicable" in line


def test_missing_openai_key_is_reported_as_an_active_fallback():
    runtime = SimpleNamespace(
        provider=DeterministicProvider(
            fallback_from="openai", fallback_reason="missing_api_key"
        )
    )
    line = _provider_line(Settings(provider_name="openai"), runtime)

    assert "requested=openai" in line
    assert "active=deterministic" in line
    assert "fallback=USED" in line
    assert "reason=missing_api_key" in line


def test_openai_responses_endpoint_and_reasoning_are_visible():
    provider = SimpleNamespace(
        name="openai",
        model_id="gpt-5.6-luna",
        observability_metadata=lambda: {
            "provider": "openai",
            "model": "gpt-5.6-luna",
            "api_endpoint": "responses",
            "reasoning_effort": "low",
            "fallback_used": False,
        },
    )
    runtime = SimpleNamespace(provider=provider)

    line = _provider_line(Settings(), runtime)

    assert "model=gpt-5.6-luna" in line
    assert "endpoint=responses" in line
    assert "reasoning=low" in line
