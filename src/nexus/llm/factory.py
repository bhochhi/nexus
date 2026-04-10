from nexus.config import settings
from nexus.llm.base import BaseLLM
from nexus.llm.bedrock import BedrockLLM


class LLMFactory:
    """Factory for creating LLM instances based on provider config."""

    @staticmethod
    def create(
        provider: str | None = None,
        model_id: str | None = None,
        **kwargs,
    ) -> BaseLLM:
        provider = provider or settings.llm_provider
        model_id = model_id or settings.bedrock_model_id

        if provider == "bedrock":
            region = kwargs.get("region", settings.aws_region)
            return BedrockLLM(model_id=model_id, region=region)

        raise ValueError(f"Unsupported LLM provider: {provider}")
