"""Synthetic member-profile adapter used for conversational personalization."""

from typing import Any, Dict


class MockMemberProfileTool:
    name = "mock_member_profile"

    def __init__(self) -> None:
        self._profiles = {
            "mock-member-001": {
                "member_ref": "mock-member-001",
                "first_name": "Jordan",
                "preferred_name": "Jordan",
            }
        }

    def invoke(self, action: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if action != "get":
            raise ValueError("Unsupported mock member-profile action: {}".format(action))
        member_ref = str(arguments["member_ref"])
        return dict(
            self._profiles.get(
                member_ref,
                {
                    "member_ref": member_ref,
                    "first_name": "Member",
                    "preferred_name": "Member",
                },
            )
        )
