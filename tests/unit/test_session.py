from nexus.memory.session import Session
from nexus.memory.store import InMemoryStore


def test_session_add_message():
    session = Session(user_id="u1", session_id="s1")
    session.add_message("user", "hello")
    session.add_message("assistant", "hi there")

    assert len(session.history) == 2
    assert session.history[0]["role"] == "user"
    assert session.history[1]["content"] == "hi there"


def test_session_format_history():
    session = Session(user_id="u1", session_id="s1")
    assert session.format_history() == "(no prior conversation)"

    session.add_message("user", "hello")
    session.add_message("assistant", "hi")
    formatted = session.format_history()
    assert "User: hello" in formatted
    assert "Assistant: hi" in formatted


def test_in_memory_store():
    store = InMemoryStore()

    session = store.load("u1", "s1")
    assert session.user_id == "u1"
    assert session.history == []

    session.add_message("user", "test")
    store.save(session)

    reloaded = store.load("u1", "s1")
    assert len(reloaded.history) == 1
