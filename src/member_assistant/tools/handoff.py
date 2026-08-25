"""Mock live-support routing adapter."""

from dataclasses import dataclass
import hashlib
from typing import Any, Dict, List


@dataclass(frozen=True)
class HandoffRequest:
    reason: str
    active_goal: str
    completed_steps: List[str]


@dataclass(frozen=True)
class HandoffReceipt:
    case_id: str
    queue: str
    status: str
    summary: str


class MockHandoffTool:
    name = "mock_live_agent"

    def create(self, request: HandoffRequest) -> HandoffReceipt:
        summary = "Goal: {}. Completed: {}. Reason: {}.".format(
            request.active_goal or "general assistance",
            ", ".join(request.completed_steps) if request.completed_steps else "none",
            request.reason,
        )
        digest = hashlib.sha256(summary.encode("utf-8")).hexdigest()[:8].upper()
        return HandoffReceipt(
            case_id="CASE-{}".format(digest),
            queue="member-support",
            status="queued",
            summary=summary,
        )

    def invoke(self, action: str, arguments: Dict[str, Any]) -> Any:
        if action != "create":
            raise ValueError("Unsupported mock handoff action: {}".format(action))
        receipt = self.create(
            HandoffRequest(
                reason=str(arguments.get("reason", "member requested a person")),
                active_goal=str(arguments.get("active_goal", "general assistance")),
                completed_steps=list(arguments.get("completed_steps", [])),
            )
        )
        return {
            "case_id": receipt.case_id,
            "queue": receipt.queue,
            "status": receipt.status,
            "summary": receipt.summary,
        }
