from typing import Protocol, runtime_checkable


@runtime_checkable
class Tool(Protocol):
    """Protocol for tool implementations."""

    name: str
    description: str
    parameters: dict

    def execute(self, args: dict) -> dict: ...
