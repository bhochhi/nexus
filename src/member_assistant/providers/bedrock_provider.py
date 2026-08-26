"""Amazon Bedrock Runtime Converse adapter. No AWS types escape this module."""

import json
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from member_assistant.catalog import SkillRoutingDefinition
from .base import GoalMatch, ModelProvider, ProviderError, TurnAnalysis
from .turn_contract import (
    TURN_UNDERSTANDING_INSTRUCTION,
    parse_turn_analysis,
    turn_request_payload,
)


_SAFETY_STOP_REASONS = {"guardrail_intervened", "content_filtered"}


class BedrockProvider(ModelProvider):
    """Use Bedrock Converse for both Amazon Nova and Bedrock-hosted OpenAI models."""

    def __init__(
        self,
        model_id: str,
        *,
        region: str,
        profile: Optional[str] = None,
        max_tokens: int = 1200,
        guardrail_id: Optional[str] = None,
        guardrail_version: Optional[str] = None,
        guardrail_trace: str = "disabled",
        client: Optional[Any] = None,
    ) -> None:
        if not model_id:
            raise ProviderError(
                "BEDROCK_MODEL_ID is required for Amazon Bedrock",
                fallback_allowed=False,
            )
        if bool(guardrail_id) != bool(guardrail_version):
            raise ProviderError(
                "BEDROCK_GUARDRAIL_ID and BEDROCK_GUARDRAIL_VERSION must be set together",
                error_code="invalid_guardrail_configuration",
                fallback_allowed=False,
            )
        if guardrail_trace not in {"enabled", "disabled", "enabled_full"}:
            raise ProviderError(
                "BEDROCK_GUARDRAIL_TRACE must be enabled, disabled, or enabled_full",
                error_code="invalid_guardrail_trace",
                fallback_allowed=False,
            )
        if max_tokens <= 0:
            raise ProviderError(
                "BEDROCK_MAX_TOKENS must be greater than zero",
                error_code="invalid_max_tokens",
                fallback_allowed=False,
            )

        self.name = "bedrock"
        self.model_id = model_id
        self._region = region
        self._profile = profile
        self._max_tokens = max_tokens
        self._guardrail_id = guardrail_id
        self._guardrail_version = guardrail_version
        self._guardrail_trace = guardrail_trace
        self._client = client or self._build_client(region, profile)
        self._last_call_metadata = self._base_metadata()

    @staticmethod
    def _build_client(region: str, profile: Optional[str]) -> Any:
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - packaging guard
            raise ProviderError(
                "Amazon Bedrock needs the bedrock extra: pip install -e '.[bedrock]'",
                error_code="missing_dependency",
            ) from exc
        try:
            if profile:
                session = boto3.Session(profile_name=profile, region_name=region)
                return session.client("bedrock-runtime", region_name=region)
            return boto3.client("bedrock-runtime", region_name=region)
        except Exception as exc:
            raise BedrockProvider._safe_provider_error("client initialization", exc) from exc

    def _base_metadata(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "model": self.model_id,
            "api_endpoint": "converse",
            "aws_region": self._region,
            "guardrail_enabled": bool(self._guardrail_id),
            "guardrail_id": self._guardrail_id,
            "guardrail_version": self._guardrail_version,
            "guardrail_trace_enabled": (
                bool(self._guardrail_id) and self._guardrail_trace != "disabled"
            ),
            "fallback_used": False,
        }

    def observability_metadata(self) -> Dict[str, Any]:
        return dict(self._last_call_metadata)

    def _request_options(self, system_instruction: str, input_text: str) -> Dict[str, Any]:
        content: List[Dict[str, Any]]
        if self._guardrail_id:
            content = [
                {
                    "guardContent": {
                        "text": {
                            "text": input_text,
                            "qualifiers": ["query"],
                        }
                    }
                }
            ]
        else:
            content = [{"text": input_text}]
        options: Dict[str, Any] = {
            "modelId": self.model_id,
            "system": [{"text": system_instruction}],
            "messages": [{"role": "user", "content": content}],
            "inferenceConfig": {"maxTokens": self._max_tokens},
        }
        if self._guardrail_id:
            options["guardrailConfig"] = {
                "guardrailIdentifier": self._guardrail_id,
                "guardrailVersion": self._guardrail_version,
                "trace": self._guardrail_trace,
            }
        return options

    @staticmethod
    def _response_text(response: Mapping[str, Any]) -> str:
        content = (
            response.get("output", {})
            .get("message", {})
            .get("content", [])
        )
        return "".join(
            str(block.get("text", ""))
            for block in content
            if isinstance(block, Mapping) and block.get("text")
        ).strip()

    def _capture_response(self, response: Mapping[str, Any], operation: str) -> str:
        usage = response.get("usage", {})
        response_metadata = response.get("ResponseMetadata", {})
        stop_reason = str(response.get("stopReason", "unknown"))
        self._last_call_metadata = {
            **self._base_metadata(),
            "operation": operation,
            "stop_reason": stop_reason,
            "guardrail_intervened": stop_reason == "guardrail_intervened",
            "input_tokens": usage.get("inputTokens"),
            "output_tokens": usage.get("outputTokens"),
            "total_tokens": usage.get("totalTokens"),
            "provider_latency_ms": response.get("metrics", {}).get("latencyMs"),
            "provider_request_id": response_metadata.get("RequestId"),
        }
        return self._response_text(response)

    @staticmethod
    def _safe_provider_error(operation: str, exc: Exception) -> ProviderError:
        response = getattr(exc, "response", None)
        response = response if isinstance(response, dict) else {}
        error = response.get("Error", {})
        metadata = response.get("ResponseMetadata", {})
        detail = error.get("Message") if isinstance(error, dict) else None
        if not detail:
            detail = str(exc)
        detail = " ".join(str(detail).split())
        detail = re.sub(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", "[redacted]", detail)
        detail = re.sub(
            r"(?i)(secret|token|credential|key)(\s*[=:]\s*)\S+",
            r"\1\2[redacted]",
            detail,
        )[:240]
        return ProviderError(
            "Amazon Bedrock {} failed".format(operation),
            status_code=metadata.get("HTTPStatusCode"),
            error_code=error.get("Code") if isinstance(error, dict) else None,
            detail=detail or None,
        )

    def _converse(self, operation: str, instruction: str, payload: Mapping[str, Any]) -> Any:
        try:
            response = self._client.converse(
                **self._request_options(instruction, json.dumps(payload))
            )
            text = self._capture_response(response, operation)
            stop_reason = str(response.get("stopReason", "unknown"))
            if stop_reason in _SAFETY_STOP_REASONS:
                return TurnAnalysis(
                    safety_intervened=True,
                    safety_response=text
                    or "I'm sorry, but I can't help with that request.",
                )
            if not text:
                raise ProviderError(
                    "Amazon Bedrock {} returned no text".format(operation),
                    error_code="empty_model_output",
                )
            return text
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise self._safe_provider_error(operation, exc) from exc

    def identify_goals(
        self,
        message: str,
        catalog: Sequence[SkillRoutingDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> List[GoalMatch]:
        return self.understand_turn(message, catalog, context).goals

    def understand_turn(
        self,
        message: str,
        catalog: Sequence[SkillRoutingDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> TurnAnalysis:
        result = self._converse(
            "understand_turn",
            TURN_UNDERSTANDING_INSTRUCTION,
            turn_request_payload(message, catalog, context),
        )
        if isinstance(result, TurnAnalysis):
            return result
        try:
            return parse_turn_analysis(result, catalog, context)
        except Exception as exc:
            raise ProviderError(
                "Amazon Bedrock turn understanding returned invalid JSON",
                error_code="invalid_model_output",
                detail="{}".format(type(exc).__name__),
            ) from exc

    def generate_response(self, instruction: str, facts: Dict[str, Any]) -> str:
        result = self._converse(
            "generate_response",
            "Follow the response instruction using only the supplied facts. "
            "Never add financial facts or outcomes.",
            {"instruction": instruction, "facts": facts},
        )
        if isinstance(result, TurnAnalysis):
            return result.safety_response or "I'm sorry, but I can't help with that request."
        return result
