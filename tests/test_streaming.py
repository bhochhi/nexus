from fastapi.testclient import TestClient

from member_assistant.server import create_app


def test_runtime_streams_semantic_multi_goal_messages_and_persists_replay(
    runtime_factory,
):
    runtime = runtime_factory()
    utterance = "tell me about account balance and do the internal transfer"

    events = list(
        runtime.stream_chat(
            "stream-session", utterance, client_message_id="member-message-1"
        )
    )

    assert [event.type for event in events] == [
        "turn.accepted",
        "assistant.message",
        "assistant.request_input",
        "turn.completed",
    ]
    assert "help with both" in events[1].content
    assert "Which account" in events[2].content
    assert events[-1].final is True
    assert events[-1].metadata["catalog_revision"] == runtime.catalog.revision
    assert runtime.store.stream_events("stream-session") == events

    duplicate = list(
        runtime.stream_chat(
            "stream-session", utterance, client_message_id="member-message-1"
        )
    )
    assert duplicate == events
    assert runtime.inspect_state("stream-session")["turn_count"] == 1


def test_synchronous_chat_aggregates_the_same_stream(runtime_factory):
    runtime = runtime_factory()

    reply = runtime.chat(
        "aggregate-session",
        "what is my balance",
        client_message_id="aggregate-message",
    )
    events = runtime.store.stream_events("aggregate-session")

    assistant_text = "\n\n".join(
        event.content
        for event in events
        if event.type.startswith("assistant.") and event.content
    )
    assert reply.text == assistant_text
    assert events[-1].metadata["reply"] == reply.text


def test_websocket_streams_events_and_replays_after_reconnect(runtime_factory):
    runtime = runtime_factory()
    app = create_app(runtime, close_runtime=False)

    with TestClient(app) as client:
        assert client.get("/health").json()["graph_instances"] == 1
        with client.websocket_connect(
            "/v1/sessions/socket-session/stream"
        ) as websocket:
            ready = websocket.receive_json()
            assert ready["type"] == "session.ready"
            websocket.send_json(
                {
                    "type": "member.message",
                    "message_id": "socket-message-1",
                    "content": "what is my balance",
                }
            )
            first_turn = []
            while True:
                event = websocket.receive_json()
                first_turn.append(event)
                if event.get("final"):
                    break

        assert first_turn[0]["type"] == "turn.accepted"
        assert first_turn[-1]["type"] == "turn.completed"
        cursor = first_turn[0]["event_id"]

        with client.websocket_connect(
            "/v1/sessions/socket-session/stream?after_event_id={}".format(cursor)
        ) as websocket:
            replayed = []
            while True:
                event = websocket.receive_json()
                if event["type"] == "session.ready":
                    assert event["replayed_event_count"] == len(first_turn) - 1
                    break
                replayed.append(event)

        assert [event["event_id"] for event in replayed] == [
            event["event_id"] for event in first_turn[1:]
        ]
        assert client.get("/v1/sessions/socket-session").json()["state"][
            "turn_count"
        ] == 1


def test_websocket_rejects_system_protocol_commands(runtime_factory):
    runtime = runtime_factory()
    app = create_app(runtime, close_runtime=False)

    with TestClient(app) as client:
        with client.websocket_connect("/v1/sessions/member-only/stream") as websocket:
            assert websocket.receive_json()["type"] == "session.ready"
            websocket.send_json({"type": "catalog.deactivate", "skill": "balance"})
            error = websocket.receive_json()

    assert error["type"] == "protocol.error"
    assert runtime.inspect_state("member-only")["turn_count"] == 0


def test_session_events_fan_out_to_multiple_connected_clients(runtime_factory):
    runtime = runtime_factory()
    app = create_app(runtime, close_runtime=False)

    with TestClient(app) as client:
        with client.websocket_connect("/v1/sessions/shared-room/stream") as member:
            assert member.receive_json()["type"] == "session.ready"
            with client.websocket_connect(
                "/v1/sessions/shared-room/stream"
            ) as observer:
                assert observer.receive_json()["type"] == "session.ready"
                member.send_json(
                    {
                        "type": "member.message",
                        "message_id": "shared-message-1",
                        "content": "what is my balance",
                    }
                )

                member_events = []
                observer_events = []
                while True:
                    event = member.receive_json()
                    member_events.append(event)
                    if event.get("final"):
                        break
                while True:
                    event = observer.receive_json()
                    observer_events.append(event)
                    if event.get("final"):
                        break

    assert [event["event_id"] for event in member_events] == [
        event["event_id"] for event in observer_events
    ]
