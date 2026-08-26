"""Compile one business-facing SKILL.md into an immutable runtime artifact."""

from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence

import yaml

from member_assistant.catalog import (
    CatalogValidationError,
    SkillDefinition,
    SkillRoutingDefinition,
)


SKILL_API_VERSION = "nexus.skills/v1"
CATALOG_API_VERSION = "nexus.catalog/v1"


@dataclass(frozen=True)
class CompiledSkill:
    source: Path
    definition_payload: Mapping[str, Any]
    definition: SkillDefinition
    acceptance: List[Mapping[str, Any]]
    documentation: str

    @property
    def routing(self) -> SkillRoutingDefinition:
        return self.definition.routing_definition()

    def artifact_payload(self) -> Dict[str, Any]:
        return dict(self.definition_payload)


@dataclass(frozen=True)
class PublicationReceipt:
    name: str
    version: str
    artifact_hash: str
    artifact_path: Path
    activated: bool
    idempotent: bool


class SkillMarkdownCompiler:
    """Parse structured frontmatter and optional YAML sections from SKILL.md."""

    def compile(
        self,
        source: Path,
        tool_contracts: Optional[Mapping[str, Sequence[str]]] = None,
    ) -> CompiledSkill:
        source = Path(source)
        text = source.read_text(encoding="utf-8")
        frontmatter, body = self._frontmatter(text, source)
        payload, acceptance = self._normalize(frontmatter, body, source)
        if not acceptance:
            raise CatalogValidationError(
                "{}: at least one acceptance scenario is required".format(source.name)
            )
        self._validate_acceptance(acceptance, source)
        payload = {
            **payload,
            "acceptance": list(acceptance),
            "documentation": body.strip(),
        }
        definition = SkillDefinition.from_dict(payload, source)
        compiled = CompiledSkill(
            source=source,
            definition_payload=payload,
            definition=definition,
            acceptance=acceptance,
            documentation=body.strip(),
        )
        SkillPublicationValidator(tool_contracts).validate(compiled)
        return compiled

    @staticmethod
    def _frontmatter(text: str, source: Path) -> tuple:
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            raise CatalogValidationError(
                "{}: SKILL.md must start with YAML frontmatter".format(source.name)
            )
        try:
            closing = next(
                index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
            )
        except StopIteration as exc:
            raise CatalogValidationError(
                "{}: YAML frontmatter is not closed".format(source.name)
            ) from exc
        parsed = yaml.safe_load("\n".join(lines[1:closing])) or {}
        if not isinstance(parsed, dict):
            raise CatalogValidationError(
                "{}: YAML frontmatter must be an object".format(source.name)
            )
        return parsed, "\n".join(lines[closing + 1 :]).strip()

    def _normalize(
        self, frontmatter: Mapping[str, Any], body: str, source: Path
    ) -> tuple:
        api_version = frontmatter.get("apiVersion", SKILL_API_VERSION)
        if api_version != SKILL_API_VERSION:
            raise CatalogValidationError(
                "{}: unsupported apiVersion {}".format(source.name, api_version)
            )
        if frontmatter.get("kind", "Skill") != "Skill":
            raise CatalogValidationError("{}: kind must be Skill".format(source.name))

        metadata = self._mapping(frontmatter.get("metadata", {}), "metadata", source)
        intent = self._mapping(frontmatter.get("intent", {}), "intent", source)
        behavior = self._mapping(frontmatter.get("behavior", {}), "behavior", source)
        governance = self._mapping(
            frontmatter.get("governance", {}), "governance", source
        )
        implementation = self._mapping(
            frontmatter.get("implementation", {}), "implementation", source
        )

        skill_type = str(
            behavior.get("archetype", frontmatter.get("type", ""))
        ).strip()
        workflow = implementation.get("workflow") or frontmatter.get("workflow")
        if workflow is None:
            workflow = self._yaml_section(body, "Workflow")
        if workflow is None:
            workflow = self._synthesize_workflow(skill_type, implementation, source)

        acceptance = frontmatter.get("acceptance")
        if acceptance is None:
            acceptance = self._yaml_section(body, "Acceptance")
        if isinstance(acceptance, dict):
            acceptance = acceptance.get("scenarios", [])
        if not isinstance(acceptance, list):
            raise CatalogValidationError(
                "{}: acceptance must be a list of scenarios".format(source.name)
            )

        input_contract = intent.get(
            "input_schema", frontmatter.get("input_schema", {"type": "object", "properties": {}})
        )
        payload: Dict[str, Any] = {
            "apiVersion": api_version,
            "name": metadata.get("name", frontmatter.get("name")),
            "version": metadata.get("version", frontmatter.get("version")),
            "type": skill_type,
            "description": intent.get("description", frontmatter.get("description", "")),
            "owner": metadata.get("owner", frontmatter.get("owner", "")),
            "risk_tier": governance.get(
                "risk_tier", frontmatter.get("risk_tier", "informational")
            ),
            "supported_goals": intent.get(
                "goals", frontmatter.get("supported_goals", [])
            ),
            "input_schema": input_contract,
            "input_extraction": intent.get(
                "input_extraction", frontmatter.get("input_extraction", {})
            ),
            "allowed_tools": implementation.get(
                "tools", frontmatter.get("allowed_tools", [])
            ),
            "response_template": implementation.get(
                "response_template", frontmatter.get("response_template", "")
            ),
            "auth_required": bool(
                governance.get("auth_required", frontmatter.get("auth_required", False))
            ),
            "required_authorization": governance.get(
                "required_authorization", frontmatter.get("required_authorization")
            ),
            "confirmation_required": bool(
                governance.get(
                    "confirmation_required",
                    frontmatter.get("confirmation_required", False),
                )
            ),
            "disclosure": governance.get("disclosure", frontmatter.get("disclosure")),
            "failure_behavior": governance.get(
                "failure_behavior", frontmatter.get("failure_behavior", "safe_reject")
            ),
            "telemetry_events": implementation.get(
                "telemetry_events", frontmatter.get("telemetry_events", [])
            ),
            "config": implementation.get("config", frontmatter.get("config", {})),
            "behavior": {
                key: behavior[key]
                for key in ("interaction", "execution", "lifecycle")
                if key in behavior
            },
            "workflow": workflow,
        }
        return payload, acceptance

    def _synthesize_workflow(
        self, skill_type: str, implementation: Mapping[str, Any], source: Path
    ) -> Mapping[str, Any]:
        if implementation.get("static_response"):
            response = self._mapping(
                implementation["static_response"], "static_response", source
            )
            return {
                "version": 1,
                "steps": [
                    {
                        "op": "respond",
                        "template": response.get("template", ""),
                        "values": response.get("values", {}),
                        "outcome": response.get("outcome", {"status": "completed"}),
                    }
                ],
            }
        if skill_type == "navigation" and implementation.get("navigation"):
            navigation = self._mapping(
                implementation["navigation"], "navigation", source
            )
            save_as = str(navigation.get("save_as", "navigation"))
            return {
                "version": 1,
                "steps": [
                    {
                        "op": "call_tool",
                        "tool": navigation["tool"],
                        "action": navigation["action"],
                        "arguments": navigation.get("arguments", {}),
                        "save_as": save_as,
                        "completed_step": navigation.get("completed_step"),
                    },
                    {
                        "op": "respond",
                        "values": navigation.get("response_values", {}),
                        "outcome": navigation.get(
                            "outcome", {"status": "navigated"}
                        ),
                    },
                ],
            }
        raise CatalogValidationError(
            "{}: {} requires a Workflow section or a supported implicit implementation"
            .format(source.name, skill_type or "skill")
        )

    @staticmethod
    def _yaml_section(body: str, heading: str) -> Optional[Any]:
        pattern = re.compile(
            r"^##\s+{}\s*$\s*```ya?ml\s*(.*?)\s*```".format(re.escape(heading)),
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(body)
        return yaml.safe_load(match.group(1)) if match else None

    @staticmethod
    def _mapping(value: Any, name: str, source: Path) -> Mapping[str, Any]:
        if not isinstance(value, dict):
            raise CatalogValidationError(
                "{}: {} must be an object".format(source.name, name)
            )
        return value

    @staticmethod
    def _validate_acceptance(acceptance: List[Any], source: Path) -> None:
        identifiers = set()
        for index, scenario in enumerate(acceptance):
            if not isinstance(scenario, dict):
                raise CatalogValidationError(
                    "{}: acceptance scenario {} must be an object".format(
                        source.name, index
                    )
                )
            identifier = str(scenario.get("id", "")).strip()
            utterance = str(scenario.get("utterance", "")).strip()
            expected = scenario.get("expect")
            if not identifier or not utterance or not isinstance(expected, dict):
                raise CatalogValidationError(
                    "{}: acceptance scenarios require id, utterance, and expect"
                    .format(source.name)
                )
            if identifier in identifiers:
                raise CatalogValidationError(
                    "{}: duplicate acceptance id {}".format(source.name, identifier)
                )
            identifiers.add(identifier)


class SkillPublicationValidator:
    """Apply acceptance and platform-dependency gates before publication."""

    def __init__(
        self, tool_contracts: Optional[Mapping[str, Sequence[str]]] = None
    ) -> None:
        self.tool_contracts = tool_contracts

    def validate(self, compiled: CompiledSkill) -> None:
        self._validate_acceptance(compiled)
        if self.tool_contracts is not None:
            self._validate_dependencies(compiled)

    @staticmethod
    def _validate_acceptance(compiled: CompiledSkill) -> None:
        # A semantic model may add matches at runtime, but a publication example
        # must remain recognizable from the skill's own routing metadata.
        from member_assistant.providers import DeterministicProvider

        definition = compiled.definition
        declared_goals = {str(goal["name"]) for goal in definition.supported_goals}
        outcome_statuses = {
            str(step.get("outcome", {}).get("status"))
            for step in definition.workflow.get("steps", [])
            if isinstance(step.get("outcome"), dict)
            and step.get("outcome", {}).get("status") is not None
        }
        router = DeterministicProvider()
        for scenario in compiled.acceptance:
            expected = scenario["expect"]
            identifier = scenario["id"]
            expected_skill = expected.get("skill")
            expected_goal = expected.get("goal")
            if expected_skill != definition.name or expected_goal not in declared_goals:
                raise CatalogValidationError(
                    "{}: acceptance {} must expect this skill and one declared goal".format(
                        compiled.source.name, identifier
                    )
                )
            matches = router.identify_goals(
                str(scenario["utterance"]), [compiled.routing], {}
            )
            if not any(
                match.skill_name == expected_skill and match.goal == expected_goal
                for match in matches
            ):
                raise CatalogValidationError(
                    "{}: acceptance {} utterance does not match its declared goal".format(
                        compiled.source.name, identifier
                    )
                )
            expected_outcome = expected.get("outcome")
            if (
                expected_outcome is not None
                and str(expected_outcome) not in outcome_statuses
            ):
                raise CatalogValidationError(
                    "{}: acceptance {} expects an outcome not produced by the workflow".format(
                        compiled.source.name, identifier
                    )
                )
            expected_confirmation = expected.get("confirmation_required")
            if expected_confirmation is not None and bool(expected_confirmation) != bool(
                definition.confirmation_required
            ):
                raise CatalogValidationError(
                    "{}: acceptance {} confirmation expectation does not match governance".format(
                        compiled.source.name, identifier
                    )
                )

    def _validate_dependencies(self, compiled: CompiledSkill) -> None:
        assert self.tool_contracts is not None
        for step in compiled.definition.workflow.get("steps", []):
            if step.get("op") != "call_tool":
                continue
            tool_name = str(step["tool"])
            action = str(step["action"])
            actions = self.tool_contracts.get(tool_name)
            if actions is None:
                raise CatalogValidationError(
                    "{}: required tool {} is not installed in this platform".format(
                        compiled.source.name, tool_name
                    )
                )
            if action not in actions:
                raise CatalogValidationError(
                    "{}: action {} is not exposed by tool {}".format(
                        compiled.source.name, action, tool_name
                    )
                )


class FileSkillPublisher:
    """Atomically publish immutable artifacts and move an active-version pointer."""

    def __init__(self, catalog_directory: Path):
        self.catalog_directory = Path(catalog_directory)
        self.registry_directory = self.catalog_directory / "_registry"
        self.artifacts_directory = self.registry_directory / "artifacts"
        self.index_path = self.registry_directory / "active.json"
        self.lock_path = self.registry_directory / "publish.lock"

    def publish(self, compiled: CompiledSkill, activate: bool = True) -> PublicationReceipt:
        definition = compiled.definition
        artifact_hash = definition.artifact_hash
        version_directory = (
            self.artifacts_directory / definition.name / definition.version
        )
        artifact_path = version_directory / "{}.json".format(artifact_hash)
        with self._publication_lock():
            version_directory.mkdir(parents=True, exist_ok=True)
            existing = list(version_directory.glob("*.json"))
            conflicts = [path for path in existing if path.stem != artifact_hash]
            if conflicts:
                raise CatalogValidationError(
                    "{} {} is immutable; publish a new version for changed content"
                    .format(definition.name, definition.version)
                )
            idempotent = artifact_path.exists()
            if idempotent:
                try:
                    existing_payload = json.loads(
                        artifact_path.read_text(encoding="utf-8")
                    )
                    existing_definition = SkillDefinition.from_dict(
                        existing_payload, artifact_path
                    )
                except (OSError, json.JSONDecodeError, CatalogValidationError) as exc:
                    raise CatalogValidationError(
                        "Existing immutable artifact is unreadable or invalid"
                    ) from exc
                if (
                    existing_definition.name != definition.name
                    or existing_definition.version != definition.version
                    or existing_definition.artifact_hash != artifact_hash
                ):
                    raise CatalogValidationError(
                        "Existing immutable artifact does not match its identity"
                    )
            else:
                self._atomic_json(artifact_path, compiled.artifact_payload())
            if activate:
                index = self._read_index()
                entry = {
                    "version": definition.version,
                    "artifact_hash": artifact_hash,
                    "artifact": str(artifact_path.relative_to(self.registry_directory)),
                    "routing": compiled.routing.as_dict(),
                }
                skills = index.setdefault("skills", {})
                if skills.get(definition.name) != entry:
                    skills[definition.name] = entry
                    index["revision"] = int(index.get("revision", 0)) + 1
                    self._atomic_json(self.index_path, index)
        return PublicationReceipt(
            name=definition.name,
            version=definition.version,
            artifact_hash=artifact_hash,
            artifact_path=artifact_path,
            activated=activate,
            idempotent=idempotent,
        )

    def activate(self, name: str, version: str, artifact_hash: str) -> PublicationReceipt:
        artifact_path = self.artifacts_directory / name / version / "{}.json".format(
            artifact_hash
        )
        if not artifact_path.is_file():
            raise CatalogValidationError("Published artifact does not exist")
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        definition = SkillDefinition.from_dict(payload, artifact_path)
        if (
            definition.name != name
            or definition.version != version
            or definition.artifact_hash != artifact_hash
        ):
            raise CatalogValidationError(
                "Published artifact identity or hash does not match its path"
            )
        with self._publication_lock():
            index = self._read_index()
            index.setdefault("skills", {})[name] = {
                "version": version,
                "artifact_hash": artifact_hash,
                "artifact": str(artifact_path.relative_to(self.registry_directory)),
                "routing": definition.routing_definition().as_dict(),
            }
            index["revision"] = int(index.get("revision", 0)) + 1
            self._atomic_json(self.index_path, index)
        return PublicationReceipt(
            name=name,
            version=version,
            artifact_hash=artifact_hash,
            artifact_path=artifact_path,
            activated=True,
            idempotent=True,
        )

    def list_versions(self, name: Optional[str] = None) -> List[Dict[str, str]]:
        pattern = [name] if name else [path.name for path in self.artifacts_directory.glob("*")]
        versions: List[Dict[str, str]] = []
        for skill_name in sorted(pattern):
            skill_directory = self.artifacts_directory / skill_name
            for version_directory in sorted(skill_directory.glob("*")):
                for artifact in sorted(version_directory.glob("*.json")):
                    versions.append(
                        {
                            "name": skill_name,
                            "version": version_directory.name,
                            "artifact_hash": artifact.stem,
                            "artifact_path": str(artifact),
                        }
                    )
        return versions

    def _read_index(self) -> Dict[str, Any]:
        if not self.index_path.exists():
            return {"apiVersion": CATALOG_API_VERSION, "revision": 0, "skills": {}}
        parsed = json.loads(self.index_path.read_text(encoding="utf-8"))
        if parsed.get("apiVersion") != CATALOG_API_VERSION:
            raise CatalogValidationError("Unsupported catalog apiVersion")
        if not isinstance(parsed.get("skills"), dict):
            raise CatalogValidationError("Catalog skills must be an object")
        return parsed

    @contextmanager
    def _publication_lock(self) -> Iterator[None]:
        self.registry_directory.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+", encoding="utf-8")
        try:
            try:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            except ImportError:  # pragma: no cover - Windows fallback for this local POC
                pass
            yield
        finally:
            try:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except ImportError:  # pragma: no cover
                pass
            handle.close()

    @staticmethod
    def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp-{}".format(os.getpid()))
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(str(temporary), str(path))


__all__ = [
    "CompiledSkill",
    "FileSkillPublisher",
    "PublicationReceipt",
    "SkillMarkdownCompiler",
    "SkillPublicationValidator",
]
