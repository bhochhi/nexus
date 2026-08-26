"""Deterministic authorization, tool, and confirmation gates."""

from dataclasses import dataclass
from typing import List, Sequence

from member_assistant.catalog import SkillDefinition


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    event: str


class PolicyEngine:
    def evaluate(
        self,
        definition: SkillDefinition,
        required_tools: Sequence[str],
        authenticated: bool,
        authorizations: List[str],
        task_status: str,
        confirmation_status: str,
        dependencies_available: bool = True,
    ) -> PolicyDecision:
        if any(tool not in definition.allowed_tools for tool in required_tools):
            return PolicyDecision(False, "Skill is not approved to call its tool.", "tool_denied")
        if not dependencies_available:
            return PolicyDecision(
                False,
                "A required integration is not available; no action was taken.",
                "tool_unavailable",
            )
        if definition.auth_required and not authenticated:
            return PolicyDecision(
                False,
                "Please sign in before I access account-specific information.",
                "authentication_denied",
            )
        if (
            definition.required_authorization
            and definition.required_authorization not in authorizations
        ):
            return PolicyDecision(
                False,
                "This session is not authorized for that request. I can connect you to support.",
                "authorization_denied",
            )
        if (
            definition.confirmation_required
            and task_status == "awaiting_confirmation"
            and confirmation_status != "confirmed"
        ):
            return PolicyDecision(
                False,
                "The action still needs explicit confirmation.",
                "confirmation_denied",
            )
        return PolicyDecision(True, "approved", "policy_approved")
