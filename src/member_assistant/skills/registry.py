"""Routes every predefined skill type through one declarative interpreter."""

from typing import Dict, Iterable, Optional

from member_assistant.catalog import SKILL_TYPES
from .base import SkillExecutor
from .declarative import DeclarativeSkillExecutor


class SkillExecutorRegistry:
    def __init__(self, executors: Optional[Iterable[SkillExecutor]] = None):
        self._default_executor = DeclarativeSkillExecutor()
        implementations = tuple(executors or (self._default_executor,))
        self._executors: Dict[str, SkillExecutor] = {}
        for executor in implementations:
            for skill_type in executor.skill_types:
                self._executors[skill_type] = executor

    def get(self, skill_type: str) -> Optional[SkillExecutor]:
        # Published archetypes can reuse the governed declarative operation set
        # without requiring a runtime release.
        return self._executors.get(skill_type, self._default_executor)

    @property
    def supported_types(self):
        return frozenset(self._executors).intersection(SKILL_TYPES)
