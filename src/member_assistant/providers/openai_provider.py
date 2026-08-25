"""OpenAI adapter. No OpenAI types escape this module."""

import json
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from member_assistant.catalog import SkillDefinition
from .base import GoalAnalysis, GoalMatch, ModelProvider, ProviderError, SkillGap


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
        catalog: Sequence[SkillDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> List[GoalMatch]:
        return self.analyze_message(message, catalog, context).goals

    def analyze_message(
        self,
        message: str,
        catalog: Sequence[SkillDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> GoalAnalysis:
        choices = [
            {
                "skill_name": skill.name,
                "description": skill.description,
                "goals": [goal["name"] for goal in skill.supported_goals],
                "input_properties": list(skill.input_schema.get("properties", {}).keys()),
            }
            for skill in catalog
        ]
        instruction = (
            "Understand the member's objectives. Return JSON only as "
            "{\"goals\":[{\"skill_name\":str,\"goal\":str,\"confidence\":number,"
            "\"inputs\":object}],\"skill_gap\":null|{\"objective\":str,\"category\":str,"
            "\"confidence\":number}}. Use only the supplied skills for goals. Do not infer "
            "financial data. An empty goals list is valid. Omit candidates with no evidence; "
            "never return zero-confidence placeholders. If conversation_context says the "
            "assistant is awaiting an input, a plausible answer to that question is not a new "
            "goal or skill gap. Return multiple goals only when the member independently "
            "requested each goal or when the utterance is genuinely ambiguous between them. "
            "Set skill_gap only when the member expresses a clear objective that none of the "
            "supplied skills supports. Do not use skill_gap for greetings, small talk, unclear "
            "fragments, or plausible slot answers. Write objective as a short sanitized verb "
            "phrase that grammatically completes 'you would like to ___'; remove names, account "
            "numbers, amounts, and other identifiers. Write category as a stable lower_snake_case "
            "business capability label."
        )
        try:
            response = self._client.responses.create(
                **self._request_options(json_output=True),
                instructions=instruction,
                input=json.dumps(
                    {
                        "skills": choices,
                        "member_message": message,
                        "conversation_context": dict(context or {}),
                    }
                ),
            )
            self._capture_usage(response, "analyze_message")
            content = response.output_text or "{}"
            parsed = json.loads(content)
            allowed = {skill.name for skill in catalog}
            goals = [
                GoalMatch(
                    skill_name=item["skill_name"],
                    goal=item["goal"],
                    confidence=float(item.get("confidence", 0.0)),
                    inputs=dict(item.get("inputs", {})),
                )
                for item in parsed.get("goals", [])
                if item.get("skill_name") in allowed
            ]
            raw_gap = parsed.get("skill_gap")
            skill_gap = None
            if isinstance(raw_gap, dict):
                objective = " ".join(str(raw_gap.get("objective", "")).split())[:160]
                category = str(raw_gap.get("category", "")).strip().casefold()
                confidence = float(raw_gap.get("confidence", 0.0))
                if (
                    objective
                    and category
                    and all(character.isalnum() or character == "_" for character in category)
                ):
                    skill_gap = SkillGap(
                        objective=objective,
                        category=category[:80],
                        confidence=max(0.0, min(1.0, confidence)),
                    )
            return GoalAnalysis(goals=goals, skill_gap=skill_gap)
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise self._safe_provider_error("goal extraction", exc) from exc

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
