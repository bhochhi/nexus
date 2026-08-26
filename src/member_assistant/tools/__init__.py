"""Replaceable mock integration adapters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

from .accounts import MockAccountTool
from .handoff import MockHandoffTool
from .knowledge import LocalKnowledgeTool
from .member_profile import MockMemberProfileTool
from .navigation import MockNavigationTool
from .transfer import MockTransferTool


@dataclass
class MockTools:
    accounts: MockAccountTool
    knowledge: LocalKnowledgeTool
    transfers: MockTransferTool
    navigation: MockNavigationTool
    handoff: MockHandoffTool
    member_profile: MockMemberProfileTool

    def __post_init__(self):
        self._registry = {
            tool.name: tool
            for tool in (
                self.accounts,
                self.knowledge,
                self.transfers,
                self.navigation,
                self.handoff,
                self.member_profile,
            )
        }

    def invoke(self, tool_name: str, action: str, arguments: Dict[str, Any]) -> Any:
        tool = self._registry.get(tool_name)
        if not tool:
            raise ValueError("Tool is not registered: {}".format(tool_name))
        return tool.invoke(action, arguments)

    def has(self, tool_name: str) -> bool:
        return tool_name in self._registry

    def supports(self, tool_name: str, action: str) -> bool:
        tool = self._registry.get(tool_name)
        return bool(tool and action in getattr(tool, "actions", ()))

    def contracts(self) -> Dict[str, Tuple[str, ...]]:
        """Return the stable dependency manifest exposed to skill publishers."""

        return {
            name: tuple(getattr(tool, "actions", ()))
            for name, tool in sorted(self._registry.items())
        }

    @classmethod
    def create(cls, knowledge_path: Path) -> "MockTools":
        accounts = MockAccountTool()
        return cls(
            accounts=accounts,
            knowledge=LocalKnowledgeTool(knowledge_path),
            transfers=MockTransferTool(accounts),
            navigation=MockNavigationTool(),
            handoff=MockHandoffTool(),
            member_profile=MockMemberProfileTool(),
        )


__all__ = ["MockTools"]
