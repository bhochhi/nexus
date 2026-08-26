import shutil

import pytest

from member_assistant.catalog import SkillCatalog
from member_assistant.config import PROJECT_ROOT
from member_assistant.providers import DeterministicProvider
from member_assistant.runtime import AgentRuntime
from member_assistant.state_store import SQLiteConversationStore
from member_assistant.tools import MockTools


@pytest.fixture
def runtime_factory(tmp_path):
    runtimes = []

    def create(
        db_name="state.db",
        catalog_dir=None,
        tools=None,
        observability=None,
        provider=None,
    ):
        active = catalog_dir or tmp_path / "catalog"
        active.mkdir(exist_ok=True)
        if not (active / "active.yaml").exists():
            shutil.copytree(
                PROJECT_ROOT / "skills" / "catalog",
                active,
                dirs_exist_ok=True,
            )
        catalog = SkillCatalog(active, poll_seconds=0.02)
        store = SQLiteConversationStore(tmp_path / db_name)
        mock_tools = tools or MockTools.create(PROJECT_ROOT / "data" / "knowledge.json")
        runtime = AgentRuntime(
            catalog,
            store,
            provider or DeterministicProvider(),
            mock_tools,
            observability=observability,
        )
        runtimes.append(runtime)
        return runtime

    yield create

    for runtime in runtimes:
        try:
            runtime.close()
        except Exception:
            pass
