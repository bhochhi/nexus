"""Mock live-support routing adapter."""

from dataclasses import dataclass
import hashlib
from typing import Any, Dict, List


@dataclass(frozen=True)
class HandoffRequest:
    reason: str
    queue: str
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
    actions = ("create",)

    @staticmethod
    def derive_queue(reason: str, requested_queue: str, active_goal: str) -> str:
        requested = requested_queue.strip().casefold()
        if requested in {"insurance", "banking", "advice"}:
            return requested
        context = "{} {} {}".format(reason, requested_queue, active_goal).casefold()
        insurance_terms = (
            "insurance",
            "policy",
            "coverage",
            "claim",
            "premium",
            "auto",
            "homeowners",
            "life insurance",
        )
        banking_terms = (
            "bank",
            "balance",
            "checking",
            "savings",
            "credit card",
            "debit card",
            "transaction",
            "transfer",
            "deposit",
            "account",
        )
        advice_terms = (
            "advice",
            "advisor",
            "planning",
            "retirement",
            "financial plan",
            "invest",
        )
        if any(term in context for term in insurance_terms):
            return "insurance"
        if any(term in context for term in banking_terms):
            return "banking"
        if any(term in context for term in advice_terms):
            return "advice"
        return "advice"

    def create(self, request: HandoffRequest) -> HandoffReceipt:
        reason = " ".join(request.reason.split())[:300]
        active_goal = " ".join(request.active_goal.split())[:300]
        goal = (
            reason
            if not active_goal or active_goal.casefold() == "general assistance"
            else active_goal
        )
        completed_steps = [
            " ".join(str(step).split())[:160]
            for step in request.completed_steps[-6:]
            if str(step).strip()
        ]
        queue = self.derive_queue(reason, request.queue, goal)
        summary = "Goal: {}\nReason: {}\nCompleted: {}".format(
            goal or "general assistance",
            reason or "member requested live support",
            ", ".join(completed_steps) if completed_steps else "none",
        )
        digest = hashlib.sha256(summary.encode("utf-8")).hexdigest()[:8].upper()
        return HandoffReceipt(
            case_id="CASE-{}".format(digest),
            queue=queue,
            status="queued",
            summary=summary,
        )

    def invoke(self, action: str, arguments: Dict[str, Any]) -> Any:
        if action != "create":
            raise ValueError("Unsupported mock handoff action: {}".format(action))
        receipt = self.create(
            HandoffRequest(
                reason=str(arguments.get("reason", "member requested a person")),
                queue=str(arguments.get("queue", "")),
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
