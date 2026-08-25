"""SQLite persistence for inspectable conversation state and audit events."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any, Callable, Dict, List, Optional

from member_assistant.models import ConversationState, new_conversation_state


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
            "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at "
            "ON conversations(updated_at)"
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
        """Delete expired conversation snapshots while retaining audit history."""

        if self.session_ttl_seconds <= 0:
            return 0
        with self._lock:
            cursor = self._connection.execute(
                "DELETE FROM conversations WHERE updated_at <= ?",
                (self._expiry_cutoff(),),
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
