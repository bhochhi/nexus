"""Provider construction and safe fallback behavior."""

from typing import Any, Dict, List, Mapping, Optional, Sequence

from member_assistant.catalog import SkillDefinition
from member_assistant.config import Settings
from .base import GoalAnalysis, GoalMatch, ModelProvider, ProviderError
from .deterministic import DeterministicProvider


class FallbackProvider(ModelProvider):
    def __init__(self, primary: ModelProvider, fallback: ModelProvider):
        self.primary = primary
        self.fallback = fallback
        self.name = primary.name
        self.model_id = primary.model_id
        self._last_call_metadata: Dict[str, Any] = self.primary.observability_metadata()

    def observability_metadata(self) -> Dict[str, Any]:
        return dict(self._last_call_metadata)

    @staticmethod
    def _failure_metadata(exc: ProviderError) -> Dict[str, Any]:
        return {
            "failure_type": type(exc).__name__,
            **exc.error_metadata(),
        }

    def identify_goals(
        self,
        message: str,
        catalog: Sequence[SkillDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> List[GoalMatch]:
        try:
            result = self.primary.identify_goals(message, catalog, context)
            self._last_call_metadata = self.primary.observability_metadata()
            return result
        except ProviderError as exc:
            result = self.fallback.identify_goals(message, catalog, context)
            self._last_call_metadata = {
                **self.fallback.observability_metadata(),
                "fallback_used": True,
                "configured_provider": self.primary.name,
                **self._failure_metadata(exc),
            }
            return result

    def analyze_message(
        self,
        message: str,
        catalog: Sequence[SkillDefinition],
        context: Optional[Mapping[str, Any]] = None,
    ) -> GoalAnalysis:
        try:
            result = self.primary.analyze_message(message, catalog, context)
            self._last_call_metadata = self.primary.observability_metadata()
            return result
        except ProviderError as exc:
            result = self.fallback.analyze_message(message, catalog, context)
            self._last_call_metadata = {
                **self.fallback.observability_metadata(),
                "fallback_used": True,
                "configured_provider": self.primary.name,
                **self._failure_metadata(exc),
            }
            return result

    def generate_response(self, instruction: str, facts: Dict[str, Any]) -> str:
        try:
            result = self.primary.generate_response(instruction, facts)
            self._last_call_metadata = self.primary.observability_metadata()
            return result
        except ProviderError as exc:
            result = self.fallback.generate_response(instruction, facts)
            self._last_call_metadata = {
                **self.fallback.observability_metadata(),
                "fallback_used": True,
                "configured_provider": self.primary.name,
                **self._failure_metadata(exc),
            }
            return result


def build_provider(settings: Settings) -> ModelProvider:
    if settings.provider_name in {"mock", "deterministic"}:
        return DeterministicProvider()
    if settings.provider_name == "openai":
        fallback = DeterministicProvider()
        if not settings.provider_api_key:
            if settings.allow_provider_fallback:
                return DeterministicProvider(
                    fallback_from="openai", fallback_reason="missing_api_key"
                )
            raise ProviderError("OPENAI_API_KEY or MODEL_API_KEY is required")
        from .openai_provider import OpenAIProvider

        primary = OpenAIProvider(
            settings.model_id,
            settings.provider_api_key,
            reasoning_effort=settings.model_reasoning_effort,
        )
        return FallbackProvider(primary, fallback) if settings.allow_provider_fallback else primary
    raise ProviderError("Unsupported MODEL_PROVIDER: {}".format(settings.provider_name))
