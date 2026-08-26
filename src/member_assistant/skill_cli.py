"""Authoring and publication commands for the file-backed skill registry."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from member_assistant.catalog import CatalogValidationError, SkillCatalog
from member_assistant.config import Settings
from member_assistant.skill_authoring import FileSkillPublisher, SkillMarkdownCompiler
from member_assistant.tools import MockTools


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and publish immutable Nexus SKILL.md capabilities"
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        help="catalog directory (defaults to SKILL_CATALOG_PATH)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate", help="compile and validate a SKILL.md without publishing"
    )
    validate.add_argument("source", type=Path)

    publish = subparsers.add_parser(
        "publish", help="publish an immutable version and activate it"
    )
    publish.add_argument("source", type=Path)
    publish.add_argument(
        "--staged",
        action="store_true",
        help="store the version without changing the active catalog pointer",
    )

    subparsers.add_parser("active", help="show the lightweight active routing index")

    versions = subparsers.add_parser(
        "versions", help="list published immutable artifacts"
    )
    versions.add_argument("--name", help="limit results to one skill")

    activate = subparsers.add_parser(
        "activate", help="activate or roll back to a published artifact"
    )
    activate.add_argument("name")
    activate.add_argument("version")
    activate.add_argument("artifact_hash")

    deactivate = subparsers.add_parser(
        "deactivate", help="stop routing new work without deleting version history"
    )
    deactivate.add_argument("name")
    return parser


def _receipt(value: Any) -> Dict[str, Any]:
    return {
        "name": value.name,
        "version": value.version,
        "artifact_hash": value.artifact_hash,
        "artifact_path": str(value.artifact_path),
        "activated": value.activated,
        "idempotent": value.idempotent,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    catalog_path = args.catalog or settings.catalog_path
    compiler = SkillMarkdownCompiler()
    publisher = FileSkillPublisher(catalog_path)
    tool_contracts = MockTools.create(settings.knowledge_path).contracts()

    try:
        if args.command == "validate":
            compiled = compiler.compile(args.source, tool_contracts)
            output = {
                "valid": True,
                "name": compiled.definition.name,
                "version": compiled.definition.version,
                "artifact_hash": compiled.definition.artifact_hash,
                "archetype": compiled.definition.archetype,
                "behavior": {
                    "interaction": compiled.definition.interaction,
                    "execution": compiled.definition.execution,
                    "lifecycle": compiled.definition.lifecycle,
                },
                "acceptance_scenarios": len(compiled.acceptance),
            }
        elif args.command == "publish":
            compiled = compiler.compile(args.source, tool_contracts)
            output = _receipt(
                publisher.publish(compiled, activate=not args.staged)
            )
        elif args.command == "active":
            catalog = SkillCatalog(catalog_path)
            output = {
                "catalog_revision": catalog.revision,
                "skills": [route.as_dict() for route in catalog.routes()],
                "errors": catalog.errors,
            }
        elif args.command == "versions":
            output = {"versions": publisher.list_versions(args.name)}
        elif args.command == "activate":
            output = _receipt(
                publisher.activate(args.name, args.version, args.artifact_hash)
            )
        else:
            receipt = publisher.deactivate(args.name)
            output = {
                "name": receipt.name,
                "version": receipt.version,
                "artifact_hash": receipt.artifact_hash,
                "deactivated": receipt.deactivated,
            }
    except (CatalogValidationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
