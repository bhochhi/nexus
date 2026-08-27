"""SQLite persistence for inspectable conversation state and audit events."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any, Callable, Dict, List, Optional

from member_assistant.models import ConversationState, new_conversation_state
from member_assistant.events import AssistantEvent


class SQLiteConversationStore:
    def __init__(
        self,
        path: Path,
        session_ttl_seconds: float = 600.0,
        clock: Optional[Callable[[], datetime]] = None,
    ):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.session_ttl_seconds = max(0.0, session_ttl_seconds)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._lock = threading.RLock()
        self._stop_cleanup = threading.Event()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._connection = sqlite3.connect(str(self.path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS turn_requests (
                session_id TEXT NOT NULL,
                client_message_id TEXT NOT NULL,
                turn_id TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(session_id, client_message_id),
                UNIQUE(turn_id)
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                session_id TEXT NOT NULL,
                turn_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                content TEXT,
                final INTEGER NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(turn_id, sequence)
            )
            """
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at "
            "ON conversations(updated_at)"
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversation_events_session_id "
            "ON conversation_events(session_id, id)"
        )
        self._connection.commit()
        self.cleanup_expired()
        if self.session_ttl_seconds > 0:
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                name="member-assistant-session-cleanup",
                daemon=True,
            )
            self._cleanup_thread.start()

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _expiry_cutoff(self) -> str:
        return (
            self._now() - timedelta(seconds=self.session_ttl_seconds)
        ).isoformat()

    def cleanup_expired(self) -> int:
        """Delete expired conversation and replay state while retaining audits."""

        if self.session_ttl_seconds <= 0:
            return 0
        with self._lock:
            cutoff = self._expiry_cutoff()
            expired_rows = self._connection.execute(
                "SELECT session_id FROM conversations WHERE updated_at <= ?",
                (cutoff,),
            ).fetchall()
            expired_session_ids = [row["session_id"] for row in expired_rows]
            cursor = self._connection.execute(
                "DELETE FROM conversations WHERE updated_at <= ?",
                (cutoff,),
            )
            for session_id in expired_session_ids:
                self._connection.execute(
                    "DELETE FROM conversation_events WHERE session_id = ?",
                    (session_id,),
                )
                self._connection.execute(
                    "DELETE FROM turn_requests WHERE session_id = ?",
                    (session_id,),
                )
            orphaned_rows = self._connection.execute(
                """
                SELECT DISTINCT session_id FROM turn_requests
                WHERE updated_at <= ?
                  AND session_id NOT IN (SELECT session_id FROM conversations)
                """,
                (cutoff,),
            ).fetchall()
            for row in orphaned_rows:
                self._connection.execute(
                    "DELETE FROM conversation_events WHERE session_id = ?",
                    (row["session_id"],),
                )
                self._connection.execute(
                    "DELETE FROM turn_requests WHERE session_id = ?",
                    (row["session_id"],),
                )
            self._connection.commit()
            return max(0, cursor.rowcount)

    def _cleanup_loop(self) -> None:
        interval = max(1.0, min(60.0, self.session_ttl_seconds / 2.0))
        while not self._stop_cleanup.wait(interval):
            self.cleanup_expired()

    def load(self, session_id: str) -> ConversationState:
        self.cleanup_expired()
        with self._lock:
            row = self._connection.execute(
                "SELECT state_json FROM conversations WHERE session_id = ?", (session_id,)
            ).fetchone()
        if row is None:
            return new_conversation_state()
        # Forward-fill new platform state fields when older durable sessions are loaded.
        state = new_conversation_state()
        state.update(json.loads(row["state_json"]))
        return state

    def save(self, session_id: str, state: ConversationState) -> None:
        payload = json.dumps(state, sort_keys=True)
        timestamp = self._now().isoformat()
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO conversations(session_id, state_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    state_json = excluded.state_json,
                    updated_at = excluded.updated_at
                """,
                (session_id, payload, timestamp),
            )
            self._connection.commit()

    def append_audit(self, session_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        timestamp = self._now().isoformat()
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO audit_events(session_id, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, event_type, json.dumps(payload, sort_keys=True), timestamp),
            )
            self._connection.commit()

    @staticmethod
    def message_digest(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def begin_turn(
        self,
        session_id: str,
        client_message_id: str,
        turn_id: str,
        content: str,
    ) -> Dict[str, Any]:
        """Claim an idempotent member message or return its existing turn."""

        timestamp = self._now().isoformat()
        digest = self.message_digest(content)
        with self._lock:
            row = self._connection.execute(
                """
                SELECT turn_id, content_sha256, status
                FROM turn_requests
                WHERE session_id = ? AND client_message_id = ?
                """,
                (session_id, client_message_id),
            ).fetchone()
            if row is not None:
                if row["content_sha256"] != digest:
                    raise ValueError(
                        "client_message_id was already used with different content"
                    )
                return {
                    "created": False,
                    "turn_id": row["turn_id"],
                    "status": row["status"],
                }
            self._connection.execute(
                """
                INSERT INTO turn_requests(
                    session_id, client_message_id, turn_id, content_sha256,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    client_message_id,
                    turn_id,
                    digest,
                    "in_progress",
                    timestamp,
                    timestamp,
                ),
            )
            self._connection.commit()
        return {"created": True, "turn_id": turn_id, "status": "in_progress"}

    def complete_turn(self, turn_id: str, status: str) -> None:
        with self._lock:
            self._connection.execute(
                """
                UPDATE turn_requests SET status = ?, updated_at = ?
                WHERE turn_id = ?
                """,
                (status, self._now().isoformat(), turn_id),
            )
            self._connection.commit()

    def append_event(self, event: AssistantEvent) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO conversation_events(
                    event_id, session_id, turn_id, sequence, event_type,
                    content, final, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.session_id,
                    event.turn_id,
                    event.sequence,
                    event.type,
                    event.content,
                    int(event.final),
                    json.dumps(event.metadata, sort_keys=True),
                    event.created_at,
                ),
            )
            self._connection.commit()

    def stream_events(
        self,
        session_id: str,
        *,
        after_event_id: Optional[str] = None,
        turn_id: Optional[str] = None,
    ) -> List[AssistantEvent]:
        """Return durable events in insertion order for reconnect or replay."""

        parameters: List[Any] = [session_id]
        clauses = ["session_id = ?"]
        if turn_id is not None:
            clauses.append("turn_id = ?")
            parameters.append(turn_id)
        with self._lock:
            if after_event_id is not None:
                cursor_row = self._connection.execute(
                    """
                    SELECT id FROM conversation_events
                    WHERE session_id = ? AND event_id = ?
                    """,
                    (session_id, after_event_id),
                ).fetchone()
                if cursor_row is None:
                    raise ValueError("after_event_id does not belong to this session")
                clauses.append("id > ?")
                parameters.append(cursor_row["id"])
            query = """
                SELECT event_id, session_id, turn_id, sequence, event_type,
                       content, final, metadata_json, created_at
                FROM conversation_events
                WHERE {}
                ORDER BY id
            """.format(" AND ".join(clauses))
            rows = self._connection.execute(query, parameters).fetchall()
        return [
            AssistantEvent.create(
                event_id=row["event_id"],
                session_id=row["session_id"],
                turn_id=row["turn_id"],
                sequence=row["sequence"],
                event_type=row["event_type"],
                content=row["content"],
                final=bool(row["final"]),
                metadata=json.loads(row["metadata_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def audit_events(self, session_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT event_type, payload_json, created_at
                FROM audit_events WHERE session_id = ? ORDER BY id
                """,
                (session_id,),
            ).fetchall()
        return [
            {
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def inspect(self, session_id: str) -> ConversationState:
        return deepcopy(self.load(session_id))

    def close(self) -> None:
        self._stop_cleanup.set()
        if self._cleanup_thread is not None:
            self._cleanup_thread.join(timeout=2.0)
        with self._lock:
            self._connection.close()
