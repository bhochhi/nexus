"""Model-provider adapters."""

from .base import GoalAnalysis, GoalMatch, ModelProvider, ProviderError, SkillGap
from .deterministic import DeterministicProvider
from .factory import build_provider

__all__ = [
    "GoalAnalysis",
    "GoalMatch",
    "ModelProvider",
    "ProviderError",
    "SkillGap",
    "DeterministicProvider",
    "build_provider",
]
