from member_assistant.config import Settings
from member_assistant.providers import DeterministicProvider, build_provider


def test_openai_is_default_provider(monkeypatch, tmp_path):
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = Settings.from_env(
        tmp_path / "missing.env", tmp_path / "missing-project.env"
    )

    assert settings.provider_name == "openai"
    assert settings.model_id == "gpt-5.6-luna"
    assert settings.model_reasoning_effort == "low"
    assert settings.session_ttl_seconds == 600.0
    provider = build_provider(settings)
    assert isinstance(provider, DeterministicProvider)
    assert provider.observability_metadata()["fallback_used"] is True
    assert provider.observability_metadata()["fallback_reason"] == "missing_api_key"


def test_dotenv_is_loaded_and_process_environment_wins(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "MODEL_PROVIDER=mock\n"
        "MODEL_ID=file-model\n"
        "MODEL_REASONING_EFFORT=medium\n"
        "SESSION_TTL_SECONDS=900\n"
        "CATALOG_POLL_SECONDS=0.25\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("CATALOG_POLL_SECONDS", raising=False)
    monkeypatch.setenv("MODEL_ID", "process-model")

    settings = Settings.from_env(env_file, tmp_path / "missing-project.env")

    assert settings.provider_name == "mock"
    assert settings.model_id == "process-model"
    assert settings.model_reasoning_effort == "medium"
    assert settings.session_ttl_seconds == 900.0
    assert settings.catalog_poll_seconds == 0.25


def test_secret_file_location_can_be_overridden(tmp_path, monkeypatch):
    env_file = tmp_path / "alternate.env"
    env_file.write_text("MODEL_PROVIDER=mock\nMODEL_ID=alternate-model\n", encoding="utf-8")
    monkeypatch.setenv("MEMBER_ASSISTANT_ENV_FILE", str(env_file))
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("MODEL_ID", raising=False)

    settings = Settings.from_env(project_env_file=tmp_path / "missing-project.env")

    assert settings.provider_name == "mock"
    assert settings.model_id == "alternate-model"


def test_trace_configuration_is_loaded_from_secret_file(tmp_path, monkeypatch):
    env_file = tmp_path / "trace.env"
    env_file.write_text(
        "TRACE_BACKENDS=console,langfuse\n"
        "TRACE_CONSOLE_FORMAT=json\n"
        "TRACE_INCLUDE_CONTENT=true\n"
        "TRACE_HASH_SESSION_ID=false\n"
        "LANGFUSE_BASE_URL=http://localhost:3333\n",
        encoding="utf-8",
    )
    for name in (
        "TRACE_BACKENDS",
        "TRACE_CONSOLE_FORMAT",
        "TRACE_INCLUDE_CONTENT",
        "TRACE_HASH_SESSION_ID",
        "LANGFUSE_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env(env_file, tmp_path / "missing-project.env")

    assert settings.trace_backends == ("console", "langfuse")
    assert settings.trace_console_format == "json"
    assert settings.trace_include_content is True
    assert settings.trace_hash_session_id is False
    assert settings.langfuse_base_url == "http://localhost:3333"


def test_project_and_secret_env_files_are_merged_with_documented_precedence(
    tmp_path, monkeypatch
):
    project_env = tmp_path / ".env"
    secret_env = tmp_path / "dev.env"
    project_env.write_text(
        "MODEL_PROVIDER=mock\nMODEL_ID=project-model\nTRACE_LOG_LEVEL=DEBUG\n",
        encoding="utf-8",
    )
    secret_env.write_text(
        "MODEL_ID=secret-model\nTRACE_BACKENDS=console,langfuse\n",
        encoding="utf-8",
    )
    for name in ("MODEL_PROVIDER", "MODEL_ID", "TRACE_LOG_LEVEL", "TRACE_BACKENDS"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env(secret_env, project_env)

    assert settings.provider_name == "mock"  # project .env fallback
    assert settings.model_id == "secret-model"  # user secret overrides project
    assert settings.trace_log_level == "DEBUG"  # project .env fallback
    assert settings.trace_backends == ("console", "langfuse")

    monkeypatch.setenv("MODEL_ID", "process-model")
    assert Settings.from_env(secret_env, project_env).model_id == "process-model"
