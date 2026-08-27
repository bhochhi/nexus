"""FastAPI transport for durable member-assistant conversations."""

import asyncio
from contextlib import asynccontextmanager
import threading
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Set
import uuid

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from member_assistant.events import AssistantEvent
from member_assistant.runtime import AgentRuntime


MAX_MEMBER_MESSAGE_LENGTH = 20_000


class SessionRequest(BaseModel):
    session_id: Optional[str] = None


class SessionEventHub:
    """In-process fan-out for every socket watching the same session.

    Durable SQLite events remain authoritative. This hub only handles live
    delivery; a production deployment can replace it with a shared broker.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List["asyncio.Queue[Dict[str, Any]]"]] = {}

    def subscribe(self, session_id: str) -> "asyncio.Queue[Dict[str, Any]]":
        queue: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()
        self._subscribers.setdefault(session_id, []).append(queue)
        return queue

    def unsubscribe(
        self, session_id: str, queue: "asyncio.Queue[Dict[str, Any]]"
    ) -> None:
        subscribers = self._subscribers.get(session_id, [])
        if queue in subscribers:
            subscribers.remove(queue)
        if not subscribers:
            self._subscribers.pop(session_id, None)

    async def publish(self, session_id: str, event: Dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(session_id, [])):
            await queue.put(dict(event))


async def _async_events(
    events: Iterator[AssistantEvent],
) -> AsyncIterator[AssistantEvent]:
    """Consume a synchronous runtime stream without blocking the ASGI loop.

    The dedicated worker continues the durable turn even if a socket disconnects.
    A reconnect can replay everything already committed to ``conversation_events``.
    """

    loop = asyncio.get_running_loop()
    queue: "asyncio.Queue[tuple]" = asyncio.Queue()

    def consume() -> None:
        try:
            for event in events:
                loop.call_soon_threadsafe(queue.put_nowait, ("event", event))
        except Exception as exc:  # The runtime already emitted a safe failure event.
            loop.call_soon_threadsafe(queue.put_nowait, ("error", exc))
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, ("done", None))

    threading.Thread(
        target=consume,
        name="member-assistant-turn-stream",
        daemon=True,
    ).start()
    pending_error: Optional[Exception] = None
    while True:
        kind, value = await queue.get()
        if kind == "event":
            yield value
        elif kind == "error":
            pending_error = value
        else:
            if pending_error is not None:
                raise pending_error
            return


def create_app(
    runtime: Optional[AgentRuntime] = None,
    *,
    close_runtime: Optional[bool] = None,
) -> FastAPI:
    """Build the API around one shared runtime and one compiled LangGraph."""

    owns_runtime = runtime is None if close_runtime is None else close_runtime
    active_runtime = runtime or AgentRuntime.from_settings()
    event_hub = SessionEventHub()
    turn_tasks: Set["asyncio.Task[None]"] = set()

    async def run_turn(
        session_id: str, content: str, client_message_id: str
    ) -> None:
        terminal_published = False
        try:
            stream = active_runtime.stream_chat(
                session_id,
                content,
                client_message_id=client_message_id,
            )
            async for event in _async_events(stream):
                terminal_published = terminal_published or event.final
                await event_hub.publish(session_id, event.as_dict())
        except Exception:
            if not terminal_published:
                await event_hub.publish(
                    session_id,
                    {
                        "type": "protocol.error",
                        "error": "the turn failed safely",
                        "final": True,
                    },
                )

    def schedule_turn(
        session_id: str, content: str, client_message_id: str
    ) -> None:
        task = asyncio.create_task(
            run_turn(session_id, content, client_message_id),
            name="member-assistant-{}".format(client_message_id),
        )
        turn_tasks.add(task)
        task.add_done_callback(turn_tasks.discard)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        if turn_tasks:
            await asyncio.gather(*list(turn_tasks), return_exceptions=True)
        if owns_runtime:
            active_runtime.close()

    app = FastAPI(
        title="Agentic Member Assistant",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.runtime = active_runtime
    app.state.event_hub = event_hub

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        metadata = active_runtime.provider.observability_metadata()
        return {
            "status": "ready",
            "graph_instances": 1,
            "catalog_revision": active_runtime.catalog.revision,
            "provider": metadata.get("provider"),
            "model": metadata.get("model"),
        }

    @app.post("/v1/sessions")
    async def create_session(request: SessionRequest) -> Dict[str, Any]:
        session_id = (request.session_id or "session_{}".format(uuid.uuid4().hex)).strip()
        if not session_id:
            raise HTTPException(status_code=422, detail="session_id must not be empty")
        state = active_runtime.inspect_state(session_id)
        return {
            "session_id": session_id,
            "turn_count": state["turn_count"],
            "websocket_path": "/v1/sessions/{}/stream".format(session_id),
        }

    @app.get("/v1/sessions/{session_id}")
    async def inspect_session(session_id: str) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "state": active_runtime.inspect_state(session_id),
            "events": [
                event.as_dict()
                for event in active_runtime.store.stream_events(session_id)
            ],
        }

    @app.get("/v1/sessions/{session_id}/events")
    async def replay_events(
        session_id: str,
        after_event_id: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        try:
            events = active_runtime.store.stream_events(
                session_id, after_event_id=after_event_id
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "session_id": session_id,
            "events": [event.as_dict() for event in events],
        }

    @app.websocket("/v1/sessions/{session_id}/stream")
    async def conversation_socket(
        websocket: WebSocket,
        session_id: str,
        after_event_id: Optional[str] = Query(default=None),
    ) -> None:
        await websocket.accept()
        outgoing = event_hub.subscribe(session_id)
        try:
            replay = active_runtime.store.stream_events(
                session_id, after_event_id=after_event_id
            )
        except ValueError as exc:
            event_hub.unsubscribe(session_id, outgoing)
            await websocket.send_json(
                {"type": "protocol.error", "error": str(exc), "final": True}
            )
            await websocket.close(code=1008)
            return
        for event in replay:
            await websocket.send_json(event.as_dict())
        replayed_event_ids = {event.event_id for event in replay}
        while True:
            try:
                buffered = outgoing.get_nowait()
            except asyncio.QueueEmpty:
                break
            if buffered.get("event_id") not in replayed_event_ids:
                await websocket.send_json(buffered)
        await websocket.send_json(
            {
                "type": "session.ready",
                "session_id": session_id,
                "catalog_revision": active_runtime.catalog.revision,
                "replayed_event_count": len(replay),
            }
        )

        async def send_events() -> None:
            while True:
                await websocket.send_json(await outgoing.get())

        sender = asyncio.create_task(
            send_events(), name="member-assistant-socket-sender"
        )

        try:
            while True:
                request = await websocket.receive_json()
                request_type = request.get("type")
                if request_type == "session.ping":
                    await outgoing.put(
                        {"type": "session.pong", "session_id": session_id}
                    )
                    continue
                if request_type != "member.message":
                    await outgoing.put(
                        {
                            "type": "protocol.error",
                            "error": "expected event type member.message",
                            "final": True,
                        }
                    )
                    continue
                content = str(request.get("content", "")).strip()
                if not content:
                    await outgoing.put(
                        {
                            "type": "protocol.error",
                            "error": "content must not be empty",
                            "final": True,
                        }
                    )
                    continue
                if len(content) > MAX_MEMBER_MESSAGE_LENGTH:
                    await outgoing.put(
                        {
                            "type": "protocol.error",
                            "error": "content exceeds the maximum message length",
                            "final": True,
                        }
                    )
                    continue
                client_message_id = str(
                    request.get("message_id") or "msg_{}".format(uuid.uuid4().hex)
                )
                schedule_turn(session_id, content, client_message_id)
        except WebSocketDisconnect:
            return
        finally:
            event_hub.unsubscribe(session_id, outgoing)
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)

    return app
