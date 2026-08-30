"""Compile one business-facing SKILL.md into an immutable runtime artifact."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
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


SKILL_API_VERSION = "nexus.skills/v2"
SKILL_SCHEMA_VERSION = "nexus.skills/v3"
SUPPORTED_SKILL_API_VERSIONS = {
    "nexus.skills/v1",
    SKILL_API_VERSION,
    SKILL_SCHEMA_VERSION,
}
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

@dataclass(frozen=True)
class PublicationReceipt:
    name: str
    version: str
    artifact_hash: str
    artifact_path: Path
    activated: bool
    idempotent: bool


@dataclass(frozen=True)
class DeactivationReceipt:
    name: str
    version: str
    artifact_hash: str
    deactivated: bool


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
        try:
            parsed = yaml.safe_load("\n".join(lines[1:closing])) or {}
        except yaml.YAMLError as exc:
            raise CatalogValidationError(
                "{}: YAML frontmatter is invalid".format(source.name)
            ) from exc
        if not isinstance(parsed, dict):
            raise CatalogValidationError(
                "{}: YAML frontmatter must be an object".format(source.name)
            )
        return parsed, "\n".join(lines[closing + 1 :]).strip()

    def _normalize(
        self, frontmatter: Mapping[str, Any], body: str, source: Path
    ) -> tuple:
        if "schema_version" in frontmatter:
            return self._normalize_v3(frontmatter, body, source)
        api_version = frontmatter.get("apiVersion", SKILL_API_VERSION)
        if api_version not in SUPPORTED_SKILL_API_VERSIONS:
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

        archetype = str(behavior.get("archetype", "")).strip()
        workflow = implementation.get("workflow")
        if workflow is None:
            workflow = self._yaml_section(body, "Workflow", source)
        if workflow is None:
            workflow = self._synthesize_workflow(archetype, implementation, source)

        acceptance = frontmatter.get("acceptance")
        if acceptance is None:
            acceptance = self._yaml_section(body, "Acceptance", source)
        if isinstance(acceptance, dict):
            acceptance = acceptance.get("scenarios", [])
        if not isinstance(acceptance, list):
            raise CatalogValidationError(
                "{}: acceptance must be a list of scenarios".format(source.name)
            )

        input_contract = intent.get(
            "input_schema", {"type": "object", "properties": {}}
        )
        payload: Dict[str, Any] = {
            "apiVersion": api_version,
            "name": metadata.get("name"),
            "version": metadata.get("version"),
            "archetype": archetype,
            "description": intent.get("description", ""),
            "owner": metadata.get("owner", ""),
            "risk_tier": governance.get("risk_tier", "informational"),
            "supported_goals": intent.get("goals", []),
            "input_schema": input_contract,
            "input_extraction": intent.get("input_extraction", {}),
            "allowed_tools": implementation.get("tools", []),
            "response_template": implementation.get("response_template", ""),
            "auth_required": bool(governance.get("auth_required", False)),
            "required_authorization": governance.get("required_authorization"),
            "confirmation_required": bool(
                governance.get("confirmation_required", False)
            ),
            "disclosure": governance.get("disclosure"),
            "failure_behavior": governance.get("failure_behavior", "safe_reject"),
            "telemetry_events": implementation.get("telemetry_events", []),
            "config": implementation.get("config", {}),
            "behavior": {
                key: behavior[key]
                for key in ("interaction", "execution", "lifecycle")
                if key in behavior
            },
            "workflow": workflow,
        }
        capability = metadata.get("capability")
        if capability is not None:
            capability = self._mapping(capability, "metadata.capability", source)
            capability_id = str(capability.get("id", "")).strip()
            specification = str(capability.get("specification", "")).strip()
            acceptance_ids = capability.get("acceptance", [])
            if (
                not capability_id
                or not specification
                or not isinstance(acceptance_ids, list)
                or not acceptance_ids
                or not all(str(identifier).strip() for identifier in acceptance_ids)
            ):
                raise CatalogValidationError(
                    "{}: metadata.capability requires id, specification, and acceptance IDs".format(
                        source.name
                    )
                )
            payload["traceability"] = {
                "capability_id": capability_id,
                "specification": specification,
                "acceptance": [str(identifier) for identifier in acceptance_ids],
            }
        if api_version == SKILL_API_VERSION or "sample_utterances" in intent:
            payload["sample_utterances"] = intent.get("sample_utterances", [])
        return payload, acceptance

    def _normalize_v3(
        self, frontmatter: Mapping[str, Any], body: str, source: Path
    ) -> tuple:
        schema_version = frontmatter.get("schema_version")
        if schema_version != SKILL_SCHEMA_VERSION:
            raise CatalogValidationError(
                "{}: unsupported schema_version {}".format(source.name, schema_version)
            )
        if "apiVersion" in frontmatter or "kind" in frontmatter or "intent" in frontmatter:
            raise CatalogValidationError(
                "{}: v3 uses flattened root fields; apiVersion, kind, and intent are not allowed".format(
                    source.name
                )
            )
        if "goals" in frontmatter:
            raise CatalogValidationError(
                "{}: multi-goal skills are not supported; omit goals for the single-goal form".format(
                    source.name
                )
            )

        metadata = self._mapping(frontmatter.get("metadata", {}), "metadata", source)
        behavior = self._mapping(frontmatter.get("behavior", {}), "behavior", source)
        governance = self._mapping(
            frontmatter.get("governance", {}), "governance", source
        )
        implementation = self._mapping(
            frontmatter.get("implementation", {}), "implementation", source
        )
        fallback = self._mapping(frontmatter.get("fallback", {}), "fallback", source)

        name = str(frontmatter.get("name", "")).strip()
        examples = frontmatter.get("examples", [])
        if not isinstance(examples, list) or any(
            not isinstance(example, str) for example in examples
        ):
            raise CatalogValidationError(
                "{}: v3 examples must be a list of strings".format(source.name)
            )
        normalized_examples = [
            {"utterance": " ".join(example.split()), "goal": name}
            for example in examples
        ]

        archetype = str(behavior.get("archetype", "")).strip()
        workflow = implementation.get("workflow")
        if workflow is None:
            workflow = self._synthesize_workflow(archetype, implementation, source)

        acceptance = frontmatter.get("acceptance")
        if isinstance(acceptance, dict):
            acceptance = acceptance.get("scenarios", [])
        if not isinstance(acceptance, list):
            raise CatalogValidationError(
                "{}: acceptance must be a list of scenarios".format(source.name)
            )

        payload: Dict[str, Any] = {
            # The catalog's normalized representation keeps this key for legacy
            # readers. It is generated by the compiler, never authored in v3.
            "apiVersion": SKILL_SCHEMA_VERSION,
            "name": name,
            "version": frontmatter.get("version"),
            "display_name": frontmatter.get("display_name", ""),
            "archetype": archetype,
            "description": frontmatter.get("description", ""),
            "sample_utterances": normalized_examples,
            "owner": metadata.get("owner", ""),
            "metadata": dict(metadata),
            "risk_tier": governance.get("risk_tier", "informational"),
            # A single-goal v3 artifact has no authored goal identifier. This
            # compatibility view is synthesized for durable runtime state.
            "supported_goals": [
                {
                    "name": name,
                    "display_name": frontmatter.get("display_name", ""),
                    "keywords": list(fallback.get("routing_hints", [])),
                }
            ],
            "input_schema": frontmatter.get(
                "input_schema", {"type": "object", "properties": {}}
            ),
            "input_extraction": fallback.get("input_extraction", {}),
            "allowed_tools": implementation.get("tools", []),
            "response_template": implementation.get("response_template", ""),
            "auth_required": bool(governance.get("auth_required", False)),
            "required_authorization": governance.get("required_authorization"),
            "confirmation_required": bool(
                governance.get("confirmation_required", False)
            ),
            "disclosure": governance.get("disclosure"),
            "failure_behavior": governance.get("failure_behavior", "safe_reject"),
            "telemetry_events": implementation.get("telemetry_events", []),
            "config": implementation.get("config", {}),
            "behavior": {
                key: behavior[key]
                for key in ("interaction", "execution", "lifecycle")
                if key in behavior
            },
            "workflow": workflow,
        }
        return payload, acceptance

    def _synthesize_workflow(
        self, archetype: str, implementation: Mapping[str, Any], source: Path
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
        if implementation.get("tool_response"):
            recipe = self._mapping(
                implementation["tool_response"], "tool_response", source
            )
            call = self._mapping(recipe.get("call", {}), "tool_response.call", source)
            response = self._mapping(
                recipe.get("response", {}), "tool_response.response", source
            )
            return {
                "version": 1,
                "steps": [
                    {**call, "op": "call_tool"},
                    {**response, "op": "respond"},
                ],
            }
        if implementation.get("guided_selection"):
            recipe = self._mapping(
                implementation["guided_selection"], "guided_selection", source
            )
            source_step = self._mapping(
                recipe.get("source", {}), "guided_selection.source", source
            )
            selection = self._mapping(
                recipe.get("selection", {}), "guided_selection.selection", source
            )
            response = self._mapping(
                recipe.get("response", {}), "guided_selection.response", source
            )
            return {
                "version": 1,
                "steps": [
                    {**source_step, "op": "call_tool"},
                    {**selection, "op": "select"},
                    {**response, "op": "respond"},
                ],
            }
        if archetype == "navigation" and implementation.get("navigation"):
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
            .format(source.name, archetype or "skill")
        )

    @staticmethod
    def _yaml_section(body: str, heading: str, source: Path) -> Optional[Any]:
        pattern = re.compile(
            r"^##\s+{}\s*$\s*```ya?ml\s*(.*?)\s*```".format(re.escape(heading)),
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(body)
        if not match:
            return None
        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            raise CatalogValidationError(
                "{}: {} YAML section is invalid".format(source.name, heading)
            ) from exc

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
            if expected_goal is None and definition.api_version == SKILL_SCHEMA_VERSION:
                expected_goal = definition.name
            if expected_skill != definition.name or expected_goal not in declared_goals:
                raise CatalogValidationError(
                    "{}: acceptance {} must expect this skill and one declared goal".format(
                        compiled.source.name, identifier
                    )
                )
            matches = router.identify_skills(
                str(scenario["utterance"]), [compiled.routing], {}
            )
            if not any(
                match.skill_name == expected_skill
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
    """Publish immutable SKILL.md artifacts and atomically move active pointers."""

    def __init__(self, catalog_directory: Path):
        self.catalog_directory = Path(catalog_directory)
        self.index_path = self.catalog_directory / "active.yaml"
        self.audit_path = self.catalog_directory / "catalog-events.yaml"
        self.lock_path = self.catalog_directory / ".publish.lock"

    def publish(self, compiled: CompiledSkill, activate: bool = True) -> PublicationReceipt:
        definition = compiled.definition
        artifact_hash = definition.artifact_hash
        version_directory = self.catalog_directory / definition.name / definition.version
        artifact_path = version_directory / "SKILL.md"
        with self._publication_lock():
            version_directory.mkdir(parents=True, exist_ok=True)
            idempotent = artifact_path.exists()
            if idempotent:
                try:
                    existing_definition = SkillMarkdownCompiler().compile(
                        artifact_path
                    ).definition
                except (OSError, yaml.YAMLError, CatalogValidationError) as exc:
                    raise CatalogValidationError(
                        "Existing immutable artifact is unreadable or invalid"
                    ) from exc
                if (
                    existing_definition.name != definition.name
                    or existing_definition.version != definition.version
                    or existing_definition.artifact_hash != artifact_hash
                ):
                    raise CatalogValidationError(
                        "{} {} is immutable; publish a new version for changed content".format(
                            definition.name, definition.version
                        )
                    )
            else:
                self._atomic_text(
                    artifact_path, compiled.source.read_text(encoding="utf-8")
                )
            if activate:
                index = self._read_index()
                entry = {
                    "version": definition.version,
                    "artifact_hash": artifact_hash,
                    "artifact": str(artifact_path.relative_to(self.catalog_directory)),
                    "routing": compiled.routing.as_dict(),
                }
                skills = index.setdefault("skills", {})
                if skills.get(definition.name) != entry:
                    skills[definition.name] = entry
                    index["revision"] = int(index.get("revision", 0)) + 1
                    self._atomic_yaml(self.index_path, index)
            else:
                index = self._read_index()
            self._append_audit(
                action="publish_and_activate" if activate else "publish_staged",
                name=definition.name,
                version=definition.version,
                artifact_hash=artifact_hash,
                catalog_revision=int(index.get("revision", 0)),
                details={
                    "idempotent": idempotent,
                    "source": str(compiled.source),
                },
            )
        return PublicationReceipt(
            name=definition.name,
            version=definition.version,
            artifact_hash=artifact_hash,
            artifact_path=artifact_path,
            activated=activate,
            idempotent=idempotent,
        )

    def activate(self, name: str, version: str, artifact_hash: str) -> PublicationReceipt:
        artifact_path = self.catalog_directory / name / version / "SKILL.md"
        if not artifact_path.is_file():
            raise CatalogValidationError("Published artifact does not exist")
        definition = SkillMarkdownCompiler().compile(artifact_path).definition
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
                "artifact": str(artifact_path.relative_to(self.catalog_directory)),
                "routing": definition.routing_definition().as_dict(),
            }
            index["revision"] = int(index.get("revision", 0)) + 1
            self._atomic_yaml(self.index_path, index)
            self._append_audit(
                action="activate",
                name=name,
                version=version,
                artifact_hash=artifact_hash,
                catalog_revision=int(index["revision"]),
            )
        return PublicationReceipt(
            name=name,
            version=version,
            artifact_hash=artifact_hash,
            artifact_path=artifact_path,
            activated=True,
            idempotent=True,
        )

    def deactivate(self, name: str) -> DeactivationReceipt:
        """Stop routing new work while retaining every immutable version."""

        with self._publication_lock():
            index = self._read_index()
            skills = index.setdefault("skills", {})
            entry = skills.get(name)
            if not isinstance(entry, dict):
                raise CatalogValidationError("Active skill does not exist: {}".format(name))
            del skills[name]
            index["revision"] = int(index.get("revision", 0)) + 1
            self._atomic_yaml(self.index_path, index)
            self._append_audit(
                action="deactivate",
                name=name,
                version=str(entry["version"]),
                artifact_hash=str(entry["artifact_hash"]),
                catalog_revision=int(index["revision"]),
            )
        return DeactivationReceipt(
            name=name,
            version=str(entry["version"]),
            artifact_hash=str(entry["artifact_hash"]),
            deactivated=True,
        )

    def list_versions(self, name: Optional[str] = None) -> List[Dict[str, str]]:
        pattern = [name] if name else [
            path.name
            for path in self.catalog_directory.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        ]
        versions: List[Dict[str, str]] = []
        for skill_name in sorted(pattern):
            skill_directory = self.catalog_directory / skill_name
            for version_directory in sorted(skill_directory.glob("*")):
                artifact = version_directory / "SKILL.md"
                if not artifact.is_file():
                    continue
                definition = SkillMarkdownCompiler().compile(artifact).definition
                versions.append(
                    {
                        "name": skill_name,
                        "version": definition.version,
                        "artifact_hash": definition.artifact_hash,
                        "artifact_path": str(artifact),
                    }
                )
        return versions

    def _read_index(self) -> Dict[str, Any]:
        if not self.index_path.exists():
            return {"apiVersion": CATALOG_API_VERSION, "revision": 0, "skills": {}}
        try:
            parsed = yaml.safe_load(self.index_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise CatalogValidationError("Catalog active.yaml is invalid") from exc
        if not isinstance(parsed, dict):
            raise CatalogValidationError("Catalog active.yaml must be an object")
        if parsed.get("apiVersion") != CATALOG_API_VERSION:
            raise CatalogValidationError("Unsupported catalog apiVersion")
        if not isinstance(parsed.get("skills"), dict):
            raise CatalogValidationError("Catalog skills must be an object")
        return parsed

    @contextmanager
    def _publication_lock(self) -> Iterator[None]:
        self.catalog_directory.mkdir(parents=True, exist_ok=True)
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

    def _append_audit(
        self,
        *,
        action: str,
        name: str,
        version: str,
        artifact_hash: str,
        catalog_revision: int,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": os.getenv("SKILL_PUBLISHER_ACTOR")
            or os.getenv("USER")
            or "local-publisher",
            "action": action,
            "skill": name,
            "version": version,
            "artifact_hash": artifact_hash,
            "catalog_revision": catalog_revision,
            "details": dict(details or {}),
        }
        self.catalog_directory.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write("---\n")
            handle.write(yaml.safe_dump(event, sort_keys=False, allow_unicode=True))
            handle.flush()
            os.fsync(handle.fileno())

    @staticmethod
    def _atomic_yaml(path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp-{}".format(os.getpid()))
        temporary.write_text(
            yaml.safe_dump(dict(value), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        os.replace(str(temporary), str(path))

    @staticmethod
    def _atomic_text(path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp-{}".format(os.getpid()))
        temporary.write_text(value, encoding="utf-8")
        os.replace(str(temporary), str(path))


__all__ = [
    "CompiledSkill",
    "DeactivationReceipt",
    "FileSkillPublisher",
    "PublicationReceipt",
    "SkillMarkdownCompiler",
    "SkillPublicationValidator",
]
