"""Stable contract that insulates the runtime and skills from model vendors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

from member_assistant.catalog import SkillRoutingDefinition


class ProviderError(RuntimeError):
    """A provider failure with bounded, non-secret troubleshooting metadata."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        parameter: Optional[str] = None,
        detail: Optional[str] = None,
        fallback_allowed: bool = True,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.parameter = parameter
        self.detail = detail
        self.fallback_allowed = fallback_allowed
        parts = [message]
        if status_code is not None:
            parts.append("status={}".format(status_code))
        if error_code:
            parts.append("code={}".format(error_code))
        if parameter:
            parts.append("parameter={}".format(parameter))
        if detail:
            parts.append("detail={}".format(detail))
        super().__init__("; ".join(parts))

    def error_metadata(self) -> Dict[str, Any]:
        """Return safe fields that can be attached to a fallback trace."""

        return {
            key: value
            for key, value in {
                "provider_status": self.status_code,
                "provider_error_code": self.error_code,
                "provider_error_param": self.parameter,
            }.items()
            if value is not None
        }


class ProviderSafetyError(ProviderError):
    """A provider safety decision that another provider must not bypass."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs["fallback_allowed"] = False
        super().__init__(message, **kwargs)


@dataclass(frozen=True)
class GoalMatch:
    skill_name: str
    goal: str
    confidence: float
    inputs: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "goal": self.goal,
            "confidence": self.confidence,
            "inputs": dict(self.inputs),
        }


@dataclass(frozen=True)
class SkillGap:
    """A clear member objective that no currently installed skill supports."""

    objective: str
    category: str
    confidence: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "objective": self.objective,
            "category": self.category,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class SlotUpdate:
    """One model-interpreted active-task input with bounded confidence."""

    field: str
    value: Any
    confidence: float


@dataclass(frozen=True)
class TurnAnalysis:
    """Provider-neutral semantic interpretation of one member turn."""

    goals: List[GoalMatch] = field(default_factory=list)
    skill_gap: Optional[SkillGap] = None
    slot_updates: List[SlotUpdate] = field(default_factory=list)
    conversation_act: str = "unknown"
    active_goal_relation: str = "none"
    safety_intervened: bool = False
    safety_response: Optional[str] = None


class ModelProvider(ABC):
    """All provider-specific behavior is constrained to implementations here."""

    name = "unknown"
    model_id = "unknown"

    def observability_metadata(self) -> Dict[str, Any]:
        """Describe the most recent call without exposing prompt content."""

        return {"provider": self.name, "model": self.model_id, "fallback_used": False}

    def understand_turn(
        self,
        message: str,
        catalog: Sequence[SkillRoutingDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> TurnAnalysis:
        """Understand objectives, task-relative inputs, and optional gaps.

        Offline providers can return only goal matches. Semantic providers can additionally
        extract every supplied or corrected input for the active task. Execution, validation,
        and confirmation remain outside this contract.
        """

        return TurnAnalysis(goals=self.identify_goals(message, catalog, context))

    @abstractmethod
    def identify_goals(
        self,
        message: str,
        catalog: Sequence[SkillRoutingDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> List[GoalMatch]:
        raise NotImplementedError

    @abstractmethod
    def generate_response(self, instruction: str, facts: Dict[str, Any]) -> str:
        raise NotImplementedError
