import uuid

from fastapi.testclient import TestClient

from member_assistant.providers import DeterministicProvider
from member_assistant.server import create_app


class _GroundedHandoffSummaryProvider(DeterministicProvider):
    def generate_response(self, instruction, facts):
        if "human support representative" not in instruction:
            return super().generate_response(instruction, facts)
        transcript = facts["transcript"]
        assert any(
            item["content"] == "This is not helping, I want a person"
            for item in transcript
        )
        assert any(
            item["content"] == "My credit card balance is wrong"
            for item in transcript
        )
        return (
            "The member reports that their credit-card balance is wrong and asked "
            "for a person after the automated assistance was not helping. The issue "
            "remains unresolved and needs review by banking support."
        )


def _receive_until(websocket, event_type, limit=50):
    seen = []
    for _ in range(limit):
        event = websocket.receive_json()
        seen.append(event)
        if event.get("type") == event_type:
            return event, seen
    raise AssertionError("did not receive {}; saw {}".format(event_type, seen))


def _member_turn(websocket, content):
    websocket.send_json(
        {
            "type": "member.message",
            "message_id": "msg_{}".format(uuid.uuid4().hex),
            "content": content,
        }
    )
    completed, seen = _receive_until(websocket, "turn.completed")
    return completed, seen


def _queue_banking_handoff(member):
    _member_turn(member, "This is not helping, I want a person")
    _member_turn(member, "yes")
    _member_turn(member, "My credit card balance is wrong")
    completed, _ = _member_turn(member, "banking")
    assert completed["metadata"]["outcome_status"] == "queued"


def test_live_support_assigns_routes_messages_updates_sentiment_and_ends(
    runtime_factory,
):
    runtime = runtime_factory(provider=_GroundedHandoffSummaryProvider())
    app = create_app(runtime, close_runtime=False)

    with TestClient(app) as client:
        with client.websocket_connect(
            "/v1/live-support/agents/agent-1/stream"
        ) as agent:
            assert agent.receive_json()["type"] == "agent.connected"
            agent.send_json(
                {"type": "agent.join", "name": "Morgan", "queue": "banking"}
            )
            ready, _ = _receive_until(agent, "agent.ready")
            assert ready["queue"] == "banking"

            with client.websocket_connect(
                "/v1/sessions/member-live/stream"
            ) as member:
                assert member.receive_json()["type"] == "session.ready"
                member.send_json({"type": "member.join", "name": "Jordan Lee"})
                member_ready, _ = _receive_until(member, "member.ready")
                assert member_ready["member_name"] == "Jordan Lee"

                _queue_banking_handoff(member)
                assigned_member, _ = _receive_until(member, "live_support.assigned")
                assigned_agent, _ = _receive_until(agent, "live_support.assigned")

                case = assigned_agent["case"]
                assert case["case_id"] == assigned_member["case"]["case_id"]
                assert case["queue"] == "banking"
                assert case["agent_name"] == "Morgan"
                assert case["member_name"] == "Jordan Lee"
                assert case["summary"] == (
                    "Goal: My credit card balance is wrong\n"
                    "Reason: My credit card balance is wrong\nCompleted: none\n\n"
                    "Summary: The member reports that their credit-card balance is "
                    "wrong and asked for a person after the automated assistance was "
                    "not helping. The issue remains unresolved and needs review by "
                    "banking support."
                )
                assert assigned_agent["system_message"] == (
                    "[System message: Summary] {}".format(case["summary"])
                )
                assert "Recent context:" not in assigned_agent["system_message"]

                member.send_json(
                    {
                        "type": "member.message",
                        "message_id": "live-member-1",
                        "content": "I am so frustrated that my balance is still wrong",
                    }
                )
                live_message, _ = _receive_until(agent, "live.message")
                assert live_message["message"]["sender_type"] == "member"
                sentiment, _ = _receive_until(agent, "sentiment.updated")
                assert sentiment["sentiment"] == "frustrated"

                agent.send_json(
                    {
                        "type": "agent.message",
                        "case_id": case["case_id"],
                        "message_id": "live-agent-1",
                        "content": "I can help review that balance with you.",
                    }
                )
                response, _ = _receive_until(member, "live.message")
                if response["message"]["sender_type"] == "member":
                    response, _ = _receive_until(member, "live.message")
                assert response["message"]["sender_type"] == "agent"

                member.send_json(
                    {
                        "type": "member.message",
                        "message_id": "live-member-end",
                        "content": "/end",
                    }
                )
                ended, _ = _receive_until(member, "live_support.ended")
                assert ended["ended_by"] == "member"
                welcome, _ = _receive_until(member, "assistant.message")
                assert "back with the virtual assistant" in welcome["content"]
                _receive_until(agent, "live_support.ended")

    assert runtime.store.active_live_case("member-live") is None
    assert runtime.inspect_state("member-live")["handoff_status"] == "ended"


def test_waiting_member_can_cancel_and_return_to_virtual_assistant(runtime_factory):
    runtime = runtime_factory()
    app = create_app(runtime, close_runtime=False)

    with TestClient(app) as client:
        with client.websocket_connect("/v1/sessions/member-wait/stream") as member:
            assert member.receive_json()["type"] == "session.ready"
            member.send_json({"type": "member.join", "name": "Avery"})
            _receive_until(member, "member.ready")
            _queue_banking_handoff(member)
            waiting, _ = _receive_until(member, "live_support.waiting")
            assert waiting["case"]["status"] == "waiting"

            member.send_json({"type": "live_support.cancel"})
            cancelled, _ = _receive_until(member, "live_support.cancelled")
            assert cancelled["case"]["status"] == "cancelled"
            welcome, _ = _receive_until(member, "assistant.message")
            assert "What else can I help" in welcome["content"]

    assert runtime.store.active_live_case("member-wait") is None
