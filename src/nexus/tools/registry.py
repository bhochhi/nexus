from nexus.tools.base import Tool


class ToolRegistry:
    """Central registry mapping tool names to implementations."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]

    def list_tools(self) -> list[dict]:
        """Return tool definitions in the format expected by LLM tool calling."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]

    def list_by_domain(self, domain: str) -> list[dict]:
        """Return tools whose names start with the given domain prefix."""
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self._tools.values()
            if t.name.startswith(domain)
        ]
