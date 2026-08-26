"""OpenAI adapter. No OpenAI types escape this module."""

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


class OpenAIProvider(ModelProvider):
    def __init__(self, model_id: str, api_key: str, reasoning_effort: str = "low"):
        if not api_key:
            raise ProviderError("OPENAI_API_KEY or MODEL_API_KEY is not configured")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - packaging guard
            raise ProviderError("The openai package is not installed") from exc
        self._client = OpenAI(api_key=api_key)
        self._model_id = model_id
        self._reasoning_effort = reasoning_effort
        self.model_id = model_id
        self.name = "openai"
        self._last_call_metadata: Dict[str, Any] = {
            "provider": self.name,
            "model": self.model_id,
            "api_endpoint": "responses",
            "reasoning_effort": self._effective_reasoning_effort(),
            "fallback_used": False,
        }

    def observability_metadata(self) -> Dict[str, Any]:
        return dict(self._last_call_metadata)

    def _capture_usage(self, response: Any, operation: str) -> None:
        usage = getattr(response, "usage", None)
        self._last_call_metadata = {
            "provider": self.name,
            "model": self.model_id,
            "operation": operation,
            "api_endpoint": "responses",
            "reasoning_effort": self._effective_reasoning_effort(),
            "fallback_used": False,
        }
        if usage is not None:
            self._last_call_metadata.update(
                {
                    "input_tokens": getattr(
                        usage, "input_tokens", getattr(usage, "prompt_tokens", None)
                    ),
                    "output_tokens": getattr(
                        usage,
                        "output_tokens",
                        getattr(usage, "completion_tokens", None),
                    ),
                    "total_tokens": getattr(usage, "total_tokens", None),
                }
            )

    def _supports_reasoning(self) -> bool:
        model = self._model_id.casefold()
        return model.startswith("gpt-5") or model.startswith(("o1", "o3", "o4"))

    def _effective_reasoning_effort(self) -> str:
        return self._reasoning_effort if self._supports_reasoning() else "not_applicable"

    def _request_options(self, *, json_output: bool = False) -> Dict[str, Any]:
        options: Dict[str, Any] = {
            "model": self._model_id,
            "store": False,
        }
        if self._supports_reasoning():
            options["reasoning"] = {"effort": self._reasoning_effort}
        if json_output:
            options["text"] = {"format": {"type": "json_object"}}
        return options

    @staticmethod
    def _safe_provider_error(operation: str, exc: Exception) -> ProviderError:
        """Keep useful API diagnostics while redacting credentials and long payloads."""

        body = getattr(exc, "body", None)
        error = body.get("error", body) if isinstance(body, dict) else {}
        detail = error.get("message") if isinstance(error, dict) else None
        if not detail:
            detail = str(exc)
        detail = " ".join(str(detail).split())
        detail = re.sub(r"(?i)bearer\s+\S+", "Bearer [redacted]", detail)
        detail = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted]", detail)[:240]
        return ProviderError(
            "OpenAI {} failed".format(operation),
            status_code=getattr(exc, "status_code", None),
            error_code=(error.get("code") if isinstance(error, dict) else None),
            parameter=(error.get("param") if isinstance(error, dict) else None),
            detail=detail or None,
        )

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
        try:
            response = self._client.responses.create(
                **self._request_options(json_output=True),
                instructions=TURN_UNDERSTANDING_INSTRUCTION,
                input=json.dumps(turn_request_payload(message, catalog, context)),
            )
            self._capture_usage(response, "understand_turn")
            return parse_turn_analysis(
                response.output_text or "{}", catalog, context
            )
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise self._safe_provider_error("turn understanding", exc) from exc

    def generate_response(self, instruction: str, facts: Dict[str, Any]) -> str:
        try:
            response = self._client.responses.create(
                **self._request_options(),
                instructions=(
                    "Follow the response instruction using only the supplied facts. "
                    "Never add financial facts or outcomes."
                ),
                input=json.dumps({"instruction": instruction, "facts": facts}),
            )
            self._capture_usage(response, "generate_response")
            return response.output_text or instruction
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise self._safe_provider_error("response generation", exc) from exc
