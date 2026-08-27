import time

from member_assistant.config import PROJECT_ROOT


def _install_navigation(runtime):
    source = (
        PROJECT_ROOT
        / "skills"
        / "available"
        / "online_id_recovery"
        / "SKILL.md"
    )
    return runtime.catalog.install(source)


def test_hot_discovery_then_interrupt_and_resume(runtime_factory):
    runtime = runtime_factory()
    original_graph = runtime.graph
    first = runtime.chat("interrupt", "What is my balance?")
    assert "Which account" in first.text
    assert runtime.catalog.get("online_id_recovery") is None

    revision = runtime.catalog.revision
    _install_navigation(runtime)
    deadline = time.monotonic() + 1
    while runtime.catalog.revision == revision and time.monotonic() < deadline:
        time.sleep(0.01)

    assert runtime.catalog.get("online_id_recovery") is not None
    assert runtime.graph is original_graph

    interrupted = runtime.chat("interrupt", "I forgot my online ID")
    assert "online-id recovery" in interrupted.text.casefold()
    assert "resume or discard" in interrupted.text
    state = runtime.inspect_state("interrupt")
    assert state["paused_tasks"][0]["skill_name"] == "guided_balance"
    assert state["awaiting_resume"] is True

    resumed = runtime.chat("interrupt", "resume")
    assert "Resuming" in resumed.text
    assert "Which account" in resumed.text
    completed = runtime.chat("interrupt", "checking")
    assert "$2,450.75" in completed.text


def test_interruption_can_be_discarded(runtime_factory):
    runtime = runtime_factory()
    _install_navigation(runtime)
    runtime.chat("discard", "What is my balance?")
    runtime.chat("discard", "I forgot my online ID")

    reply = runtime.chat("discard", "discard")

    assert "discarded" in reply.text
    state = runtime.inspect_state("discard")
    assert state["active_task"] is None
    assert state["paused_tasks"] == []
    assert state["awaiting_resume"] is False


def test_invalid_hot_edit_retains_last_valid_skill(runtime_factory):
    runtime = runtime_factory()
    _install_navigation(runtime)
    valid = runtime.catalog.get("online_id_recovery")
    assert valid is not None

    index = runtime.catalog.directory / "active.yaml"
    index.write_text("skills: [not a valid catalog", encoding="utf-8")
    runtime.catalog.refresh(force=True)

    retained = runtime.catalog.get("online_id_recovery")
    assert retained == valid
    assert "active.yaml" in runtime.catalog.errors


def test_unpublished_skill_file_does_not_change_active_catalog(runtime_factory):
    runtime = runtime_factory()
    before = {skill.name for skill in runtime.catalog.list()}
    draft_directory = runtime.catalog.directory / "unpublished" / "1.0.0"
    draft_directory.mkdir(parents=True)
    draft = draft_directory / "SKILL.md"
    draft.write_text("not a valid skill", encoding="utf-8")

    runtime.catalog.refresh(force=True)

    assert {skill.name for skill in runtime.catalog.list()} == before
    assert "unpublished" not in {skill.name for skill in runtime.catalog.routes()}
