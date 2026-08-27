import json
from pathlib import Path

from member_assistant.admin_cli import main as admin_main
from member_assistant.cli import _model_line, main
from member_assistant.config import PROJECT_ROOT
from member_assistant.skill_cli import main as skill_main


class _FakeSocket:
    def __init__(self, incoming):
        self.incoming = iter(incoming)
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def recv(self):
        return json.dumps(next(self.incoming))

    def send(self, payload):
        self.sent.append(json.loads(payload))


def test_model_metadata_is_rendered_from_completion_event():
    line = _model_line(
        {
            "provider": "bedrock",
            "model": "us.amazon.nova-2-lite-v1:0",
            "api_endpoint": "converse",
            "aws_region": "us-east-1",
            "fallback_used": False,
        }
    )

    assert "provider=bedrock" in line
    assert "model=us.amazon.nova-2-lite-v1:0" in line
    assert "endpoint=converse" in line
    assert "region=us-east-1" in line
    assert "fallback=not used" in line


def test_member_cli_sends_plain_conversation_over_websocket(monkeypatch, capsys):
    socket = _FakeSocket(
        [
            {
                "type": "session.ready",
                "session_id": "member-1",
                "catalog_revision": 7,
            },
            {"type": "turn.accepted", "final": False},
            {
                "type": "assistant.request_input",
                "content": "Which account would you like?",
                "final": False,
            },
            {
                "type": "turn.completed",
                "final": True,
                "metadata": {
                    "provider": "deterministic",
                    "model": "deterministic-catalog-router",
                    "fallback_used": False,
                },
            },
        ]
    )
    monkeypatch.setattr("websockets.sync.client.connect", lambda _: socket)
    messages = iter(["what is my balance"])

    def member_input(_):
        try:
            return next(messages)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr("builtins.input", member_input)

    assert main(["--session", "member-1", "--url", "ws://testserver"]) == 0

    assert len(socket.sent) == 1
    assert socket.sent[0]["type"] == "member.message"
    assert socket.sent[0]["content"] == "what is my balance"
    output = capsys.readouterr().out
    assert "Connected (catalog revision 7)" in output
    assert "assistant> Which account would you like?" in output
    assert "provider=deterministic" in output
    assert "/skills" not in output


def test_admin_cli_inspects_skills_outside_member_chat(tmp_path, capsys):
    catalog = tmp_path / "catalog"
    import shutil

    shutil.copytree(PROJECT_ROOT / "skills" / "catalog", catalog)

    assert admin_main(["--catalog", str(catalog), "skills"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["catalog_revision"] >= 1
    assert any(skill["name"] == "guided_balance" for skill in output["skills"])


def test_skill_cli_validates_publishes_and_lists_active_catalog(tmp_path, capsys):
    source = (
        PROJECT_ROOT
        / "skills"
        / "available"
        / "online_id_recovery"
        / "SKILL.md"
    )
    catalog = tmp_path / "catalog"

    assert skill_main(["--catalog", str(catalog), "validate", str(source)]) == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated["valid"] is True

    assert skill_main(["--catalog", str(catalog), "publish", str(source)]) == 0
    published = json.loads(capsys.readouterr().out)
    assert published["activated"] is True

    assert skill_main(["--catalog", str(catalog), "active"]) == 0
    active = json.loads(capsys.readouterr().out)
    assert active["skills"][0]["name"] == "online_id_recovery"

    assert skill_main(
        ["--catalog", str(catalog), "deactivate", "online_id_recovery"]
    ) == 0
    deactivated = json.loads(capsys.readouterr().out)
    assert deactivated["deactivated"] is True

    assert skill_main(["--catalog", str(catalog), "active"]) == 0
    assert json.loads(capsys.readouterr().out)["skills"] == []
