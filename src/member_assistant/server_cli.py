"""Command-line entry point for the WebSocket/HTTP service."""

import argparse
from dataclasses import replace
import logging
from pathlib import Path
from typing import Optional, Sequence

import uvicorn

from member_assistant.config import Settings
from member_assistant.runtime import AgentRuntime
from member_assistant.server import create_app


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agentic Member Assistant socket server")
    parser.add_argument("--host", help="bind host override")
    parser.add_argument("--port", type=int, help="bind port override")
    parser.add_argument(
        "--provider", choices=("openai", "bedrock", "mock"), help="provider override"
    )
    parser.add_argument("--model", help="model ID override")
    parser.add_argument("--db", type=Path, help="SQLite state path override")
    parser.add_argument("--catalog", type=Path, help="skill-catalog path override")
    parser.add_argument(
        "--session-ttl-minutes",
        type=float,
        help="expire inactive session state after this many minutes; 0 disables TTL",
    )
    parser.add_argument(
        "--trace", choices=("off", "console", "langfuse", "both"), help="trace override"
    )
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="application log level",
    )
    parser.add_argument(
        "--trace-format",
        choices=("pretty", "json"),
        help="console trace format override",
    )
    content = parser.add_mutually_exclusive_group()
    content.add_argument("--trace-content", action="store_true", dest="trace_content")
    content.add_argument(
        "--no-trace-content", action="store_false", dest="trace_content"
    )
    parser.set_defaults(trace_content=None)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    if args.provider:
        selected_model = {
            "openai": settings.openai_model_id,
            "bedrock": settings.bedrock_model_id,
            "mock": "deterministic",
        }[args.provider]
        settings = replace(
            settings, provider_name=args.provider, model_id=selected_model
        )
    if args.model:
        settings = replace(settings, model_id=args.model)
    if args.db:
        settings = replace(settings, state_db_path=args.db)
    if args.catalog:
        settings = replace(settings, catalog_path=args.catalog)
    if args.session_ttl_minutes is not None:
        if args.session_ttl_minutes < 0:
            parser.error("--session-ttl-minutes must be zero or greater")
        settings = replace(
            settings, session_ttl_seconds=args.session_ttl_minutes * 60.0
        )
    if args.trace:
        settings = replace(
            settings,
            trace_backends={
                "off": (),
                "console": ("console",),
                "langfuse": ("langfuse",),
                "both": ("console", "langfuse"),
            }[args.trace],
        )
    if args.log_level:
        settings = replace(settings, trace_log_level=args.log_level)
    if args.trace_format:
        settings = replace(settings, trace_console_format=args.trace_format)
    if args.trace_content is not None:
        settings = replace(settings, trace_include_content=args.trace_content)

    logging.basicConfig(
        level=getattr(logging, settings.trace_log_level, logging.INFO),
        format="%(message)s",
    )
    runtime = AgentRuntime.from_settings(settings)
    app = create_app(runtime, close_runtime=True)
    uvicorn.run(
        app,
        host=args.host or settings.server_host,
        port=args.port or settings.server_port,
        log_level=settings.trace_log_level.lower(),
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
