"""Portable specification workflow validation, stage selection, and evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import re
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

STAGE_SKILLS = {
    "specification_analysis": "nexus-specification-analysis",
    "specification_validation": "nexus-specification-validation",
    "impact_analysis": "nexus-impact-analysis",
    "implementation_planning": "nexus-implementation-planning",
    "implementation": "nexus-implementation",
    "independent_verification": "nexus-independent-verification",
    "release_evidence": "nexus-release-evidence",
    "promotion": "nexus-promotion",
}

CAPABILITY_ARCHETYPES = (
    "declarative",
    "guided",
    "navigation",
    "deterministic",
    "human_handoff",
)
CAPABILITY_STATUSES = ("draft", "in_review", "approved", "retired")

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


def _load_markdown(path: Path) -> tuple:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecificationValidationError("{}: {}".format(path, exc)) from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SpecificationValidationError(
            "{}: Markdown specification must start with YAML frontmatter".format(path)
        )
    try:
        closing = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise SpecificationValidationError(
            "{}: YAML frontmatter is not closed".format(path)
        ) from exc
    try:
        frontmatter = yaml.safe_load("\n".join(lines[1:closing])) or {}
    except yaml.YAMLError as exc:
        raise SpecificationValidationError(
            "{}: YAML frontmatter is invalid".format(path)
        ) from exc
    if not isinstance(frontmatter, dict):
        raise SpecificationValidationError(
            "{}: YAML frontmatter must be an object".format(path)
        )
    return frontmatter, "\n".join(lines[closing + 1 :]).strip()


def _require(payload: Dict[str, Any], keys: Iterable[str], path: Path) -> None:
    missing = [key for key in keys if not payload.get(key)]
    if missing:
        raise SpecificationValidationError("{}: missing {}".format(path, ", ".join(missing)))


def _require_headings(body: str, headings: Iterable[str], path: Path) -> None:
    missing = [heading for heading in headings if "## {}".format(heading) not in body]
    if missing:
        raise SpecificationValidationError(
            "{}: missing Markdown sections {}".format(path, ", ".join(missing))
        )


def validate(root: Path = PROJECT_ROOT) -> Dict[str, Any]:
    """Validate the intentionally small portable contract surface."""
    root = Path(root)
    workflow_path = root / "workflow" / "spec-driven-development.yaml"
    workflow = _load_yaml(workflow_path)
    _require(
        workflow,
        (
            "apiVersion",
            "kind",
            "constitution",
            "routerSkill",
            "stages",
            "stageSkills",
            "rules",
        ),
        workflow_path,
    )
    if tuple(workflow["stages"]) != STAGES:
        raise SpecificationValidationError("{}: stages must use the canonical lifecycle".format(workflow_path))
    expected_stage_skills = {
        stage: "workflow/skills/{}/SKILL.md".format(skill_name)
        for stage, skill_name in STAGE_SKILLS.items()
    }
    if workflow["stageSkills"] != expected_stage_skills:
        raise SpecificationValidationError(
            "{}: stageSkills must map every canonical stage".format(workflow_path)
        )
    if workflow["constitution"] != "specifications/constitution.md":
        raise SpecificationValidationError(
            "{}: constitution must reference the portable source".format(
                workflow_path
            )
        )
    if (
        workflow["routerSkill"]
        != "workflow/skills/nexus-spec-driven-development/SKILL.md"
    ):
        raise SpecificationValidationError(
            "{}: routerSkill must reference the portable router".format(
                workflow_path
            )
        )

    workflow_skill_paths = []
    for stage in STAGES:
        skill_path = (
            root
            / "workflow"
            / "skills"
            / STAGE_SKILLS[stage]
            / "SKILL.md"
        )
        skill, body = _load_markdown(skill_path)
        _require(skill, ("name", "description"), skill_path)
        if skill["name"] != STAGE_SKILLS[stage]:
            raise SpecificationValidationError(
                "{}: skill name must match its stage mapping".format(skill_path)
            )
        if "Workflow stage: {}".format(stage) not in body:
            raise SpecificationValidationError(
                "{}: skill must announce its workflow stage".format(skill_path)
            )
        workflow_skill_paths.append(skill_path)
    router_path = (
        root
        / "workflow"
        / "skills"
        / "nexus-spec-driven-development"
        / "SKILL.md"
    )
    router, router_body = _load_markdown(router_path)
    _require(router, ("name", "description"), router_path)
    if router["name"] != "nexus-spec-driven-development":
        raise SpecificationValidationError(
            "{}: invalid workflow router name".format(router_path)
        )
    for skill_name in STAGE_SKILLS.values():
        if skill_name not in router_body:
            raise SpecificationValidationError(
                "{}: router does not reference {}".format(router_path, skill_name)
            )
    workflow_skill_paths.insert(0, router_path)

    for adapter_path in (
        root / "AGENTS.md",
        root / ".github" / "copilot-instructions.md",
        root / "CLAUDE.md",
    ):
        try:
            adapter = adapter_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise SpecificationValidationError(
                "{}: {}".format(adapter_path, exc)
            ) from exc
        if "workflow/skills/nexus-spec-driven-development/SKILL.md" not in adapter:
            raise SpecificationValidationError(
                "{}: adapter must reference the portable workflow".format(
                    adapter_path
                )
            )

    constitution_path = root / "specifications" / "constitution.md"
    constitution, constitution_body = _load_markdown(constitution_path)
    _require(constitution, ("apiVersion", "kind", "metadata"), constitution_path)
    if constitution["kind"] != "PlatformConstitution":
        raise SpecificationValidationError(
            "{}: kind must be PlatformConstitution".format(constitution_path)
        )
    _require_headings(
        constitution_body,
        (
            "Purpose",
            "Principles",
            "Specification authority",
            "Safety and governance",
            "Quality gates",
            "Terminology",
        ),
        constitution_path,
    )

    adr_paths = sorted((root / "specifications" / "platform" / "adr").glob("*.md"))
    foundation_paths = sorted(
        (root / "specifications" / "platform" / "foundations").glob("*.md")
    )
    feature_paths = sorted((root / "specifications" / "platform" / "features").glob("*.md"))
    capability_paths = sorted(
        (root / "specifications" / "capabilities").glob("*/CAPABILITY.md")
    )
    contract_paths = sorted((root / "specifications" / "contracts").glob("*.yaml"))
    if (
        not adr_paths
        or not foundation_paths
        or not feature_paths
        or not capability_paths
        or not contract_paths
    ):
        raise SpecificationValidationError(
            "portable ADR, foundation, feature, capability, and contract specifications are required"
        )
    for path in adr_paths:
        decision, body = _load_markdown(path)
        _require(decision, ("apiVersion", "kind", "metadata", "enforcement"), path)
        if decision["kind"] != "ArchitectureDecision":
            raise SpecificationValidationError(
                "{}: kind must be ArchitectureDecision".format(path)
            )
        _require_headings(
            body,
            (
                "Context",
                "Decision",
                "Alternatives considered",
                "Consequences",
                "Enforcement",
                "Supersession",
            ),
            path,
        )
    for path in foundation_paths:
        foundation, body = _load_markdown(path)
        _require(foundation, ("apiVersion", "kind", "metadata", "interfaces"), path)
        if foundation["kind"] != "PlatformFoundation":
            raise SpecificationValidationError(
                "{}: kind must be PlatformFoundation".format(path)
            )
        _require_headings(
            body,
            (
                "Purpose",
                "Responsibilities",
                "Invariants",
                "Interfaces",
                "Failure behavior",
                "Verification",
            ),
            path,
        )
    for path in feature_paths:
        feature, body = _load_markdown(path)
        _require(feature, ("apiVersion", "kind", "metadata"), path)
        if feature["kind"] != "PlatformFeature":
            raise SpecificationValidationError(
                "{}: kind must be PlatformFeature".format(path)
            )
        _require_headings(
            body,
            (
                "Purpose",
                "Required behavior",
                "Acceptance criteria",
                "Examples",
                "Edge cases",
                "Verification",
            ),
            path,
        )
    acceptance_ids = set()
    for path in capability_paths:
        capability, body = _load_markdown(path)
        _require(
            capability,
            ("apiVersion", "kind", "metadata", "archetype", "risk"),
            path,
        )
        if capability["kind"] != "Capability":
            raise SpecificationValidationError(
                "{}: kind must be Capability".format(path)
            )
        metadata = capability["metadata"]
        if not isinstance(metadata, dict):
            raise SpecificationValidationError(
                "{}: metadata must be an object".format(path)
            )
        _require(metadata, ("id", "name", "status", "owner"), path)
        if metadata["status"] not in CAPABILITY_STATUSES:
            raise SpecificationValidationError(
                "{}: unsupported capability status {}".format(
                    path, metadata["status"]
                )
            )
        if capability["archetype"] not in CAPABILITY_ARCHETYPES:
            raise SpecificationValidationError(
                "{}: unsupported capability archetype {}".format(
                    path, capability["archetype"]
                )
            )
        _require_headings(
            body,
            (
                "Purpose and member value",
                "Scope",
                "Member scenarios",
                "Required behavior",
                "Acceptance criteria",
                "Examples",
                "Edge cases and failures",
                "Governance and integrations",
                "Verification",
            ),
            path,
        )
        path_acceptance_ids = re.findall(r"\*\*(AC-[A-Z0-9-]+)\s+—", body)
        if not path_acceptance_ids:
            raise SpecificationValidationError(
                "{}: at least one stable acceptance criterion ID is required".format(path)
            )
        duplicates = acceptance_ids.intersection(path_acceptance_ids)
        if duplicates:
            raise SpecificationValidationError(
                "{}: duplicate acceptance IDs {}".format(
                    path, ", ".join(sorted(duplicates))
                )
            )
        acceptance_ids.update(path_acceptance_ids)
        implementation = capability.get("implementation", {})
        if metadata["status"] == "approved" and not implementation:
            raise SpecificationValidationError(
                "{}: approved capability requires an implementation".format(path)
            )
        if implementation:
            if not isinstance(implementation, dict):
                raise SpecificationValidationError(
                    "{}: implementation must be an object".format(path)
                )
            skill_reference = implementation.get("skill")
            if metadata["status"] == "approved" and not skill_reference:
                raise SpecificationValidationError(
                    "{}: approved capability must reference a candidate skill".format(
                        path
                    )
                )
            skill_path = root / str(skill_reference) if skill_reference else None
            if skill_path is not None and not skill_path.is_file():
                raise SpecificationValidationError(
                    "{}: referenced skill does not exist: {}".format(
                        path, skill_reference
                    )
                )
            published_reference = implementation.get("publishedSkill")
            if published_reference and not (root / str(published_reference)).is_file():
                raise SpecificationValidationError(
                    "{}: referenced published skill does not exist: {}".format(
                        path, published_reference
                    )
                )
            if skill_path is not None:
                skill, _ = _load_markdown(skill_path)
                _require(skill, ("apiVersion", "kind", "metadata", "acceptance"), skill_path)
                if skill["kind"] != "Skill":
                    raise SpecificationValidationError(
                        "{}: kind must be Skill".format(skill_path)
                    )
                skill_metadata = skill["metadata"]
                traceability = (
                    skill_metadata.get("capability", {})
                    if isinstance(skill_metadata, dict)
                    else {}
                )
                if not isinstance(traceability, dict):
                    raise SpecificationValidationError(
                        "{}: metadata.capability must be an object".format(skill_path)
                    )
                expected_specification = str(path.relative_to(root))
                if (
                    traceability.get("id") != metadata["id"]
                    or traceability.get("specification") != expected_specification
                ):
                    raise SpecificationValidationError(
                        "{}: capability identity or specification reference does not match {}".format(
                            skill_path, path
                        )
                    )
                traced_acceptance = traceability.get("acceptance", [])
                if set(str(item) for item in traced_acceptance) != set(
                    path_acceptance_ids
                ):
                    raise SpecificationValidationError(
                        "{}: traceability must list every capability acceptance ID".format(
                            skill_path
                        )
                    )
                skill_acceptance = skill.get("acceptance", [])
                executable_ids = {
                    str(item.get("id"))
                    for item in skill_acceptance
                    if isinstance(item, dict) and item.get("id")
                }
                if not executable_ids or not executable_ids.issubset(
                    set(path_acceptance_ids)
                ):
                    raise SpecificationValidationError(
                        "{}: executable acceptance IDs must reference capability criteria".format(
                            skill_path
                        )
                    )
    for path in contract_paths:
        contract = _load_yaml(path)
        _require(contract, ("apiVersion", "kind", "contracts"), path)
        if not isinstance(contract["contracts"], list) or not contract["contracts"]:
            raise SpecificationValidationError("{}: contracts must be a non-empty list".format(path))

    return {
        "valid": True,
        "constitution": str(constitution_path.relative_to(root)),
        "workflow_skills": [
            str(path.relative_to(root)) for path in workflow_skill_paths
        ],
        "adrs": [str(path.relative_to(root)) for path in adr_paths],
        "foundations": [str(path.relative_to(root)) for path in foundation_paths],
        "features": [str(path.relative_to(root)) for path in feature_paths],
        "capabilities": [
            str(path.relative_to(root)) for path in capability_paths
        ],
        "contracts": [str(path.relative_to(root)) for path in contract_paths],
    }


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
