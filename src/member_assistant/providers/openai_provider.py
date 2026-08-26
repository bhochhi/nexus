"""OpenAI adapter. No OpenAI types escape this module."""

import json
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from member_assistant.catalog import SkillRoutingDefinition
from .base import (
    GoalMatch,
    ModelProvider,
    ProviderError,
    SkillGap,
    SlotUpdate,
    TurnAnalysis,
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
        choices = [
            {
                "skill_name": skill.name,
                "description": skill.description,
                "goals": [
                    {
                        "name": goal["name"],
                        "display_name": goal.get("display_name", goal["name"]),
                    }
                    for goal in skill.supported_goals
                ],
                "input_schema": skill.input_schema,
            }
            for skill in catalog
        ]
        instruction = (
            "Understand the member's complete conversational turn. Return JSON only as "
            "{\"goals\":[{\"skill_name\":str,\"goal\":str,\"confidence\":number,"
            "\"inputs\":object}],\"slot_updates\":[{\"field\":str,\"value\":any,"
            "\"confidence\":number}],\"conversation_act\":str,"
            "\"active_goal_relation\":str,\"skill_gap\":null|{\"objective\":str,"
            "\"category\":str,\"confidence\":number}}. Use only the supplied skills for "
            "goals. Do not infer "
            "financial data. Each returned goal must exactly equal one supplied "
            "goals[].name value; never return its display_name. An empty goals list is "
            "valid. Omit candidates with no evidence; "
            "never return zero-confidence placeholders. If conversation_context says the "
            "assistant has an active task, interpret the utterance relative to that task. Put "
            "every explicitly supplied or corrected active-task input in slot_updates, even "
            "when more than one value appears and even when a different field was asked for. "
            "Use only fields from the active skill's input_schema. Distinguish source and "
            "destination using the member's wording. Normalize an unambiguous monetary amount "
            "written in words to a plain decimal-number string, such as 'two hundred' to "
            "'200.00'. Never treat a masked account suffix or identifier as an amount unless "
            "the member explicitly describes it as money. Give each slot update a calibrated "
            "confidence from 0 to 1. Do not guess an ambiguous value. A plausible task answer "
            "is not a new goal or skill gap. Put inputs on a goal candidate only for a newly "
            "requested goal. "
            "Return multiple goals only when the member independently "
            "requested each goal or when the utterance is genuinely ambiguous between them. "
            "conversation_act must be one of provide_information, correction, confirmation, "
            "new_goal, clarification_request, greeting, small_talk, or unknown. "
            "active_goal_relation must be continue, replace, ambiguous, or none. "
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
                        "output_requirement": "Return valid JSON only.",
                        "skills": choices,
                        "member_message": message,
                        "conversation_context": dict(context or {}),
                    }
                ),
            )
            self._capture_usage(response, "understand_turn")
            content = response.output_text or "{}"
            parsed = json.loads(content)
            skills_by_name = {skill.name: skill for skill in catalog}
            goals = []
            for item in parsed.get("goals", []):
                if not isinstance(item, dict):
                    continue
                skill = skills_by_name.get(str(item.get("skill_name", "")))
                if skill is None:
                    continue
                allowed_inputs = set(
                    skill.input_schema.get("properties", {}).keys()
                )
                inputs = item.get("inputs", {})
                goals.append(
                    GoalMatch(
                        skill_name=skill.name,
                        goal=str(item.get("goal", "")),
                        confidence=float(item.get("confidence", 0.0)),
                        inputs={
                            str(key): value
                            for key, value in (
                                inputs.items() if isinstance(inputs, dict) else []
                            )
                            if key in allowed_inputs
                            and value is not None
                            and value != ""
                        },
                    )
                )
            context_value = dict(context or {})
            active = skills_by_name.get(str(context_value.get("active_skill") or ""))
            active_fields = (
                set(active.input_schema.get("properties", {}).keys())
                if active
                else set()
            )
            slot_updates = []
            for item in parsed.get("slot_updates", []):
                if not isinstance(item, dict):
                    continue
                field_name = str(item.get("field", ""))
                value = item.get("value")
                if field_name not in active_fields or value is None or value == "":
                    continue
                slot_updates.append(
                    SlotUpdate(
                        field=field_name,
                        value=value,
                        confidence=max(
                            0.0, min(1.0, float(item.get("confidence", 0.0)))
                        ),
                    )
                )
            allowed_acts = {
                "provide_information",
                "correction",
                "confirmation",
                "new_goal",
                "clarification_request",
                "greeting",
                "small_talk",
                "unknown",
            }
            conversation_act = (
                str(parsed.get("conversation_act", "unknown")).strip().casefold()
            )
            if conversation_act not in allowed_acts:
                conversation_act = "unknown"
            active_goal_relation = (
                str(parsed.get("active_goal_relation", "none")).strip().casefold()
            )
            if active_goal_relation not in {"continue", "replace", "ambiguous", "none"}:
                active_goal_relation = "none"
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
            return TurnAnalysis(
                goals=goals,
                skill_gap=skill_gap,
                slot_updates=slot_updates,
                conversation_act=conversation_act,
                active_goal_relation=active_goal_relation,
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
