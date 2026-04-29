"""
Nexus — Global configuration.
"""
import os


class Config:
    """Application configuration with sensible defaults."""

    # LLM
    LLM_MODEL_ID: str = os.getenv("NEXUS_LLM_MODEL", "amazon.nova-pro-v1:0")
    LLM_REGION: str = os.getenv("NEXUS_LLM_REGION", "us-east-1")

    # Session
    DEFAULT_MEMBER_ID: str = "member_default"
    SESSION_TIMEOUT_MINUTES: int = 30
    LIVE_AGENT_IDLE_TIMEOUT_SECONDS: int = 120  # 2 minutes

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    AGENTS_DIR: str = os.path.join(BASE_DIR, "agents")

    # Debug
    DEBUG: bool = os.getenv("NEXUS_DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("NEXUS_LOG_LEVEL", "INFO")

    # Contact Center
    WS_HOST: str = os.getenv("NEXUS_WS_HOST", "localhost")
    WS_PORT: int = int(os.getenv("NEXUS_WS_PORT", "8765"))
