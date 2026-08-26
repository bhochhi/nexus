import json

import pytest

from member_assistant.providers import (
    DeterministicProvider,
    ProviderError,
    ProviderSafetyError,
)
from member_assistant.providers.bedrock_provider import BedrockProvider
from member_assistant.providers.factory import FallbackProvider


class _FakeBedrockClient:
    def __init__(self, response=None, error=None):
        self.response = response or {}
        self.error = error
        self.requests = []

    def converse(self, **kwargs):
        self.requests.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def _response(text, *, stop_reason="end_turn"):
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": text}],
            }
        },
        "stopReason": stop_reason,
        "usage": {"inputTokens": 31, "outputTokens": 19, "totalTokens": 50},
        "metrics": {"latencyMs": 87},
        "ResponseMetadata": {"RequestId": "request-123", "HTTPStatusCode": 200},
    }


@pytest.mark.parametrize(
    "model_id",
    ["us.amazon.nova-2-lite-v1:0", "us.openai.gpt-5.6-terra"],
)
def test_bedrock_nova_and_terra_share_converse_turn_contract(
    runtime_factory, model_id
):
    runtime = runtime_factory()
    client = _FakeBedrockClient(
        _response(
            "```json\n"
            + json.dumps(
                {
                    "goals": [
                        {
                            "skill_name": "guided_balance",
                            "goal": "check_account_balance",
                            "confidence": 0.94,
                            "inputs": {"account": "checking"},
                        }
                    ],
                    "slot_updates": [],
                    "conversation_act": "new_goal",
                    "active_goal_relation": "none",
                    "skill_gap": None,
                }
            )
            + "\n```"
        )
    )
    provider = BedrockProvider(
        model_id,
        region="us-east-1",
        max_tokens=900,
        client=client,
    )

    analysis = provider.understand_turn(
        "What is my checking balance?", runtime.catalog.routes(), {}
    )

    assert analysis.goals[0].skill_name == "guided_balance"
    assert analysis.goals[0].goal == "check_account_balance"
    assert analysis.goals[0].inputs == {"account": "checking"}
    request = client.requests[0]
    assert request["modelId"] == model_id
    assert request["inferenceConfig"] == {"maxTokens": 900}
    assert request["messages"][0]["role"] == "user"
    payload = json.loads(request["messages"][0]["content"][0]["text"])
    assert payload["member_message"] == "What is my checking balance?"
    assert payload["output_requirement"] == "Return valid JSON only."
    metadata = provider.observability_metadata()
    assert metadata["provider"] == "bedrock"
    assert metadata["api_endpoint"] == "converse"
    assert metadata["aws_region"] == "us-east-1"
    assert metadata["input_tokens"] == 31
    assert metadata["provider_request_id"] == "request-123"


def test_bedrock_attaches_guardrail_to_converse_request():
    client = _FakeBedrockClient(_response("Grounded response."))
    provider = BedrockProvider(
        "us.amazon.nova-2-lite-v1:0",
        region="us-east-1",
        guardrail_id="guardrail-abc",
        guardrail_version="7",
        guardrail_trace="enabled",
        client=client,
    )

    assert provider.generate_response("Respond warmly.", {"status": "mock"}) == (
        "Grounded response."
    )

    request = client.requests[0]
    assert request["guardrailConfig"] == {
        "guardrailIdentifier": "guardrail-abc",
        "guardrailVersion": "7",
        "trace": "enabled",
    }
    guarded = request["messages"][0]["content"][0]["guardContent"]
    assert guarded["text"]["qualifiers"] == ["query"]
    assert provider.observability_metadata()["guardrail_enabled"] is True
    assert provider.observability_metadata()["guardrail_trace_enabled"] is True


def test_guardrail_intervention_is_a_member_response_and_audited(runtime_factory):
    client = _FakeBedrockClient(
        _response(
            "I can't help with that request.",
            stop_reason="guardrail_intervened",
        )
    )
    provider = BedrockProvider(
        "us.amazon.nova-2-lite-v1:0",
        region="us-east-1",
        guardrail_id="guardrail-abc",
        guardrail_version="DRAFT",
        client=client,
    )
    runtime = runtime_factory(provider=provider)

    reply = runtime.chat("guardrail-session", "blocked input")

    assert "can't help" in reply.text
    assert reply.outcome == {"status": "guardrail_intervened"}
    assert provider.observability_metadata()["guardrail_intervened"] is True
    audit = runtime.store.audit_events("guardrail-session")
    safety_event = next(
        event for event in audit if event["event_type"] == "provider_safety_intervention"
    )
    assert safety_event["payload"]["stop_reason"] == "guardrail_intervened"
    assert "blocked input" not in str(safety_event)


def test_fallback_provider_never_bypasses_a_safety_error(runtime_factory):
    class _BlockedProvider(DeterministicProvider):
        name = "blocked-primary"

        def understand_turn(self, message, catalog, context=None):
            raise ProviderSafetyError("blocked by provider policy")

    fallback = DeterministicProvider()
    provider = FallbackProvider(_BlockedProvider(), fallback)
    runtime = runtime_factory()

    with pytest.raises(ProviderSafetyError):
        provider.understand_turn("hello", runtime.catalog.routes(), {})

    assert provider.observability_metadata()["fallback_used"] is False


def test_bedrock_error_keeps_safe_aws_metadata_and_redacts_credentials():
    class _AwsError(Exception):
        response = {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "credential=AKIAABCDEFGHIJKLMNOP was rejected",
            },
            "ResponseMetadata": {"HTTPStatusCode": 403, "RequestId": "denied-1"},
        }

    provider = BedrockProvider(
        "us.amazon.nova-2-lite-v1:0",
        region="us-east-1",
        client=_FakeBedrockClient(error=_AwsError()),
    )

    with pytest.raises(ProviderError) as caught:
        provider.generate_response("Respond.", {})

    assert caught.value.status_code == 403
    assert caught.value.error_code == "AccessDeniedException"
    assert "AKIAABCDEFGHIJKLMNOP" not in str(caught.value)
    assert "[redacted]" in str(caught.value)


def test_bedrock_guardrail_id_and_version_are_an_atomic_configuration():
    with pytest.raises(ProviderError, match="must be set together"):
        BedrockProvider(
            "us.amazon.nova-2-lite-v1:0",
            region="us-east-1",
            guardrail_id="guardrail-abc",
            client=_FakeBedrockClient(),
        )
