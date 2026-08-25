"""Offline provider used by tests and as a safe availability fallback."""

import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from member_assistant.catalog import SkillDefinition
from .base import GoalMatch, ModelProvider


class DeterministicProvider(ModelProvider):
    name = "deterministic"
    model_id = "deterministic-catalog-router"

    def __init__(
        self,
        *,
        fallback_from: str = "",
        fallback_reason: str = "",
    ) -> None:
        self._fallback_from = fallback_from
        self._fallback_reason = fallback_reason

    def observability_metadata(self) -> Dict[str, Any]:
        metadata = super().observability_metadata()
        if self._fallback_from:
            metadata.update(
                {
                    "fallback_used": True,
                    "configured_provider": self._fallback_from,
                    "fallback_reason": self._fallback_reason or "provider_unavailable",
                }
            )
        return metadata

    def identify_goals(
        self,
        message: str,
        catalog: Sequence[SkillDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> List[GoalMatch]:
        normalized = " ".join(message.lower().replace("’", "'").split())
        matches: List[GoalMatch] = []
        for skill in catalog:
            best_goal = None
            best_score = 0
            for goal in skill.supported_goals:
                keywords = [str(word).lower() for word in goal.get("keywords", [])]
                score = sum(1 for keyword in keywords if keyword in normalized)
                if score > best_score:
                    best_goal = str(goal["name"])
                    best_score = score
            if best_goal and best_score:
                matches.append(
                    GoalMatch(
                        skill_name=skill.name,
                        goal=best_goal,
                        confidence=min(0.99, 0.76 + best_score * 0.08),
                        inputs=self._extract_inputs(skill, message),
                    )
                )

        # A request for human support takes priority over all automated work.
        handoffs = [
            match
            for match in matches
            if next(
                (skill for skill in catalog if skill.name == match.skill_name), None
            ).risk_tier
            == "handoff"
        ]
        return handoffs[:1] if handoffs else matches

    def generate_response(self, instruction: str, facts: Dict[str, Any]) -> str:
        template = facts.get("template") or instruction
        try:
            return str(template).format(**facts)
        except (KeyError, ValueError):
            return str(instruction)

    def _extract_inputs(self, skill: SkillDefinition, message: str) -> Dict[str, Any]:
        normalized = message.lower()
        inputs: Dict[str, Any] = {}
        for field_name, rule in skill.input_extraction.items():
            strategy = rule["strategy"]
            if strategy == "full_message":
                inputs[field_name] = message.strip()
            elif strategy == "regex":
                match = re.search(str(rule["pattern"]), normalized)
                if match:
                    inputs[field_name] = match.group(int(rule.get("group", 1)))
            elif strategy == "alias":
                aliases = rule.get("aliases", {})
                if isinstance(aliases, list):
                    aliases = {alias: alias for alias in aliases}
                matched = next(
                    (
                        canonical
                        for alias, canonical in aliases.items()
                        if str(alias).lower() in normalized
                    ),
                    None,
                )
                if matched is not None:
                    inputs[field_name] = matched
        return inputs
