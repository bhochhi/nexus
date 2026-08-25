"""Environment-backed runtime configuration."""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = Path.home() / ".secrets" / "dev.env"
PROJECT_ENV_FILE = PROJECT_ROOT / ".env"


def _as_bool(value: str) -> bool:
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _as_csv(value: str) -> Tuple[str, ...]:
    return tuple(item.strip().lower() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    """Configuration is intentionally independent of skills and graph nodes."""

    provider_name: str = "openai"
    model_id: str = "gpt-5.6-luna"
    model_reasoning_effort: str = "low"
    provider_api_key: Optional[str] = None
    allow_provider_fallback: bool = True
    catalog_path: Path = PROJECT_ROOT / "skills" / "catalog"
    available_skills_path: Path = PROJECT_ROOT / "skills" / "available"
    knowledge_path: Path = PROJECT_ROOT / "data" / "knowledge.json"
    state_db_path: Path = PROJECT_ROOT / "data" / "assistant_state.db"
    session_ttl_seconds: float = 600.0
    catalog_poll_seconds: float = 0.5
    trace_backends: Tuple[str, ...] = ("console",)
    trace_console_format: str = "pretty"
    trace_include_content: bool = False
    trace_log_level: str = "INFO"
    trace_environment: str = "local"
    trace_service_name: str = "agentic-member-assistant"
    trace_hash_session_id: bool = True
    langfuse_base_url: str = "http://localhost:3000"
    langfuse_public_key: Optional[str] = "pk-lf-member-assistant-local"
    langfuse_secret_key: Optional[str] = "sk-lf-member-assistant-local"

    @classmethod
    def from_env(
        cls,
        env_file: Optional[Path] = None,
        project_env_file: Optional[Path] = None,
    ) -> "Settings":
        """Load project and user files; real process variables take precedence.

        Precedence is process environment, the user secret file, the project
        ``.env`` file, and finally the built-in defaults. ``.env.example`` is
        documentation only and is never read.
        """

        configured_path = env_file or Path(
            os.getenv("MEMBER_ASSISTANT_ENV_FILE", str(DEFAULT_ENV_FILE))
        ).expanduser()
        project_path = (project_env_file or PROJECT_ENV_FILE).expanduser()
        project_values: Dict[str, Optional[str]] = dict(dotenv_values(project_path))
        secret_values: Dict[str, Optional[str]] = dict(dotenv_values(configured_path))

        def configured(name: str, default: Optional[str] = None) -> Optional[str]:
            process_value = os.getenv(name)
            if process_value is not None:
                return process_value
            secret_value = secret_values.get(name)
            if secret_value is not None:
                return secret_value
            project_value = project_values.get(name)
            if project_value is not None:
                return project_value
            return default

        provider = (configured("MODEL_PROVIDER", "openai") or "openai").strip().lower()
        provider_key = configured("MODEL_API_KEY")
        if provider == "openai":
            provider_key = provider_key or configured("OPENAI_API_KEY")
        return cls(
            provider_name=provider,
            model_id=configured("MODEL_ID", "gpt-5.6-luna") or "gpt-5.6-luna",
            model_reasoning_effort=(
                configured("MODEL_REASONING_EFFORT", "low") or "low"
            ).strip().lower(),
            provider_api_key=provider_key,
            allow_provider_fallback=_as_bool(
                configured("ALLOW_PROVIDER_FALLBACK", "true") or "true"
            ),
            catalog_path=Path(
                configured(
                    "SKILL_CATALOG_PATH", str(PROJECT_ROOT / "skills" / "catalog")
                )
                or str(PROJECT_ROOT / "skills" / "catalog")
            ),
            available_skills_path=Path(
                configured(
                    "AVAILABLE_SKILLS_PATH", str(PROJECT_ROOT / "skills" / "available")
                )
                or str(PROJECT_ROOT / "skills" / "available")
            ),
            knowledge_path=Path(
                configured(
                    "KNOWLEDGE_PATH", str(PROJECT_ROOT / "data" / "knowledge.json")
                )
                or str(PROJECT_ROOT / "data" / "knowledge.json")
            ),
            state_db_path=Path(
                configured(
                    "STATE_DB_PATH", str(PROJECT_ROOT / "data" / "assistant_state.db")
                )
                or str(PROJECT_ROOT / "data" / "assistant_state.db")
            ),
            session_ttl_seconds=max(
                0.0, float(configured("SESSION_TTL_SECONDS", "600") or "600")
            ),
            catalog_poll_seconds=float(configured("CATALOG_POLL_SECONDS", "0.5") or "0.5"),
            trace_backends=_as_csv(configured("TRACE_BACKENDS", "console") or "console"),
            trace_console_format=(
                configured("TRACE_CONSOLE_FORMAT", "pretty") or "pretty"
            ).lower(),
            trace_include_content=_as_bool(
                configured("TRACE_INCLUDE_CONTENT", "false") or "false"
            ),
            trace_log_level=(configured("TRACE_LOG_LEVEL", "INFO") or "INFO").upper(),
            trace_environment=configured("TRACE_ENVIRONMENT", "local") or "local",
            trace_service_name=(
                configured("TRACE_SERVICE_NAME", "agentic-member-assistant")
                or "agentic-member-assistant"
            ),
            trace_hash_session_id=_as_bool(
                configured("TRACE_HASH_SESSION_ID", "true") or "true"
            ),
            langfuse_base_url=(
                configured("LANGFUSE_BASE_URL", "http://localhost:3000")
                or "http://localhost:3000"
            ),
            langfuse_public_key=configured(
                "LANGFUSE_PUBLIC_KEY", "pk-lf-member-assistant-local"
            ),
            langfuse_secret_key=configured(
                "LANGFUSE_SECRET_KEY", "sk-lf-member-assistant-local"
            ),
        )
