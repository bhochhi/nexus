from pathlib import Path
from textwrap import dedent

import pytest

from member_assistant.catalog import CatalogValidationError, SkillCatalog
from member_assistant.config import PROJECT_ROOT
from member_assistant.skill_authoring import FileSkillPublisher, SkillMarkdownCompiler


ONLINE_ID = (
    PROJECT_ROOT / "skills" / "available" / "online_id" / "SKILL.md"
)


def _guided_source(path: Path, version: str, label: str) -> Path:
    path.write_text(
        dedent(
            """\
            ---
            apiVersion: nexus.skills/v1
            kind: Skill
            metadata:
              name: configurable_advisory
              version: {version}
              owner: Business Demo
            intent:
              description: Demonstrates a version-pinned guided conversation.
              goals:
                - name: start_advisory
                  display_name: start an advisory conversation
                  keywords: [start advisory]
              input_schema:
                type: object
                properties:
                  answer:
                    type: string
            behavior:
              archetype: configurable_guided
              interaction: guided
              execution: workflow
              lifecycle: synchronous
            governance:
              risk_tier: informational
            implementation:
              tools: []
              response_template: "{label} saved {{answer}}."
              workflow:
                version: 1
                steps:
                  - op: collect
                    fields:
                      - name: answer
                        prompt: "{label} question: what should I save?"
                  - op: respond
                    template: "{label} saved {{answer}}."
                    values:
                      answer: $inputs.answer
                    outcome:
                      status: completed
            acceptance:
              - id: starts-guided-flow
                utterance: start advisory
                expect:
                  skill: configurable_advisory
                  goal: start_advisory
                  outcome: completed
            ---

            # Configurable advisory

            This body is business documentation and is packaged with the immutable artifact.
            """
        ).format(version=version, label=label),
        encoding="utf-8",
    )
    return path


def test_one_skill_markdown_can_add_a_custom_archetype_without_python(
    runtime_factory, tmp_path
):
    source = tmp_path / "SKILL.md"
    source.write_text(
        dedent(
            """\
            ---
            apiVersion: nexus.skills/v1
            kind: Skill
            metadata:
              name: demo_welcome
              version: 1.0.0
              owner: Member Experience
            intent:
              description: Gives a configured welcome response.
              goals:
                - name: request_demo_welcome
                  keywords: [demo welcome]
              input_schema:
                type: object
                properties: {}
            behavior:
              archetype: member_conversation
              interaction: direct
              execution: response
              lifecycle: synchronous
            governance:
              risk_tier: informational
            implementation:
              tools: []
              static_response:
                template: Welcome from a business-authored skill.
                outcome:
                  status: completed
            acceptance:
              - id: welcome
                utterance: give me the demo welcome
                expect:
                  skill: demo_welcome
                  goal: request_demo_welcome
                  outcome: completed
            ---

            # Demo welcome

            This custom archetype still compiles to the platform's safe response operation.
            """
        ),
        encoding="utf-8",
    )
    runtime = runtime_factory()
    original_graph = runtime.graph

    runtime.catalog.install(source, runtime.tools.contracts())
    reply = runtime.chat("custom-archetype", "give me the demo welcome")

    assert runtime.graph is original_graph
    assert reply.selected_skill == "demo_welcome"
    assert "business-authored skill" in reply.text
    assert runtime.executors.get("member_conversation") is not None


def test_publication_is_immutable_idempotent_and_rollbackable(tmp_path):
    compiler = SkillMarkdownCompiler()
    publisher = FileSkillPublisher(tmp_path / "catalog")
    compiled = compiler.compile(ONLINE_ID)

    first = publisher.publish(compiled)
    repeated = publisher.publish(compiled)

    assert first.idempotent is False
    assert repeated.idempotent is True
    assert first.artifact_path == repeated.artifact_path

    conflicting = tmp_path / "conflicting.md"
    conflicting.write_text(
        ONLINE_ID.read_text(encoding="utf-8").replace(
            "approved recovery journey", "approved digital recovery journey"
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogValidationError, match="immutable"):
        publisher.publish(compiler.compile(conflicting))

    next_source = tmp_path / "next.md"
    next_source.write_text(
        ONLINE_ID.read_text(encoding="utf-8").replace("3.0.0", "3.1.0", 1),
        encoding="utf-8",
    )
    next_receipt = publisher.publish(compiler.compile(next_source))
    catalog = SkillCatalog(tmp_path / "catalog")
    assert catalog.routes()[0].version == "3.1.0"

    publisher.activate(first.name, first.version, first.artifact_hash)
    catalog.refresh(force=True)
    assert catalog.routes()[0].version == "3.0.0"
    assert {item["version"] for item in publisher.list_versions(first.name)} == {
        "3.0.0",
        "3.1.0",
    }
    assert next_receipt.artifact_hash != first.artifact_hash


def test_catalog_loads_routing_metadata_before_full_artifact(tmp_path):
    compiled = SkillMarkdownCompiler().compile(ONLINE_ID)
    FileSkillPublisher(tmp_path / "catalog").publish(compiled)

    catalog = SkillCatalog(tmp_path / "catalog")

    assert catalog.routes()[0].name == "online_id_recovery"
    assert catalog._versions == {}
    definition = catalog.get("online_id_recovery")
    assert definition is not None
    assert definition.artifact_hash == compiled.definition.artifact_hash
    assert len(catalog._versions) == 1


def test_paused_task_resumes_with_pinned_version_after_publish_and_restart(
    runtime_factory, tmp_path
):
    catalog_dir = tmp_path / "catalog"
    first_runtime = runtime_factory(
        db_name="version-pin.db", catalog_dir=catalog_dir
    )
    v1 = _guided_source(tmp_path / "v1.md", "1.0.0", "V1")
    v2 = _guided_source(tmp_path / "v2.md", "2.0.0", "V2")
    first_runtime.catalog.install(v1, first_runtime.tools.contracts())

    prompt = first_runtime.chat("pinned", "start advisory")
    task = first_runtime.inspect_state("pinned")["active_task"]
    assert "V1 question" in prompt.text
    assert task["skill_version"] == "1.0.0"
    assert task["skill_artifact_hash"]

    first_runtime.catalog.install(v2, first_runtime.tools.contracts())
    first_runtime.close()
    second_runtime = runtime_factory(
        db_name="version-pin.db", catalog_dir=catalog_dir
    )

    resumed = second_runtime.chat("pinned", "blue")
    new_work = second_runtime.chat("new-version", "start advisory")

    assert "V1 saved blue" in resumed.text
    assert "V2 question" in new_work.text
    route = next(
        item
        for item in second_runtime.catalog.routes()
        if item.name == "configurable_advisory"
    )
    assert route.version == "2.0.0"


def test_publication_rejects_a_missing_tool_dependency(tmp_path):
    text = ONLINE_ID.read_text(encoding="utf-8").replace(
        "mock_approved_navigation", "future_navigation_tool"
    )
    source = tmp_path / "missing-tool.md"
    source.write_text(text, encoding="utf-8")

    with pytest.raises(CatalogValidationError, match="not installed"):
        SkillMarkdownCompiler().compile(
            source, {"mock_approved_navigation": ("open_destination",)}
        )
