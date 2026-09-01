"""FastAPI transport for durable member-assistant conversations."""

import asyncio
from contextlib import asynccontextmanager
import threading
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Set
import uuid

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from member_assistant.events import AssistantEvent
from member_assistant.live_support import LiveSupportBroker
from member_assistant.runtime import AgentRuntime


MAX_MEMBER_MESSAGE_LENGTH = 20_000
SESSION_EXPIRED_CLOSE_CODE = 4001


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
    agent_event_hub = SessionEventHub()
    turn_tasks: Set["asyncio.Task[None]"] = set()

    async def publish_member(session_id: str, event: Dict[str, Any]) -> None:
        await event_hub.publish(session_id, event)

    async def publish_agent(agent_id: str, event: Dict[str, Any]) -> None:
        await agent_event_hub.publish(agent_id, event)

    live_broker = LiveSupportBroker(
        active_runtime.store,
        publish_member=publish_member,
        publish_agent=publish_agent,
        analyze_sentiment=active_runtime.analyze_live_sentiment,
        handoff_ended=active_runtime.end_handoff,
    )

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
            state = active_runtime.inspect_state(session_id)
            outcome = state.get("outcome") or {}
            if (
                state.get("handoff_status") == "queued"
                and outcome.get("case_id")
                and outcome.get("queue")
            ):
                reason = str(outcome.get("reason") or "member requested live support")
                await live_broker.enqueue(
                    case_id=str(outcome["case_id"]),
                    session_id=session_id,
                    member_name=str(
                        state.get("member_profile", {}).get(
                            "preferred_name", "Member"
                        )
                    ),
                    queue=str(outcome["queue"]),
                    reason=reason,
                    summary=active_runtime.handoff_summary(session_id, reason),
                    sentiment=str(state.get("sentiment", "unknown")),
                    sentiment_confidence=float(
                        state.get("sentiment_confidence", 0.0)
                    ),
                )
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
    app.state.agent_event_hub = agent_event_hub
    app.state.live_support = live_broker

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

    @app.get("/v1/live-support/status")
    async def live_support_status() -> Dict[str, Any]:
        return live_broker.queue_snapshot()

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
        ready_case = active_runtime.store.active_live_case(session_id)
        if ready_case is not None:
            ready_case = {
                **ready_case,
                "messages": active_runtime.store.live_messages(
                    ready_case["case_id"]
                ),
            }
        await websocket.send_json(
            {
                "type": "session.ready",
                "session_id": session_id,
                "catalog_revision": active_runtime.catalog.revision,
                "replayed_event_count": len(replay),
                "messages": active_runtime.inspect_state(session_id).get(
                    "messages", []
                ),
                "live_case": ready_case,
            }
        )

        async def send_events() -> None:
            while True:
                await websocket.send_json(await outgoing.get())

        sender = asyncio.create_task(
            send_events(), name="member-assistant-socket-sender"
        )
        session_ttl = float(active_runtime.store.session_ttl_seconds)
        idle_deadline = (
            asyncio.get_running_loop().time() + session_ttl
            if session_ttl > 0
            else None
        )

        try:
            while True:
                if idle_deadline is None:
                    request = await websocket.receive_json()
                else:
                    remaining = idle_deadline - asyncio.get_running_loop().time()
                    if remaining <= 0:
                        raise asyncio.TimeoutError
                    request = await asyncio.wait_for(
                        websocket.receive_json(), timeout=remaining
                    )
                request_type = request.get("type")
                if request_type == "session.ping":
                    await outgoing.put(
                        {"type": "session.pong", "session_id": session_id}
                    )
                    continue
                if request_type in {
                    "member.join",
                    "member.message",
                    "live_support.cancel",
                } and session_ttl > 0:
                    # Protocol heartbeats prove that the transport is healthy but
                    # do not extend the member's application-session lifetime.
                    idle_deadline = asyncio.get_running_loop().time() + session_ttl
                if request_type == "member.join":
                    try:
                        state = active_runtime.set_member_name(
                            session_id, str(request.get("name", ""))
                        )
                    except ValueError as exc:
                        await outgoing.put(
                            {
                                "type": "protocol.error",
                                "error": str(exc),
                                "final": False,
                            }
                        )
                    else:
                        await outgoing.put(
                            {
                                "type": "member.ready",
                                "session_id": session_id,
                                "member_name": state.get("member_profile", {}).get(
                                    "preferred_name", "Member"
                                ),
                            }
                        )
                    continue
                if request_type == "live_support.cancel":
                    cancelled = await live_broker.cancel_waiting(session_id)
                    if cancelled is None:
                        await outgoing.put(
                            {
                                "type": "protocol.error",
                                "error": "there is no waiting live-support request to cancel",
                                "final": False,
                            }
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
                active_case = active_runtime.store.active_live_case(session_id)
                if active_case and active_case.get("status") == "connected":
                    try:
                        await live_broker.member_message(
                            session_id,
                            content,
                            message_id=client_message_id,
                        )
                    except ValueError as exc:
                        await outgoing.put(
                            {
                                "type": "protocol.error",
                                "error": str(exc),
                                "final": False,
                            }
                        )
                    continue
                if active_case and active_case.get("status") == "waiting":
                    await outgoing.put(
                        {
                            "type": "live_support.waiting",
                            "case": active_case,
                            "message": "You are still waiting for an available MSR. Use Cancel live support to return to the virtual assistant.",
                        }
                    )
                    continue
                schedule_turn(session_id, content, client_message_id)
        except asyncio.TimeoutError:
            # Use one writer for the terminal event so it is delivered before the
            # close frame. The private close code lets clients distinguish an
            # intentional application-session expiry from a network interruption.
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)
            try:
                await websocket.send_json(
                    {
                        "type": "session.expired",
                        "session_id": session_id,
                        "reason": "inactivity_timeout",
                        "final": True,
                    }
                )
                await websocket.close(code=SESSION_EXPIRED_CLOSE_CODE)
            except (RuntimeError, WebSocketDisconnect):
                pass
            return
        except WebSocketDisconnect:
            return
        finally:
            event_hub.unsubscribe(session_id, outgoing)
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)

    @app.websocket("/v1/live-support/agents/{agent_id}/stream")
    async def live_agent_socket(websocket: WebSocket, agent_id: str) -> None:
        await websocket.accept()
        outgoing = agent_event_hub.subscribe(agent_id)
        await websocket.send_json(
            {"type": "agent.connected", "agent_id": agent_id}
        )

        async def send_agent_events() -> None:
            while True:
                await websocket.send_json(await outgoing.get())

        sender = asyncio.create_task(
            send_agent_events(), name="live-support-agent-sender"
        )
        joined = False
        try:
            while True:
                request = await websocket.receive_json()
                request_type = request.get("type")
                if request_type == "session.ping":
                    await outgoing.put({"type": "session.pong", "agent_id": agent_id})
                    continue
                if request_type == "agent.join":
                    try:
                        ready = await live_broker.join_agent(
                            agent_id,
                            str(request.get("name", "")),
                            str(request.get("queue", "")),
                        )
                    except ValueError as exc:
                        await outgoing.put(
                            {"type": "protocol.error", "error": str(exc), "final": False}
                        )
                    else:
                        joined = True
                        await outgoing.put(ready)
                    continue
                if not joined:
                    await outgoing.put(
                        {
                            "type": "protocol.error",
                            "error": "agent.join is required before live-support actions",
                            "final": False,
                        }
                    )
                    continue
                if request_type == "agent.message":
                    content = str(request.get("content", "")).strip()
                    case_id = str(request.get("case_id", "")).strip()
                    if not content or not case_id:
                        await outgoing.put(
                            {
                                "type": "protocol.error",
                                "error": "case_id and content must not be empty",
                                "final": False,
                            }
                        )
                        continue
                    if len(content) > MAX_MEMBER_MESSAGE_LENGTH:
                        await outgoing.put(
                            {
                                "type": "protocol.error",
                                "error": "content exceeds the maximum message length",
                                "final": False,
                            }
                        )
                        continue
                    try:
                        await live_broker.agent_message(
                            agent_id,
                            case_id,
                            content,
                            message_id=str(
                                request.get("message_id")
                                or "live_msg_{}".format(uuid.uuid4().hex)
                            ),
                        )
                    except ValueError as exc:
                        await outgoing.put(
                            {"type": "protocol.error", "error": str(exc), "final": False}
                        )
                    continue
                if request_type == "agent.end":
                    case_id = str(request.get("case_id", "")).strip()
                    case = active_runtime.store.live_case(case_id)
                    if not case or case.get("agent_id") != agent_id:
                        await outgoing.put(
                            {
                                "type": "protocol.error",
                                "error": "case is not assigned to this MSR",
                                "final": False,
                            }
                        )
                    else:
                        await live_broker.end_case(case_id, ended_by="agent")
                    continue
                await outgoing.put(
                    {
                        "type": "protocol.error",
                        "error": "unsupported live-agent event type",
                        "final": False,
                    }
                )
        except WebSocketDisconnect:
            return
        finally:
            if joined:
                await live_broker.leave_agent(agent_id)
            agent_event_hub.unsubscribe(agent_id, outgoing)
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)

    return app
