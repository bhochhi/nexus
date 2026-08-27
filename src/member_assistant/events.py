"""Provider- and transport-neutral conversation stream events."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid


@dataclass(frozen=True)
class AssistantEvent:
    """One durable event produced while processing a member turn.

    The runtime owns this contract. WebSocket, CLI, and future HTTP/SSE clients
    are only transports and must not infer behavior from LangGraph internals.
    """

    event_id: str
    session_id: str
    turn_id: str
    sequence: int
    type: str
    created_at: str
    content: Optional[str] = None
    final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        turn_id: str,
        sequence: int,
        event_type: str,
        content: Optional[str] = None,
        final: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> "AssistantEvent":
        return cls(
            event_id=event_id or "evt_{}".format(uuid.uuid4().hex),
            session_id=session_id,
            turn_id=turn_id,
            sequence=sequence,
            type=event_type,
            created_at=created_at or datetime.now(timezone.utc).isoformat(),
            content=content,
            final=final,
            metadata=dict(metadata or {}),
        )

    def as_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "sequence": self.sequence,
            "type": self.type,
            "created_at": self.created_at,
            "final": self.final,
            "metadata": dict(self.metadata),
        }
        if self.content is not None:
            payload["content"] = self.content
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AssistantEvent":
        return cls(
            event_id=str(payload["event_id"]),
            session_id=str(payload["session_id"]),
            turn_id=str(payload["turn_id"]),
            sequence=int(payload["sequence"]),
            type=str(payload["type"]),
            created_at=str(payload["created_at"]),
            content=payload.get("content"),
            final=bool(payload.get("final", False)),
            metadata=dict(payload.get("metadata", {})),
        )
