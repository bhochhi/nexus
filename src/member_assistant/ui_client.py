"""Small reconnecting WebSocket client shared by the Streamlit demo apps."""

import json
import queue
import threading
import time
from typing import Any, Dict, List, Optional


class RealtimeWebSocketClient:
    def __init__(self, url: str, initial_event: Optional[Dict[str, Any]] = None):
        self.url = url
        self.initial_event = dict(initial_event or {})
        self.events: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._socket: Any = None
        self._send_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="streamlit-live-chat-socket",
            daemon=True,
        )
        self._thread.start()

    def _run(self) -> None:
        try:
            from websockets.sync.client import connect
        except ImportError:
            self.events.put(
                {
                    "type": "connection.error",
                    "error": "The WebSocket client dependency is not installed.",
                }
            )
            return
        while not self._stop.is_set():
            try:
                with connect(self.url, open_timeout=5) as websocket:
                    self._socket = websocket
                    self.events.put({"type": "connection.open"})
                    if self.initial_event:
                        websocket.send(json.dumps(self.initial_event))
                    while not self._stop.is_set():
                        try:
                            payload = websocket.recv(timeout=1)
                        except TimeoutError:
                            continue
                        if payload is not None:
                            self.events.put(json.loads(payload))
            except Exception as exc:
                if not self._stop.is_set():
                    self.events.put(
                        {
                            "type": "connection.error",
                            "error": " ".join(str(exc).split())[:240],
                        }
                    )
                    self._stop.wait(1.5)
            finally:
                self._socket = None

    def send(self, event: Dict[str, Any]) -> None:
        with self._send_lock:
            if self._socket is None:
                raise ConnectionError("The live connection is not ready yet.")
            self._socket.send(json.dumps(event))

    def drain(self, limit: int = 200) -> List[Dict[str, Any]]:
        drained = []
        while len(drained) < limit:
            try:
                drained.append(self.events.get_nowait())
            except queue.Empty:
                break
        return drained

    def close(self) -> None:
        self._stop.set()
        socket = self._socket
        if socket is not None:
            try:
                socket.close()
            except Exception:
                pass
        self._thread.join(timeout=2)


__all__ = ["RealtimeWebSocketClient"]
