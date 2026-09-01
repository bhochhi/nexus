import json
import time

from member_assistant.ui_client import RealtimeWebSocketClient


class _FakeSocket:
    def __init__(self, payloads=None):
        self.sent = []
        self.closed = False
        self._payloads = list(
            payloads
            if payloads is not None
            else [
                json.dumps(
                    {
                        "type": "session.expired",
                        "reason": "inactivity_timeout",
                    }
                )
            ]
        )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def send(self, payload):
        self.sent.append(json.loads(payload))

    def recv(self, timeout):
        if self._payloads:
            return self._payloads.pop(0)
        raise AssertionError("client attempted to read after terminal expiry event")

    def close(self):
        self.closed = True


def test_session_expiry_is_terminal_and_does_not_reconnect(monkeypatch):
    socket = _FakeSocket()
    connect_calls = []

    def connect(url, open_timeout):
        connect_calls.append((url, open_timeout))
        return socket

    monkeypatch.setattr("websockets.sync.client.connect", connect)
    client = RealtimeWebSocketClient(
        "ws://example.test/member",
        {"type": "member.join", "name": "Rupee"},
    )
    deadline = time.monotonic() + 1
    events = []
    while time.monotonic() < deadline:
        events.extend(client.drain())
        if any(event.get("type") == "session.expired" for event in events):
            break
        time.sleep(0.01)
    client.close()

    assert [event["type"] for event in events] == [
        "connection.open",
        "session.expired",
    ]
    assert connect_calls == [("ws://example.test/member", 5)]
    assert socket.sent == [{"type": "member.join", "name": "Rupee"}]


def test_expiry_close_code_is_terminal_when_event_is_not_received(monkeypatch):
    class ExpiredConnection(Exception):
        code = 4001

    socket = _FakeSocket([])

    def recv(timeout):
        raise ExpiredConnection("session expired")

    socket.recv = recv
    connect_calls = []

    def connect(url, open_timeout):
        connect_calls.append((url, open_timeout))
        return socket

    monkeypatch.setattr("websockets.sync.client.connect", connect)
    client = RealtimeWebSocketClient("ws://example.test/member")
    deadline = time.monotonic() + 1
    events = []
    while time.monotonic() < deadline:
        events.extend(client.drain())
        if any(event.get("type") == "session.expired" for event in events):
            break
        time.sleep(0.01)
    client.close()

    assert [event["type"] for event in events] == [
        "connection.open",
        "session.expired",
    ]
    assert connect_calls == [("ws://example.test/member", 5)]
