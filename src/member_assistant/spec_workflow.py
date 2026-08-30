"""Portable specification workflow validation, stage selection, and evidence."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence

import yaml

from member_assistant.config import PROJECT_ROOT


STAGES = (
    "specification_analysis",
    "specification_validation",
    "impact_analysis",
    "implementation_planning",
    "implementation",
    "independent_verification",
    "release_evidence",
    "promotion",
)

_KEYWORDS = (
    ("release_evidence", ("evidence", "provenance", "release notes")),
    ("independent_verification", ("verify", "review", "test", "audit")),
    ("implementation_planning", ("plan", "design", "approach")),
    ("implementation", ("implement", "build", "code", "fix")),
    ("impact_analysis", ("impact", "dependency", "affected")),
    ("specification_validation", ("validate spec", "validate contract")),
    ("specification_analysis", ("spec", "requirement", "analyse", "analyze")),
    ("promotion", ("promote", "deploy", "release")),
)


class SpecificationValidationError(ValueError):
    pass


def select_stage(task: str, requested_stage: Optional[str] = None) -> Dict[str, str]:
    """Select a lifecycle stage deterministically from a human task description."""
    if requested_stage:
        if requested_stage not in STAGES:
            raise SpecificationValidationError("unknown workflow stage: {}".format(requested_stage))
        return {"active_stage": requested_stage, "selection": "explicit"}
    normalized = task.lower()
    for stage, keywords in _KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return {"active_stage": stage, "selection": "task_context"}
    return {"active_stage": "specification_analysis", "selection": "default"}


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SpecificationValidationError("{}: {}".format(path, exc)) from exc
    if not isinstance(value, dict):
        raise SpecificationValidationError("{}: expected a YAML object".format(path))
    return value


def _require(payload: Dict[str, Any], keys: Iterable[str], path: Path) -> None:
    missing = [key for key in keys if not payload.get(key)]
    if missing:
        raise SpecificationValidationError("{}: missing {}".format(path, ", ".join(missing)))


def validate(root: Path = PROJECT_ROOT) -> Dict[str, Any]:
    """Validate the intentionally small portable contract surface."""
    root = Path(root)
    workflow_path = root / "workflow" / "spec-driven-development.yaml"
    workflow = _load_yaml(workflow_path)
    _require(workflow, ("apiVersion", "kind", "stages", "rules"), workflow_path)
    if tuple(workflow["stages"]) != STAGES:
        raise SpecificationValidationError("{}: stages must use the canonical lifecycle".format(workflow_path))

    feature_paths = sorted((root / "specifications" / "platform" / "features").glob("*.yaml"))
    contract_paths = sorted((root / "specifications" / "contracts").glob("*.yaml"))
    if not feature_paths or not contract_paths:
        raise SpecificationValidationError("portable feature and contract specifications are required")
    for path in feature_paths:
        feature = _load_yaml(path)
        _require(feature, ("apiVersion", "kind", "metadata", "behavior", "acceptance"), path)
        if feature["kind"] != "PlatformFeature" or not isinstance(feature["acceptance"], list):
            raise SpecificationValidationError("{}: invalid platform feature contract".format(path))
    for path in contract_paths:
        contract = _load_yaml(path)
        _require(contract, ("apiVersion", "kind", "contracts"), path)
        if not isinstance(contract["contracts"], list) or not contract["contracts"]:
            raise SpecificationValidationError("{}: contracts must be a non-empty list".format(path))

    return {"valid": True, "features": [str(path.relative_to(root)) for path in feature_paths], "contracts": [str(path.relative_to(root)) for path in contract_paths]}


def evidence(paths: Sequence[Path], root: Path = PROJECT_ROOT) -> Dict[str, Any]:
    """Return reproducible release evidence: sorted relative paths and SHA-256."""
    root = Path(root).resolve()
    records = []
    for path in sorted((Path(item).resolve() for item in paths), key=str):
        if not path.is_file():
            raise SpecificationValidationError("evidence input is not a file: {}".format(path))
        try:
            relative = str(path.relative_to(root))
        except ValueError:
            relative = str(path)
        records.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"stage": "release_evidence", "evidence": records}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Portable spec-driven development workflow")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    select = commands.add_parser("select-stage")
    select.add_argument("--task", default="")
    select.add_argument("--stage", choices=STAGES)
    proof = commands.add_parser("evidence")
    proof.add_argument("paths", nargs="+", type=Path)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            output = validate(args.root)
        elif args.command == "select-stage":
            output = select_stage(args.task, args.stage)
        else:
            output = evidence(args.paths, args.root)
    except SpecificationValidationError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
