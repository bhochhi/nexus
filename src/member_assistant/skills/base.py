"""Common contracts for skill implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import re
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

    def collect_input(self, task: Dict[str, Any], message: str, context: SkillContext) -> None:
        field_name = task.get("missing_field")
        if field_name:
            value = message.strip()
            field_schema = (
                context.definition.input_schema.get("properties", {}).get(
                    field_name, {}
                )
            )
            rule = context.definition.input_extraction.get(field_name, {})
            strategy = rule.get("strategy")
            if strategy == "regex":
                match = re.search(str(rule.get("pattern", "")), message.lower())
                if match:
                    value = match.group(int(rule.get("group", 1)))
            elif strategy == "alias":
                aliases = rule.get("aliases", {})
                if isinstance(aliases, list):
                    aliases = {alias: alias for alias in aliases}
                normalized = message.casefold()
                matched = next(
                    (
                        canonical
                        for alias, canonical in aliases.items()
                        if str(alias).casefold() in normalized
                    ),
                    None,
                )
                if matched is not None:
                    value = str(matched)
            pattern = field_schema.get("pattern") if isinstance(field_schema, dict) else None
            if pattern and not re.fullmatch(str(pattern), value):
                # A semantic provider may decline to interpret malformed natural
                # language. Do not turn that raw phrase into a misleading workflow
                # validation error; leave the field missing so it is elicited again.
                return
            task.setdefault("inputs", {})[field_name] = value

    @abstractmethod
    def execute(self, task: Dict[str, Any], context: SkillContext) -> SkillResult:
        raise NotImplementedError
