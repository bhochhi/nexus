import json

import pytest

from member_assistant.catalog import CatalogValidationError, SKILL_TYPES, SkillDefinition


def test_skill_types_are_execution_patterns_not_business_capabilities(runtime_factory):
    runtime = runtime_factory()

    assert SKILL_TYPES == {
        "knowledge",
        "guided_resolution",
        "deterministic_workflow",
        "navigation",
        "human_handoff",
    }
    assert runtime.executors.supported_types == SKILL_TYPES
    assert "balance" not in runtime.executors.supported_types
    assert "transfer" not in runtime.executors.supported_types


def test_new_guided_skill_is_added_with_json_only(runtime_factory):
    runtime = runtime_factory()
    graph = runtime.graph
    source = runtime.catalog.directory / "balance.json"
    definition = json.loads(source.read_text(encoding="utf-8"))
    definition.update(
        {
            "name": "account_snapshot",
            "version": "1.0.0",
            "description": "Shows a configured snapshot using an existing approved tool.",
            "owner": "POC Configuration Test",
            "response_template": "Configured account snapshot: {items}.",
        }
    )
    definition["supported_goals"] = [
        {
            "name": "show_account_snapshot",
            "keywords": ["account snapshot"],
            "examples": ["Show my savings account snapshot"],
        }
    ]
    definition["workflow"]["steps"][-1]["template"] = (
        "Configured account snapshot: {items}."
    )
    added = runtime.catalog.directory / "account_snapshot.json"
    added.write_text(json.dumps(definition), encoding="utf-8")
    runtime.catalog.refresh()

    reply = runtime.chat("configured-skill", "Show my savings account snapshot")

    assert runtime.graph is graph
    assert reply.selected_skill == "account_snapshot"
    assert "Configured account snapshot" in reply.text
    assert "$8,250.25" in reply.text


def test_catalog_rejects_a_consequential_call_not_immediately_after_confirmation(
    runtime_factory, tmp_path
):
    runtime = runtime_factory()
    definition = json.loads(
        (runtime.catalog.directory / "transfer.json").read_text(encoding="utf-8")
    )
    steps = definition["workflow"]["steps"]
    confirm_index = next(index for index, step in enumerate(steps) if step["op"] == "confirm")
    steps.insert(confirm_index + 1, {"op": "set", "value": "unsafe-gap", "save_as": "gap"})

    with pytest.raises(CatalogValidationError, match="immediately follow confirmation"):
        SkillDefinition.from_dict(definition, tmp_path / "unsafe.json")
