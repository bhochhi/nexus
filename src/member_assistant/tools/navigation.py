"""Approved navigation-link adapter."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class NavigationResult:
    destination: str
    url: str


class MockNavigationTool:
    name = "mock_approved_navigation"

    def open_destination(self, destination: str) -> NavigationResult:
        if destination != "online_id_recovery":
            raise ValueError("Destination is not approved")
        return NavigationResult(
            destination=destination,
            url="https://example.test/member/online-id-recovery",
        )

    def invoke(self, action: str, arguments: Dict[str, Any]) -> Any:
        if action != "open_destination":
            raise ValueError("Unsupported mock navigation action: {}".format(action))
        result = self.open_destination(str(arguments["destination"]))
        return {"destination": result.destination, "url": result.url}
