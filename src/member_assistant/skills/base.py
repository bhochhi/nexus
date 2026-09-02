"""Common contracts for skill implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from member_assistant.catalog import SkillDefinition
from member_assistant.observability import Observability
from member_assistant.providers.base import ModelProvider
from member_assistant.tools import MockTools


@dataclass
class SkillContext:
    definition: SkillDefinition
    session_id: str
    member_ref: str
    authenticated: bool
    authorizations: List[str]
    confirmation_status: str
    tools: MockTools
    provider: ModelProvider
    observability: Observability
    member_profile: Dict[str, Any] = field(default_factory=dict)
    execution_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    status: str
    response: str
    inputs: Dict[str, Any]
    missing_field: Optional[str] = None
    pending_question: Optional[str] = None
    outcome: Optional[Dict[str, Any]] = None
    completed_steps: List[str] = field(default_factory=list)


class SkillExecutor(ABC):
    archetypes: Tuple[str, ...] = ()

    def required_tools(self, definition: SkillDefinition) -> Tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                step["tool"]
                for step in definition.workflow.get("steps", [])
                if step.get("op") == "call_tool"
            )
        )

    @abstractmethod
    def execute(self, task: Dict[str, Any], context: SkillContext) -> SkillResult:
        raise NotImplementedError
