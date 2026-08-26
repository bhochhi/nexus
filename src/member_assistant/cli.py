"""Local command-line demonstration."""

import argparse
from dataclasses import replace
import json
import logging
import os
from pathlib import Path
import sys
from typing import Optional, Sequence

from member_assistant.config import Settings
from member_assistant.runtime import AgentRuntime


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agentic Member Assistant POC")
    parser.add_argument("--session", default="demo-session", help="durable session identifier")
    parser.add_argument("--provider", choices=("openai", "mock"), help="model provider override")
    parser.add_argument("--db", type=Path, help="SQLite state path override")
    parser.add_argument(
        "--session-ttl-minutes",
        type=float,
        help="expire inactive conversation state after this many minutes; 0 disables TTL",
    )
    parser.add_argument("--catalog", type=Path, help="active skill-catalog path override")
    parser.add_argument(
        "--trace",
        choices=("off", "console", "langfuse", "both"),
        help="trace destination override",
    )
    content = parser.add_mutually_exclusive_group()
    content.add_argument(
        "--trace-content",
        action="store_true",
        dest="trace_content",
        help="include mock prompts, tool values, and replies in traces",
    )
    content.add_argument(
        "--no-trace-content",
        action="store_false",
        dest="trace_content",
        help="redact prompt, tool, and response content (default)",
    )
    parser.set_defaults(trace_content=None)
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="console trace and application log level",
    )
    parser.add_argument(
        "--trace-format",
        choices=("pretty", "json"),
        help="interactive or machine-readable console traces",
    )
    return parser


def _color(text: str, code: str, enabled: bool) -> str:
    return "\033[{}m{}\033[0m".format(code, text) if enabled else text


def _provider_line(settings: Settings, runtime: AgentRuntime, *, turn: bool = False) -> str:
    metadata = runtime.provider.observability_metadata()
    active = str(metadata.get("provider", runtime.provider.name))
    requested = str(metadata.get("configured_provider", settings.provider_name))
    requested_runtime = (
        "deterministic" if requested in {"mock", "deterministic"} else requested
    )
    fallback_used = bool(metadata.get("fallback_used")) or active != requested_runtime
    parts = [
        "requested={}".format(requested),
        "active={}".format(active),
        "model={}".format(metadata.get("model", runtime.provider.model_id)),
        "fallback={}".format("USED" if fallback_used else "not used"),
    ]
    if metadata.get("api_endpoint"):
        parts.append("endpoint={}".format(metadata["api_endpoint"]))
    if metadata.get("reasoning_effort"):
        parts.append("reasoning={}".format(metadata["reasoning_effort"]))
    if not turn:
        policy = (
            "not applicable"
            if requested_runtime == "deterministic"
            else "enabled" if settings.allow_provider_fallback else "disabled"
        )
        parts.append(
            "fallback_policy={}".format(policy)
        )
    reason = metadata.get("fallback_reason") or metadata.get("failure_type")
    if reason:
        parts.append("reason={}".format(reason))
    if metadata.get("provider_status"):
        parts.append("http_status={}".format(metadata["provider_status"]))
    if metadata.get("provider_error_code"):
        parts.append("error_code={}".format(metadata["provider_error_code"]))
    if metadata.get("provider_error_param"):
        parts.append("error_param={}".format(metadata["provider_error_param"]))
    return " | ".join(parts)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    if args.provider:
        settings = replace(settings, provider_name=args.provider)
    if args.db:
        settings = replace(settings, state_db_path=args.db)
    if args.session_ttl_minutes is not None:
        if args.session_ttl_minutes < 0:
            parser.error("--session-ttl-minutes must be zero or greater")
        settings = replace(
            settings, session_ttl_seconds=args.session_ttl_minutes * 60.0
        )
    if args.catalog:
        settings = replace(settings, catalog_path=args.catalog)
    if args.trace:
        backends = {
            "off": (),
            "console": ("console",),
            "langfuse": ("langfuse",),
            "both": ("console", "langfuse"),
        }[args.trace]
        settings = replace(settings, trace_backends=backends)
    if args.trace_content is not None:
        settings = replace(settings, trace_include_content=args.trace_content)
    if args.log_level:
        settings = replace(settings, trace_log_level=args.log_level)
    if args.trace_format:
        settings = replace(settings, trace_console_format=args.trace_format)

    logging.basicConfig(
        level=getattr(logging, settings.trace_log_level, logging.INFO),
        format="%(message)s",
    )

    runtime = AgentRuntime.from_settings(settings)
    color_enabled = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    print(_color("Agentic Member Assistant POC", "1;36", color_enabled))
    provider_line = _provider_line(settings, runtime)
    provider_warning = "fallback=USED" in provider_line
    print(
        _color(
            "Model: " + provider_line,
            "33" if provider_warning else "32",
            color_enabled,
        )
    )
    print("Mock member data and tools only")
    ttl = settings.session_ttl_seconds
    print(
        "Session TTL: {}".format(
            "disabled"
            if ttl <= 0
            else "{:g} minutes".format(ttl / 60.0)
        )
    )
    print(
        "Commands: /skills, /state, /trace, /add-online-id, "
        "/remove-online-id, /quit"
    )
    try:
        while True:
            try:
                prompt = "\033[1;34mmember> " if color_enabled else "member> "
                message = input(prompt).strip()
                if color_enabled:
                    print("\033[0m", end="", flush=True)
            except EOFError:
                if color_enabled:
                    print("\033[0m", end="", flush=True)
                break
            if not message:
                continue
            if message in {"/quit", "/exit"}:
                break
            if message == "/skills":
                print(
                    "assistant> Active skills: "
                    + ", ".join(skill.name for skill in runtime.catalog.routes())
                )
                if runtime.catalog.errors:
                    print("assistant> Catalog errors: " + json.dumps(runtime.catalog.errors))
                continue
            if message == "/state":
                print(json.dumps(runtime.inspect_state(args.session), indent=2, sort_keys=True))
                continue
            if message == "/trace":
                print(json.dumps(runtime.observability.describe(), indent=2, sort_keys=True))
                continue
            if message == "/add-online-id":
                source = (
                    settings.available_skills_path
                    / "online_id_recovery"
                    / "SKILL.md"
                )
                target = runtime.catalog.install(source, runtime.tools.contracts())
                print(
                    _color("assistant>", "1;32", color_enabled)
                    + " Installed {} at runtime; catalog revision is {}.".format(
                        target.name, runtime.catalog.revision
                    )
                )
                continue
            if message == "/remove-online-id":
                if any(
                    route.name == "online_id_recovery"
                    for route in runtime.catalog.routes()
                ):
                    runtime.catalog.deactivate("online_id_recovery")
                    response = (
                        "Deactivated online-ID recovery for new requests; its immutable "
                        "version history was retained."
                    )
                else:
                    response = "Online-ID recovery is already inactive."
                print(_color("assistant>", "1;32", color_enabled) + " " + response)
                continue
            if message.startswith("/"):
                print(
                    _color("error>", "1;31", color_enabled)
                    + " Unknown local command. Use /skills, /state, /trace, "
                    "/add-online-id, /remove-online-id, or /quit."
                )
                continue
            try:
                reply = runtime.chat(args.session, message)
                print(_color("assistant>", "1;32", color_enabled) + " " + reply.text)
                turn_line = _provider_line(settings, runtime, turn=True)
                turn_warning = "fallback=USED" in turn_line
                print(
                    _color(
                        "model(last call)> " + turn_line,
                        "33" if turn_warning else "2;37",
                        color_enabled,
                    )
                )
            except Exception as exc:
                print(
                    _color("error>", "1;31", color_enabled)
                    + " Safe runtime error: {}".format(exc)
                )
    finally:
        runtime.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
