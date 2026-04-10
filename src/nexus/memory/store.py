from abc import ABC, abstractmethod

from nexus.memory.session import Session


class SessionStore(ABC):
    """Abstract session store."""

    @abstractmethod
    def load(self, user_id: str, session_id: str) -> Session: ...

    @abstractmethod
    def save(self, session: Session) -> None: ...


class InMemoryStore(SessionStore):
    """In-memory session store for local development and testing."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def _key(self, user_id: str, session_id: str) -> str:
        return f"{user_id}:{session_id}"

    def load(self, user_id: str, session_id: str) -> Session:
        key = self._key(user_id, session_id)
        if key not in self._sessions:
            self._sessions[key] = Session(user_id=user_id, session_id=session_id)
        return self._sessions[key]

    def save(self, session: Session) -> None:
        key = self._key(session.user_id, session.session_id)
        self._sessions[key] = session
