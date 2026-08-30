import json

import yaml

from member_assistant.catalog import BUILTIN_ARCHETYPES, RISK_TIERS, WORKFLOW_OPERATIONS
from member_assistant.config import PROJECT_ROOT
from member_assistant.spec_workflow import STAGES, evidence, main, select_stage, validate


def test_portable_specs_validate_without_loading_business_skill_artifacts():
    result = validate(PROJECT_ROOT)

    assert result["valid"] is True
    assert "specifications/platform/features/conversation-lifecycle.md" in result["features"]
    assert "specifications/platform/features/capability-authoring-and-delivery.md" in result["features"]
    assert "specifications/capabilities/internal-transfer/CAPABILITY.md" in result["capabilities"]


def test_stage_selection_is_contextual_or_explicit():
    assert select_stage("Build the approved change")["active_stage"] == "implementation"
    assert select_stage("Create an implementation plan")["active_stage"] == "implementation_planning"
    assert select_stage("Prepare release evidence")["active_stage"] == "release_evidence"
    assert select_stage("anything", "promotion")["active_stage"] == "promotion"
    assert tuple(STAGES)[0] == "specification_analysis"


def test_capability_archetype_templates_share_the_human_readable_standard():
    template_directory = PROJECT_ROOT / "specifications" / "templates" / "capabilities"
    expected = {"declarative", "guided", "navigation", "deterministic", "human-handoff"}

    assert {path.stem for path in template_directory.glob("*.md")} == expected
    for path in template_directory.glob("*.md"):
        body = path.read_text(encoding="utf-8")
        for heading in (
            "## Purpose and member value",
            "## Scope",
            "## Member scenarios",
            "## Required behavior",
            "## Acceptance criteria",
            "## Examples",
            "## Edge cases and failures",
            "## Governance and integrations",
            "## Verification",
        ):
            assert heading in body


def test_published_capability_surface_matches_runtime_primitives():
    path = (
        PROJECT_ROOT
        / "specifications"
        / "contracts"
        / "capability-runtime-contract.yaml"
    )
    contract_set = yaml.safe_load(path.read_text(encoding="utf-8"))
    surface = contract_set["contracts"][0]

    assert set(surface["authoring_profiles"].values()) == BUILTIN_ARCHETYPES
    assert set(surface["risk_tiers"]) == RISK_TIERS
    assert set(surface["workflow_operations"]) == WORKFLOW_OPERATIONS


def test_cli_announces_stage_and_emits_reproducible_evidence(capsys):
    assert main(["select-stage", "--task", "please independently verify this change"]) == 0
    stage = json.loads(capsys.readouterr().out)
    assert stage == {"active_stage": "independent_verification", "selection": "task_context"}

    spec = PROJECT_ROOT / "workflow" / "spec-driven-development.yaml"
    first = evidence([spec])
    second = evidence([spec])
    assert first == second
    assert first["stage"] == "release_evidence"
