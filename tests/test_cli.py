import json
from types import SimpleNamespace

from member_assistant.cli import _provider_line
from member_assistant.config import PROJECT_ROOT, Settings
from member_assistant.providers import DeterministicProvider
from member_assistant.skill_cli import main as skill_main


def test_mock_provider_is_not_reported_as_a_fallback():
    runtime = SimpleNamespace(provider=DeterministicProvider())
    line = _provider_line(Settings(provider_name="mock"), runtime)

    assert "requested=mock" in line
    assert "active=deterministic" in line
    assert "fallback=not used" in line
    assert "fallback_policy=not applicable" in line


def test_missing_openai_key_is_reported_as_an_active_fallback():
    runtime = SimpleNamespace(
        provider=DeterministicProvider(
            fallback_from="openai", fallback_reason="missing_api_key"
        )
    )
    line = _provider_line(Settings(provider_name="openai"), runtime)

    assert "requested=openai" in line
    assert "active=deterministic" in line
    assert "fallback=USED" in line
    assert "reason=missing_api_key" in line


def test_openai_responses_endpoint_and_reasoning_are_visible():
    provider = SimpleNamespace(
        name="openai",
        model_id="gpt-5.6-luna",
        observability_metadata=lambda: {
            "provider": "openai",
            "model": "gpt-5.6-luna",
            "api_endpoint": "responses",
            "reasoning_effort": "low",
            "fallback_used": False,
        },
    )
    runtime = SimpleNamespace(provider=provider)

    line = _provider_line(Settings(), runtime)

    assert "model=gpt-5.6-luna" in line
    assert "endpoint=responses" in line
    assert "reasoning=low" in line


def test_skill_cli_validates_publishes_and_lists_active_catalog(tmp_path, capsys):
    source = (
        PROJECT_ROOT / "skills" / "available" / "online_id" / "SKILL.md"
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
