"""Routes every predefined skill type through one declarative interpreter."""

from typing import Dict, Iterable, Optional

from member_assistant.catalog import BUILTIN_ARCHETYPES
from .base import SkillExecutor
from .declarative import DeclarativeSkillExecutor


class SkillExecutorRegistry:
    def __init__(self, executors: Optional[Iterable[SkillExecutor]] = None):
        self._default_executor = DeclarativeSkillExecutor()
        implementations = tuple(executors or (self._default_executor,))
        self._executors: Dict[str, SkillExecutor] = {}
        for executor in implementations:
            for archetype in executor.archetypes:
                self._executors[archetype] = executor

    def get(self, archetype: str) -> Optional[SkillExecutor]:
        # Published archetypes can reuse the governed declarative operation set
        # without requiring a runtime release.
        return self._executors.get(archetype, self._default_executor)

    @property
    def supported_archetypes(self):
        return frozenset(self._executors).intersection(BUILTIN_ARCHETYPES)
