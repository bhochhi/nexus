from copy import deepcopy

import pytest

from member_assistant.catalog import (
    BUILTIN_ARCHETYPES,
    CatalogValidationError,
    SkillDefinition,
)
from member_assistant.config import PROJECT_ROOT
from member_assistant.skill_authoring import SkillMarkdownCompiler


def test_archetypes_are_authoring_patterns_not_business_capabilities(runtime_factory):
    runtime = runtime_factory()

    assert BUILTIN_ARCHETYPES == {
        "knowledge",
        "guided_resolution",
        "deterministic_workflow",
        "navigation",
        "human_handoff",
    }
    assert runtime.executors.supported_archetypes == BUILTIN_ARCHETYPES
    assert "balance" not in runtime.executors.supported_archetypes
    assert "transfer" not in runtime.executors.supported_archetypes


def test_new_guided_skill_is_added_with_skill_markdown_only(runtime_factory, tmp_path):
    runtime = runtime_factory()
    graph = runtime.graph
    balance = (
        PROJECT_ROOT
        / "skills"
        / "catalog"
        / "guided_balance"
        / "2.0.0"
        / "SKILL.md"
    )
    text = balance.read_text(encoding="utf-8")
    replacements = {
        "name: guided_balance": "name: account_snapshot",
        "version: 2.0.0": "version: 1.0.0",
        "owner: Deposit Servicing": "owner: POC Configuration Test",
        "name: check_account_balance": "name: show_account_snapshot",
        "display_name: check an account balance": "display_name: show an account snapshot",
        "keywords: [balance, how much money, available funds]": "keywords: [account snapshot]",
        "utterance: What is my balance?": "utterance: Show my savings account snapshot",
        "skill: guided_balance": "skill: account_snapshot",
        "goal: check_account_balance": "goal: show_account_snapshot",
        'response_template: "Mock balance: {items}."': (
            'response_template: "Configured account snapshot: {items}."'
        ),
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    skill_directory = tmp_path / "account_snapshot"
    skill_directory.mkdir()
    source = skill_directory / "SKILL.md"
    source.write_text(text, encoding="utf-8")

    runtime.catalog.install(source, runtime.tools.contracts())

    reply = runtime.chat("configured-skill", "Show my savings account snapshot")

    assert runtime.graph is graph
    assert reply.selected_skill == "account_snapshot"
    assert "Configured account snapshot" in reply.text
    assert "$8,250.25" in reply.text


def test_catalog_rejects_a_consequential_call_not_immediately_after_confirmation(
    runtime_factory, tmp_path
):
    runtime = runtime_factory()
    source = (
        PROJECT_ROOT
        / "skills"
        / "catalog"
        / "internal_transfer"
        / "2.0.0"
        / "SKILL.md"
    )
    definition = deepcopy(SkillMarkdownCompiler().compile(source).definition_payload)
    steps = definition["workflow"]["steps"]
    confirm_index = next(index for index, step in enumerate(steps) if step["op"] == "confirm")
    steps.insert(confirm_index + 1, {"op": "set", "value": "unsafe-gap", "save_as": "gap"})

    with pytest.raises(CatalogValidationError, match="immediately follow confirmation"):
        SkillDefinition.from_dict(definition, tmp_path / "unsafe.json")
