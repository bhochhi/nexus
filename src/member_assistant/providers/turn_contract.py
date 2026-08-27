"""Provider-neutral prompt and parser for conversational turn understanding."""

import json
from typing import Any, Dict, Mapping, Optional, Sequence

from member_assistant.catalog import SkillRoutingDefinition
from .base import GoalMatch, SkillGap, SlotUpdate, TurnAnalysis


TURN_UNDERSTANDING_INSTRUCTION = (
    "Understand the member's complete conversational turn. Return JSON only as "
    "{\"goals\":[{\"skill_name\":str,\"goal\":str,\"confidence\":number,"
    "\"inputs\":object}],\"slot_updates\":[{\"field\":str,\"value\":any,"
    "\"confidence\":number}],\"conversation_act\":str,"
    "\"active_goal_relation\":str,\"sentiment\":str,"
    "\"sentiment_confidence\":number,\"skill_gap\":null|{\"objective\":str,"
    "\"category\":str,\"confidence\":number}}. Use only the supplied skills for "
    "goals. Do not infer financial data. Each returned goal must exactly equal one "
    "supplied goals[].name value; never return its display_name. An empty goals list "
    "is valid. Omit candidates with no evidence; never return zero-confidence "
    "placeholders. If conversation_context says the assistant has an active task, "
    "interpret the utterance relative to that task. Put every explicitly supplied or "
    "corrected active-task input in slot_updates, even when more than one value appears "
    "and even when a different field was asked for. Use only fields from the active "
    "skill's input_schema. Distinguish source and destination using the member's wording. "
    "Normalize an unambiguous monetary amount written in words to a plain decimal-number "
    "string, such as 'two hundred' to '200.00'. Never treat a masked account suffix or "
    "identifier as an amount unless the member explicitly describes it as money. Be "
    "tolerant of obvious speech-recognition disfluencies and number morphology when the "
    "active missing field is an amount: 'one hundred dollars', 'one hundreds dollar', and "
    "'a hundred bucks' all unambiguously mean '100.00'; 'two hundreds' means '200.00'. "
    "Ask for clarification rather than guessing only when more than one numeric meaning is "
    "plausible. Give "
    "each slot update a calibrated confidence from 0 to 1. Do not guess an ambiguous "
    "value. A plausible task answer is not a new goal or skill gap. Put inputs on a goal "
    "candidate only for a newly requested goal. Return multiple goals only when the "
    "member independently requested each goal or when the utterance is genuinely "
    "ambiguous between them. conversation_act must be one of provide_information, "
    "correction, confirmation, new_goal, clarification_request, greeting, small_talk, "
    "or unknown. active_goal_relation must be continue, replace, ambiguous, or none. "
    "sentiment must be positive, neutral, negative, frustrated, or unknown. Classify "
    "the member's current emotional state from this utterance and the supplied recent "
    "sentiment context. Use frustrated for clear anger, repeated unresolved difficulty, "
    "or strong dissatisfaction; negative for concern or dissatisfaction without strong "
    "frustration; neutral for ordinary task-focused language; positive for clear positive "
    "affect; and unknown only when there is not enough evidence. Return a calibrated "
    "sentiment_confidence from 0 to 1. "
    "Set skill_gap only when the member expresses a clear objective that none of the "
    "supplied skills supports. Do not use skill_gap for greetings, small talk, unclear "
    "fragments, or plausible slot answers. Write objective as a short sanitized verb "
    "phrase that grammatically completes 'you would like to ___'; remove names, account "
    "numbers, amounts, and other identifiers. Write category as a stable lower_snake_case "
    "business capability label."
)


def turn_request_payload(
    message: str,
    catalog: Sequence[SkillRoutingDefinition],
    context: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the same bounded semantic request for every model provider."""

    return {
        "output_requirement": "Return valid JSON only.",
        "skills": [
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
        ],
        "member_message": message,
        "conversation_context": dict(context or {}),
    }


def parse_json_object(content: str) -> Dict[str, Any]:
    """Decode a JSON object, tolerating a provider's optional Markdown fence."""

    text = (content or "").strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        last_fence = text.rfind("```")
        if first_newline >= 0 and last_fence > first_newline:
            text = text[first_newline + 1 : last_fence].strip()
    parsed = json.loads(text or "{}")
    if not isinstance(parsed, dict):
        raise ValueError("turn-understanding response must be a JSON object")
    return parsed


def parse_turn_analysis(
    content: str,
    catalog: Sequence[SkillRoutingDefinition],
    context: Optional[Mapping[str, Any]] = None,
) -> TurnAnalysis:
    """Validate model output against only the currently supplied skill contracts."""

    parsed = parse_json_object(content)
    skills_by_name = {skill.name: skill for skill in catalog}
    goals = []
    for item in parsed.get("goals", []):
        if not isinstance(item, dict):
            continue
        skill = skills_by_name.get(str(item.get("skill_name", "")))
        if skill is None:
            continue
        allowed_inputs = set(skill.input_schema.get("properties", {}).keys())
        inputs = item.get("inputs", {})
        try:
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        goals.append(
            GoalMatch(
                skill_name=skill.name,
                goal=str(item.get("goal", "")),
                confidence=max(0.0, min(1.0, confidence)),
                inputs={
                    str(key): value
                    for key, value in (
                        inputs.items() if isinstance(inputs, dict) else []
                    )
                    if key in allowed_inputs and value is not None and value != ""
                },
            )
        )

    active = skills_by_name.get(str(dict(context or {}).get("active_skill") or ""))
    active_fields = (
        set(active.input_schema.get("properties", {}).keys()) if active else set()
    )
    slot_updates = []
    for item in parsed.get("slot_updates", []):
        if not isinstance(item, dict):
            continue
        field_name = str(item.get("field", ""))
        value = item.get("value")
        if field_name not in active_fields or value is None or value == "":
            continue
        try:
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        slot_updates.append(
            SlotUpdate(
                field=field_name,
                value=value,
                confidence=max(0.0, min(1.0, confidence)),
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
    conversation_act = str(parsed.get("conversation_act", "unknown")).strip().casefold()
    if conversation_act not in allowed_acts:
        conversation_act = "unknown"
    active_goal_relation = str(
        parsed.get("active_goal_relation", "none")
    ).strip().casefold()
    if active_goal_relation not in {"continue", "replace", "ambiguous", "none"}:
        active_goal_relation = "none"

    sentiment = str(parsed.get("sentiment", "unknown")).strip().casefold()
    if sentiment not in {"positive", "neutral", "negative", "frustrated", "unknown"}:
        sentiment = "unknown"
    try:
        sentiment_confidence = float(parsed.get("sentiment_confidence", 0.0))
    except (TypeError, ValueError):
        sentiment_confidence = 0.0

    raw_gap = parsed.get("skill_gap")
    skill_gap = None
    if isinstance(raw_gap, dict):
        objective = " ".join(str(raw_gap.get("objective", "")).split())[:160]
        category = str(raw_gap.get("category", "")).strip().casefold()
        try:
            confidence = float(raw_gap.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
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
        sentiment=sentiment,
        sentiment_confidence=max(0.0, min(1.0, sentiment_confidence)),
    )
