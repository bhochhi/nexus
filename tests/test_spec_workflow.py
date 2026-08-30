import json

from member_assistant.config import PROJECT_ROOT
from member_assistant.spec_workflow import STAGES, evidence, main, select_stage, validate


def test_portable_specs_validate_without_loading_business_skill_artifacts():
    result = validate(PROJECT_ROOT)

    assert result["valid"] is True
    assert "specifications/platform/features/conversation-lifecycle.yaml" in result["features"]


def test_stage_selection_is_contextual_or_explicit():
    assert select_stage("Build the approved change")["active_stage"] == "implementation"
    assert select_stage("Create an implementation plan")["active_stage"] == "implementation_planning"
    assert select_stage("Prepare release evidence")["active_stage"] == "release_evidence"
    assert select_stage("anything", "promotion")["active_stage"] == "promotion"
    assert tuple(STAGES)[0] == "specification_analysis"


def test_cli_announces_stage_and_emits_reproducible_evidence(capsys):
    assert main(["select-stage", "--task", "please independently verify this change"]) == 0
    stage = json.loads(capsys.readouterr().out)
    assert stage == {"active_stage": "independent_verification", "selection": "task_context"}

    spec = PROJECT_ROOT / "workflow" / "spec-driven-development.yaml"
    first = evidence([spec])
    second = evidence([spec])
    assert first == second
    assert first["stage"] == "release_evidence"
