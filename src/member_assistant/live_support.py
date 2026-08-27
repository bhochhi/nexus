"""Queueing and participant routing for live member support."""

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional
import uuid

from member_assistant.state_store import SQLiteConversationStore


LIVE_SUPPORT_QUEUES = ("insurance", "banking", "advice")

Publish = Callable[[str, Dict[str, Any]], Awaitable[None]]
SentimentAnalyzer = Callable[[str, str], Dict[str, Any]]
HandoffEnded = Callable[[str, str], Dict[str, Any]]


@dataclass(frozen=True)
class OnlineAgent:
    agent_id: str
    name: str
    queue: str


class LiveSupportBroker:
    """Automatically matches waiting cases to the least-active online MSR."""

    def __init__(
        self,
        store: SQLiteConversationStore,
        *,
        publish_member: Publish,
        publish_agent: Publish,
        analyze_sentiment: SentimentAnalyzer,
        handoff_ended: HandoffEnded,
    ) -> None:
        self.store = store
        self._publish_member = publish_member
        self._publish_agent = publish_agent
        self._analyze_sentiment = analyze_sentiment
        self._handoff_ended = handoff_ended
        self._agents: Dict[str, OnlineAgent] = {}
        self._lock = asyncio.Lock()
        self.store.requeue_all_live_cases()

    @staticmethod
    def validate_queue(queue: str) -> str:
        normalized = str(queue).strip().casefold()
        if normalized not in LIVE_SUPPORT_QUEUES:
            raise ValueError(
                "queue must be one of {}".format(", ".join(LIVE_SUPPORT_QUEUES))
            )
        return normalized

    async def join_agent(self, agent_id: str, name: str, queue: str) -> Dict[str, Any]:
        clean_id = str(agent_id).strip()
        clean_name = " ".join(str(name).split())[:80]
        clean_queue = self.validate_queue(queue)
        if not clean_id or not clean_name:
            raise ValueError("agent ID and name must not be empty")
        async with self._lock:
            self._agents[clean_id] = OnlineAgent(clean_id, clean_name, clean_queue)
            await self._assign_waiting_locked(clean_queue)
            cases = [self._case_snapshot(case) for case in self.store.agent_live_cases(clean_id)]
            snapshot = self.queue_snapshot()
        return {
            "type": "agent.ready",
            "agent_id": clean_id,
            "agent_name": clean_name,
            "queue": clean_queue,
            "cases": cases,
            **snapshot,
        }

    async def leave_agent(self, agent_id: str) -> None:
        async with self._lock:
            agent = self._agents.pop(agent_id, None)
            if agent is None:
                return
            requeued = self.store.requeue_agent_cases(agent_id)
            for case in requeued:
                await self._publish_member(
                    case["session_id"],
                    {
                        "type": "live_support.waiting",
                        "case": self._case_snapshot(case),
                        "message": "Your MSR disconnected. We are finding another available specialist.",
                    },
                )
            await self._assign_waiting_locked(agent.queue)
            await self._broadcast_queue_snapshot_locked()

    async def enqueue(
        self,
        *,
        case_id: str,
        session_id: str,
        member_name: str,
        queue: str,
        reason: str,
        summary: str,
        sentiment: str,
        sentiment_confidence: float,
    ) -> Dict[str, Any]:
        clean_queue = self.validate_queue(queue)
        async with self._lock:
            case = self.store.create_live_case(
                case_id=case_id,
                session_id=session_id,
                member_name=member_name,
                queue=clean_queue,
                reason=reason,
                summary=summary,
                sentiment=sentiment,
                sentiment_confidence=sentiment_confidence,
            )
            self.store.append_audit(
                session_id,
                "live_case_queued",
                {"case_id": case["case_id"], "queue": clean_queue},
            )
            if case["status"] == "waiting":
                await self._publish_member(
                    session_id,
                    {
                        "type": "live_support.waiting",
                        "case": self._case_snapshot(case),
                        "message": "You are in the {} queue. We'll connect you automatically when an MSR is available.".format(
                            clean_queue
                        ),
                    },
                )
                await self._assign_waiting_locked(clean_queue)
            await self._broadcast_queue_snapshot_locked()
            return self._case_snapshot(
                self.store.active_live_case(session_id) or case,
                include_messages=True,
            )

    async def cancel_waiting(self, session_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            case = self.store.active_live_case(session_id)
            if case is None or case["status"] != "waiting":
                return None
            finished = self.store.finish_live_case(
                case["case_id"], status="cancelled", ended_by="member"
            )
            if finished is None:
                return None
            event = {
                "type": "live_support.cancelled",
                "case": self._case_snapshot(finished),
                "message": "The live-support request was cancelled. You can keep chatting with the virtual assistant.",
            }
            await self._publish_member(session_id, event)
            assistant_event = self._handoff_ended(session_id, "cancelled")
            await self._publish_member(session_id, assistant_event)
            await self._broadcast_queue_snapshot_locked()
            return event

    async def member_message(
        self,
        session_id: str,
        content: str,
        *,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        case = self.store.active_live_case(session_id)
        if case is None or case["status"] != "connected":
            raise ValueError("the member is not connected to an MSR")
        if content.strip() == "/end":
            ended = await self.end_case(case["case_id"], ended_by="member")
            return ended or {"type": "live_support.ended"}
        message = self.store.append_live_message(
            message_id=message_id or "live_msg_{}".format(uuid.uuid4().hex),
            case_id=case["case_id"],
            sender_type="member",
            sender_name=case["member_name"],
            content=content,
        )
        created = bool(message.pop("created", True))
        event = {"type": "live.message", "message": message}
        await self._publish_member(session_id, event)
        await self._publish_agent(str(case["agent_id"]), event)

        if not created:
            return event

        self.store.append_audit(
            session_id,
            "live_message",
            {
                "case_id": case["case_id"],
                "sender_type": "member",
                "message_length": len(content),
            },
        )

        sentiment = await asyncio.to_thread(
            self._analyze_sentiment, session_id, content
        )
        updated = self.store.update_live_sentiment(
            case["case_id"],
            str(sentiment.get("sentiment", "unknown")),
            float(sentiment.get("confidence", 0.0)),
        )
        sentiment_event = {
            "type": "sentiment.updated",
            "case_id": case["case_id"],
            "sentiment": sentiment.get("sentiment", "unknown"),
            "confidence": sentiment.get("confidence", 0.0),
            "source": "live_member_message",
        }
        await self._publish_member(session_id, sentiment_event)
        if updated and updated.get("agent_id"):
            await self._publish_agent(str(updated["agent_id"]), sentiment_event)
        return event

    async def agent_message(
        self,
        agent_id: str,
        case_id: str,
        content: str,
        *,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        case = self.store.live_case(case_id)
        if (
            case is None
            or case["status"] != "connected"
            or case.get("agent_id") != agent_id
        ):
            raise ValueError("case is not assigned to this MSR")
        if content.strip() == "/end":
            ended = await self.end_case(case_id, ended_by="agent")
            return ended or {"type": "live_support.ended"}
        message = self.store.append_live_message(
            message_id=message_id or "live_msg_{}".format(uuid.uuid4().hex),
            case_id=case_id,
            sender_type="agent",
            sender_name=str(case["agent_name"]),
            content=content,
        )
        created = bool(message.pop("created", True))
        event = {"type": "live.message", "message": message}
        await self._publish_member(case["session_id"], event)
        await self._publish_agent(agent_id, event)
        if created:
            self.store.append_audit(
                case["session_id"],
                "live_message",
                {
                    "case_id": case_id,
                    "sender_type": "agent",
                    "message_length": len(content),
                },
            )
        return event

    async def end_case(self, case_id: str, *, ended_by: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            case = self.store.live_case(case_id)
            if case is None or case["status"] not in {"waiting", "connected"}:
                return None
            finished = self.store.finish_live_case(
                case_id, status="ended", ended_by=ended_by
            )
            if finished is None:
                return None
            event = {
                "type": "live_support.ended",
                "case": self._case_snapshot(finished),
                "ended_by": ended_by,
            }
            await self._publish_member(finished["session_id"], event)
            if finished.get("agent_id"):
                await self._publish_agent(str(finished["agent_id"]), event)
            assistant_event = self._handoff_ended(finished["session_id"], ended_by)
            await self._publish_member(finished["session_id"], assistant_event)
            if finished.get("queue"):
                await self._assign_waiting_locked(str(finished["queue"]))
            await self._broadcast_queue_snapshot_locked()
            return event

    async def _assign_waiting_locked(self, queue: str) -> None:
        while True:
            waiting = self.store.waiting_live_cases(queue)
            candidates = [agent for agent in self._agents.values() if agent.queue == queue]
            if not waiting or not candidates:
                return
            candidates.sort(
                key=lambda agent: (len(self.store.agent_live_cases(agent.agent_id)), agent.agent_id)
            )
            selected = candidates[0]
            assigned = self.store.assign_live_case(
                waiting[0]["case_id"], selected.agent_id, selected.name
            )
            if assigned is None:
                continue
            self.store.append_audit(
                assigned["session_id"],
                "live_case_assigned",
                {
                    "case_id": assigned["case_id"],
                    "queue": queue,
                    "agent_id": selected.agent_id,
                },
            )
            event = {
                "type": "live_support.assigned",
                "case": self._case_snapshot(assigned, include_messages=True),
                "system_message": "[System message: Summary] {}".format(
                    assigned["summary"]
                ),
            }
            await self._publish_member(assigned["session_id"], event)
            await self._publish_agent(selected.agent_id, event)

    def queue_snapshot(self) -> Dict[str, Any]:
        snapshot = self.store.live_support_snapshot()
        queues = {
            queue: {
                "waiting": snapshot.get("queues", {}).get(queue, {}).get("waiting", 0),
                "connected": snapshot.get("queues", {}).get(queue, {}).get(
                    "connected", 0
                ),
                "online_agents": sum(
                    1 for agent in self._agents.values() if agent.queue == queue
                ),
            }
            for queue in LIVE_SUPPORT_QUEUES
        }
        return {"queue_status": queues}

    async def _broadcast_queue_snapshot_locked(self) -> None:
        event = {"type": "queue.updated", **self.queue_snapshot()}
        for agent_id in list(self._agents):
            await self._publish_agent(agent_id, event)

    def _case_snapshot(
        self, case: Dict[str, Any], *, include_messages: bool = False
    ) -> Dict[str, Any]:
        snapshot = dict(case)
        if include_messages:
            snapshot["messages"] = self.store.live_messages(case["case_id"])
        return snapshot


__all__ = ["LIVE_SUPPORT_QUEUES", "LiveSupportBroker"]
