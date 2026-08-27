"""Local system operations kept separate from the member chat client."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from member_assistant.catalog import CatalogValidationError, SkillCatalog
from member_assistant.config import Settings
from member_assistant.skill_authoring import FileSkillPublisher, SkillMarkdownCompiler
from member_assistant.state_store import SQLiteConversationStore
from member_assistant.tools import MockTools


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Member Assistant system controls")
    parser.add_argument("--catalog", type=Path, help="skill catalog path override")
    parser.add_argument("--db", type=Path, help="SQLite state path override")
    parser.add_argument("--session", default="demo-session", help="session to inspect")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("skills", help="show active hot-reloaded skills")
    subparsers.add_parser("state", help="inspect durable conversation state")
    subparsers.add_parser("trace", help="show effective trace configuration")
    subparsers.add_parser(
        "add-online-id", help="publish the demo online-ID skill"
    )
    subparsers.add_parser(
        "remove-online-id", help="deactivate the demo online-ID skill"
    )
    return parser


def _trace_settings(settings: Settings) -> Dict[str, Any]:
    return {
        "backends": list(settings.trace_backends),
        "console_format": settings.trace_console_format,
        "include_content": settings.trace_include_content,
        "log_level": settings.trace_log_level,
        "environment": settings.trace_environment,
        "service_name": settings.trace_service_name,
        "langfuse_base_url": settings.langfuse_base_url,
        "hash_session_id": settings.trace_hash_session_id,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    settings = Settings.from_env()
    catalog_path = args.catalog or settings.catalog_path
    db_path = args.db or settings.state_db_path
    try:
        if args.command == "skills":
            catalog = SkillCatalog(catalog_path)
            try:
                output = {
                    "catalog_revision": catalog.revision,
                    "skills": [route.as_dict() for route in catalog.routes()],
                    "errors": catalog.errors,
                }
            finally:
                catalog.stop()
        elif args.command == "state":
            store = SQLiteConversationStore(
                db_path, session_ttl_seconds=settings.session_ttl_seconds
            )
            try:
                output = {
                    "session_id": args.session,
                    "state": store.inspect(args.session),
                    "events": [
                        event.as_dict()
                        for event in store.stream_events(args.session)
                    ],
                }
            finally:
                store.close()
        elif args.command == "trace":
            output = _trace_settings(settings)
        elif args.command == "add-online-id":
            source = (
                settings.available_skills_path
                / "online_id_recovery"
                / "SKILL.md"
            )
            compiled = SkillMarkdownCompiler().compile(
                source, MockTools.create(settings.knowledge_path).contracts()
            )
            receipt = FileSkillPublisher(catalog_path).publish(
                compiled, activate=True
            )
            output = {
                "name": receipt.name,
                "version": receipt.version,
                "artifact_hash": receipt.artifact_hash,
                "activated": receipt.activated,
                "idempotent": receipt.idempotent,
            }
        else:
            receipt = FileSkillPublisher(catalog_path).deactivate(
                "online_id_recovery"
            )
            output = {
                "name": receipt.name,
                "version": receipt.version,
                "artifact_hash": receipt.artifact_hash,
                "deactivated": receipt.deactivated,
            }
    except (CatalogValidationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
