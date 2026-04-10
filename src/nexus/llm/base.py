from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model_id: str):
        self.model_id = model_id

    @abstractmethod
    def invoke(self, prompt: str, system_prompt: str | None = None) -> str:
        """Send a prompt to the LLM and return the response text."""

    @abstractmethod
    def invoke_with_tools(
        self,
        prompt: str,
        tools: list[dict],
        system_prompt: str | None = None,
    ) -> dict:
        """Send a prompt with tool definitions. Returns structured response."""
