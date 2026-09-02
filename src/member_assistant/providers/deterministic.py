"""Offline provider used by tests and as a safe availability fallback."""

import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from member_assistant.catalog import SkillRoutingDefinition
from .base import SkillGap, SkillMatch, ModelProvider, SlotUpdate, TurnAnalysis


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

    def identify_skills(
        self,
        message: str,
        catalog: Sequence[SkillRoutingDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> List[SkillMatch]:
        normalized = " ".join(message.lower().replace("’", "'").split())
        normalized_example = " ".join(re.findall(r"[a-z0-9]+", normalized))
        matches: List[SkillMatch] = []
        for skill in catalog:
            best_score = 0
            for goal in skill.supported_goals:
                keywords = [str(word).lower() for word in goal.get("keywords", [])]
                score = sum(1 for keyword in keywords if keyword in normalized)
                if score > best_score:
                    best_score = score
            for sample in skill.sample_utterances:
                sample_text = " ".join(
                    re.findall(
                        r"[a-z0-9]+",
                        str(sample.get("utterance", "")).casefold(),
                    )
                )
                if sample_text and sample_text == normalized_example:
                    best_score = max(best_score, 2)
            if best_score:
                matches.append(
                    SkillMatch(
                        skill_name=skill.name,
                        confidence=min(0.99, 0.76 + best_score * 0.08),
                        inputs=self.extract_inputs(skill, message),
                    )
                )

        if not matches and not (context or {}).get("active_skill"):
            prior_skill = next(
                (
                    skill
                    for skill in catalog
                    if skill.name == str((context or {}).get("last_selected_skill") or "")
                ),
                None,
            )
            inputs = self.extract_inputs(prior_skill, message) if prior_skill else {}
            if prior_skill and inputs:
                matches.append(
                    SkillMatch(
                        skill_name=prior_skill.name,
                        confidence=0.84,
                        inputs=inputs,
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

    def understand_turn(
        self,
        message: str,
        catalog: Sequence[SkillRoutingDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> TurnAnalysis:
        normalized = " ".join(message.lower().replace("’", "'").split())
        goals = self.identify_skills(message, catalog, context)
        active_name = str((context or {}).get("active_skill") or "")
        active = next((skill for skill in catalog if skill.name == active_name), None)
        extracted = self.extract_inputs(active, message) if active else {}
        # The offline fallback fills only the field currently being elicited. Broad
        # multi-slot interpretation belongs to a semantic provider; otherwise a
        # four-digit account suffix can be mistaken for a transfer amount.
        missing_field = str((context or {}).get("missing_field") or "")
        correction_cues = ("actually", "instead", "change", "correction")
        is_correction = any(cue in normalized for cue in correction_cues)
        slot_updates = []
        if active and active.archetype == "guided_resolution":
            slot_updates.extend(
                SlotUpdate(
                    field_name,
                    value,
                    1.0,
                    "pending_answer" if field_name == missing_field else "explicit",
                )
                for field_name, value in extracted.items()
            )
        elif missing_field and missing_field in extracted and not is_correction:
            slot_updates.append(
                SlotUpdate(
                    missing_field,
                    extracted[missing_field],
                    1.0,
                    "pending_answer",
                )
            )
        elif (
            active
            and missing_field
            and not is_correction
            and self._is_direct_pending_answer(normalized)
        ):
            # Offline/fallback mode can conservatively bind a direct reply to the
            # question it just asked. This limitation stays inside the provider
            # adapter; the runtime itself never assigns raw text to a slot.
            slot_updates.append(
                SlotUpdate(missing_field, message.strip(), 0.82, "pending_answer")
            )
        current_inputs = dict((context or {}).get("current_inputs") or {})
        for field_name, value in extracted.items():
            if current_inputs.get(field_name) not in {None, ""} and current_inputs.get(
                field_name
            ) != value and (not missing_field or field_name == missing_field or is_correction):
                slot_updates.append(SlotUpdate(field_name, value, 1.0, "correction"))
        return TurnAnalysis(
            skill_matches=goals,
            skill_gap=self._detect_skill_gap(normalized, goals),
            slot_updates=slot_updates,
            conversation_act="provide_information" if slot_updates else "unknown",
            active_goal_relation="continue" if slot_updates else "none",
            **self.classify_sentiment(normalized, context),
        )

    @staticmethod
    def _is_direct_pending_answer(normalized_message: str) -> bool:
        return normalized_message not in {
            "",
            "yes",
            "yes please",
            "no",
            "no thanks",
            "ok",
            "okay",
            "sure",
            "both",
            "hello",
            "hi",
            "hey",
        }

    @staticmethod
    def classify_sentiment(
        normalized_message: str,
        context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalized = " ".join(normalized_message.casefold().split())
        frustrated = (
            "not helping",
            "this is useless",
            "so frustrated",
            "i am frustrated",
            "terrible service",
            "ridiculous",
            "fed up",
            "angry",
            "third time",
        )
        negative = (
            "problem",
            "issue",
            "wrong",
            "worried",
            "concerned",
            "disappointed",
            "doesn't work",
            "does not work",
            "can't",
            "cannot",
        )
        positive = (
            "thank you",
            "thanks",
            "great",
            "perfect",
            "awesome",
            "appreciate",
            "helpful",
        )
        previous = str((context or {}).get("previous_sentiment") or "unknown")
        if any(phrase in normalized for phrase in frustrated):
            return {"sentiment": "frustrated", "sentiment_confidence": 0.96}
        if any(phrase in normalized for phrase in negative):
            confidence = 0.88 if previous in {"negative", "frustrated"} else 0.78
            return {"sentiment": "negative", "sentiment_confidence": confidence}
        if any(phrase in normalized for phrase in positive):
            return {"sentiment": "positive", "sentiment_confidence": 0.9}
        if len(normalized.split()) >= 3:
            return {"sentiment": "neutral", "sentiment_confidence": 0.7}
        return {"sentiment": "unknown", "sentiment_confidence": 0.25}

    @staticmethod
    def _detect_skill_gap(
        normalized_message: str, goals: Sequence[SkillMatch]
    ) -> Optional[SkillGap]:
        """Recognize a small set of unambiguous safety-critical capability gaps.

        This gives the offline demo the same safe behavior as a semantic provider
        for fraud reporting. It does not route or answer the request; the runtime
        records the gap and offers the governed human-support capability.
        """

        if goals:
            return None
        fraud_phrases = (
            "report fraud",
            "report a fraud",
            "report fraudulent",
            "fraudulent charge",
            "fraudulent transaction",
            "someone used my card",
            "card was used without",
        )
        if any(phrase in normalized_message for phrase in fraud_phrases):
            return SkillGap(
                objective="report suspected fraud",
                category="fraud_reporting",
                confidence=0.99,
            )
        return None

    def generate_response(self, instruction: str, facts: Dict[str, Any]) -> str:
        template = facts.get("template") or instruction
        try:
            return str(template).format(**facts)
        except (KeyError, ValueError):
            return str(instruction)

    def extract_inputs(
        self, skill: SkillRoutingDefinition, message: str
    ) -> Dict[str, Any]:
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
