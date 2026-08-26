"""Validated, file-based skill discovery with last-known-good reloads."""

from dataclasses import asdict, dataclass, field, replace
import hashlib
import json
from pathlib import Path
import re
import threading
from typing import Any, Dict, List, Mapping, Optional, Tuple

import yaml


RISK_TIERS = {"informational", "navigation", "read_only", "consequential", "handoff"}
# Built-in authoring archetypes. This is deliberately not a closed runtime enum:
# publishers may introduce another archetype when it compiles to the governed
# workflow operation set below.
BUILTIN_ARCHETYPES = {
    "knowledge",
    "guided_resolution",
    "deterministic_workflow",
    "navigation",
    "human_handoff",
}
DEFAULT_BEHAVIOR = {
    "knowledge": ("direct", "knowledge_retrieval", "synchronous"),
    "guided_resolution": ("guided", "tool_query", "synchronous"),
    "deterministic_workflow": ("guided", "workflow", "synchronous"),
    "navigation": ("direct", "navigation", "synchronous"),
    "human_handoff": ("guided", "handoff", "synchronous"),
}
WORKFLOW_OPERATIONS = {
    "call_tool",
    "collect",
    "confirm",
    "respond",
    "select",
    "set",
    "validate",
    "validate_decimal",
}
TYPE_WORKFLOW_OPERATIONS = {
    "knowledge": {"call_tool", "collect", "respond"},
    "guided_resolution": {
        "call_tool",
        "collect",
        "respond",
        "select",
        "set",
        "validate",
        "validate_decimal",
    },
    "deterministic_workflow": WORKFLOW_OPERATIONS,
    "navigation": {"call_tool", "collect", "respond"},
    "human_handoff": {"call_tool", "respond"},
}


class CatalogValidationError(ValueError):
    pass


def _artifact_hash(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class SkillRoutingDefinition:
    """Small catalog record used for routing without loading executable content."""

    name: str
    version: str
    artifact_hash: str
    archetype: str
    description: str
    owner: str
    risk_tier: str
    interaction: str
    execution: str
    lifecycle: str
    supported_goals: Tuple[Mapping[str, Any], ...]
    input_schema: Mapping[str, Any]
    input_extraction: Mapping[str, Any]

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SkillRoutingDefinition":
        return cls(
            name=str(value["name"]),
            version=str(value["version"]),
            artifact_hash=str(value["artifact_hash"]),
            archetype=str(value["archetype"]),
            description=str(value["description"]),
            owner=str(value["owner"]),
            risk_tier=str(value["risk_tier"]),
            interaction=str(value["interaction"]),
            execution=str(value["execution"]),
            lifecycle=str(value["lifecycle"]),
            supported_goals=tuple(value["supported_goals"]),
            input_schema=dict(value["input_schema"]),
            input_extraction=dict(value.get("input_extraction", {})),
        )

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    version: str
    archetype: str
    description: str
    owner: str
    risk_tier: str
    supported_goals: Tuple[Mapping[str, Any], ...]
    input_schema: Mapping[str, Any]
    allowed_tools: Tuple[str, ...]
    response_template: str
    auth_required: bool = False
    required_authorization: Optional[str] = None
    confirmation_required: bool = False
    disclosure: Optional[str] = None
    failure_behavior: str = "safe_reject"
    telemetry_events: Tuple[str, ...] = field(default_factory=tuple)
    config: Mapping[str, Any] = field(default_factory=dict)
    input_extraction: Mapping[str, Any] = field(default_factory=dict)
    workflow: Mapping[str, Any] = field(default_factory=dict)
    api_version: str = "nexus.skills/v1"
    interaction: str = "guided"
    execution: str = "workflow"
    lifecycle: str = "synchronous"
    artifact_hash: str = ""

    @classmethod
    def from_dict(cls, value: Mapping[str, Any], source: Path) -> "SkillDefinition":
        required = (
            "name",
            "version",
            "archetype",
            "description",
            "owner",
            "risk_tier",
            "supported_goals",
            "input_schema",
            "allowed_tools",
            "response_template",
            "workflow",
        )
        missing = [key for key in required if key not in value]
        if missing:
            raise CatalogValidationError(
                "{}: missing required fields: {}".format(source.name, ", ".join(missing))
            )
        if not isinstance(value["name"], str) or not re.fullmatch(
            r"[a-z][a-z0-9_]{1,79}", value["name"].strip()
        ):
            raise CatalogValidationError(
                "{}: name must be a lower_snake_case identifier".format(source.name)
            )
        if not re.fullmatch(
            r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?",
            str(value["version"]),
        ):
            raise CatalogValidationError(
                "{}: version must use semantic versioning".format(source.name)
            )
        if not str(value["description"]).strip() or not str(value["owner"]).strip():
            raise CatalogValidationError(
                "{}: description and owner must be non-empty".format(source.name)
            )
        if value["risk_tier"] not in RISK_TIERS:
            raise CatalogValidationError("{}: unsupported risk_tier".format(source.name))
        archetype = str(value["archetype"])
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,79}", archetype):
            raise CatalogValidationError("{}: invalid archetype".format(source.name))
        goals = value["supported_goals"]
        if not isinstance(goals, list) or not goals:
            raise CatalogValidationError("{}: supported_goals must be non-empty".format(source.name))
        for goal in goals:
            if not isinstance(goal, dict) or not isinstance(goal.get("name"), str):
                raise CatalogValidationError("{}: each goal requires a name".format(source.name))
            if not isinstance(goal.get("keywords", []), list):
                raise CatalogValidationError("{}: goal keywords must be a list".format(source.name))
            if "display_name" in goal and (
                not isinstance(goal["display_name"], str)
                or not goal["display_name"].strip()
            ):
                raise CatalogValidationError(
                    "{}: goal display_name must be a non-empty string".format(
                        source.name
                    )
                )
        goal_names = [str(goal["name"]) for goal in goals]
        if len(goal_names) != len(set(goal_names)):
            raise CatalogValidationError(
                "{}: goal names must be unique".format(source.name)
            )
        if not isinstance(value["input_schema"], dict):
            raise CatalogValidationError("{}: input_schema must be an object".format(source.name))
        if not isinstance(value["input_schema"].get("properties", {}), dict):
            raise CatalogValidationError(
                "{}: input_schema.properties must be an object".format(source.name)
            )
        if not isinstance(value["allowed_tools"], list):
            raise CatalogValidationError("{}: allowed_tools must be a list".format(source.name))
        workflow = value["workflow"]
        if not isinstance(workflow, dict) or workflow.get("version") != 1:
            raise CatalogValidationError("{}: workflow.version must be 1".format(source.name))
        steps = workflow.get("steps")
        if not isinstance(steps, list) or not steps:
            raise CatalogValidationError("{}: workflow.steps must be non-empty".format(source.name))
        for index, step in enumerate(steps):
            if not isinstance(step, dict) or step.get("op") not in WORKFLOW_OPERATIONS:
                raise CatalogValidationError(
                    "{}: workflow step {} has an unsupported operation".format(
                        source.name, index
                    )
                )
            allowed_operations = TYPE_WORKFLOW_OPERATIONS.get(
                archetype, WORKFLOW_OPERATIONS
            )
            if step["op"] not in allowed_operations:
                raise CatalogValidationError(
                    "{}: operation {} is not allowed for skill type {}".format(
                        source.name, step["op"], archetype
                    )
                )
            if step["op"] == "call_tool":
                tool_name = step.get("tool")
                if tool_name not in value["allowed_tools"]:
                    raise CatalogValidationError(
                        "{}: workflow tool {} is not in allowed_tools".format(
                            source.name, tool_name
                        )
                    )
                if step.get("consequential") and (
                    index == 0 or steps[index - 1].get("op") != "confirm"
                ):
                    raise CatalogValidationError(
                        "{}: consequential tool calls must immediately follow confirmation".format(
                            source.name
                        )
                    )
            required_by_operation = {
                "call_tool": ("tool", "action"),
                "collect": ("fields",),
                "confirm": ("template",),
                "respond": (),
                "select": (
                    "collection",
                    "input",
                    "choice_template",
                    "prompt_template",
                    "save_as",
                ),
                "set": ("value", "save_as"),
                "validate": ("rule", "left", "on_fail"),
                "validate_decimal": ("value", "save_as", "on_fail"),
            }
            missing_step_fields = [
                field_name
                for field_name in required_by_operation[step["op"]]
                if field_name not in step
            ]
            if missing_step_fields:
                raise CatalogValidationError(
                    "{}: workflow step {} is missing {}".format(
                        source.name, index, ", ".join(missing_step_fields)
                    )
                )
            if step["op"] == "validate" and step["rule"] not in {
                "not_equal",
                "truthy",
            }:
                raise CatalogValidationError(
                    "{}: workflow step {} has an unsupported validation rule".format(
                        source.name, index
                    )
                )
        if value.get("confirmation_required", False) and value["risk_tier"] != "consequential":
            raise CatalogValidationError(
                "{}: confirmation is only valid for consequential skills".format(source.name)
            )
        if value.get("confirmation_required", False) and archetype in BUILTIN_ARCHETYPES and archetype != "deterministic_workflow":
            raise CatalogValidationError(
                "{}: confirmation requires deterministic_workflow".format(source.name)
            )
        if value.get("confirmation_required", False) and not any(
            step.get("op") == "confirm" for step in steps
        ):
            raise CatalogValidationError(
                "{}: confirmation_required needs a confirm workflow step".format(source.name)
            )
        if value.get("confirmation_required", False) and not any(
            step.get("op") == "call_tool" and step.get("consequential")
            for step in steps
        ):
            raise CatalogValidationError(
                "{}: confirmation_required needs a consequential tool call".format(source.name)
            )
        extraction = value.get("input_extraction", {})
        if not isinstance(extraction, dict):
            raise CatalogValidationError("{}: input_extraction must be an object".format(source.name))
        for field_name, rule in extraction.items():
            if field_name not in value["input_schema"].get("properties", {}):
                raise CatalogValidationError(
                    "{}: extraction field {} is absent from input_schema".format(
                        source.name, field_name
                    )
                )
            if not isinstance(rule, dict) or rule.get("strategy") not in {
                "alias",
                "full_message",
                "regex",
            }:
                raise CatalogValidationError(
                    "{}: invalid extraction rule for {}".format(source.name, field_name)
                )
            if rule["strategy"] == "regex":
                try:
                    re.compile(str(rule.get("pattern", "")))
                except re.error as exc:
                    raise CatalogValidationError(
                        "{}: invalid extraction regex for {}".format(source.name, field_name)
                    ) from exc
        default_interaction, default_execution, default_lifecycle = DEFAULT_BEHAVIOR.get(
            archetype, ("guided", "workflow", "synchronous")
        )
        behavior = value.get("behavior", {})
        if not isinstance(behavior, dict):
            raise CatalogValidationError("{}: behavior must be an object".format(source.name))
        definition = cls(
            name=value["name"].strip(),
            version=str(value["version"]),
            archetype=archetype,
            description=str(value["description"]),
            owner=str(value["owner"]),
            risk_tier=str(value["risk_tier"]),
            supported_goals=tuple(goals),
            input_schema=value["input_schema"],
            allowed_tools=tuple(str(tool) for tool in value["allowed_tools"]),
            response_template=str(value["response_template"]),
            auth_required=bool(value.get("auth_required", False)),
            required_authorization=value.get("required_authorization"),
            confirmation_required=bool(value.get("confirmation_required", False)),
            disclosure=value.get("disclosure"),
            failure_behavior=str(value.get("failure_behavior", "safe_reject")),
            telemetry_events=tuple(value.get("telemetry_events", [])),
            config=value.get("config", {}),
            input_extraction=extraction,
            workflow=workflow,
            api_version=str(value.get("apiVersion", "nexus.skills/v1")),
            interaction=str(behavior.get("interaction", default_interaction)),
            execution=str(behavior.get("execution", default_execution)),
            lifecycle=str(behavior.get("lifecycle", default_lifecycle)),
        )
        return replace(definition, artifact_hash=_artifact_hash(value))

    def public_contract(self) -> Dict[str, Any]:
        return asdict(self)

    def routing_definition(self) -> SkillRoutingDefinition:
        return SkillRoutingDefinition(
            name=self.name,
            version=self.version,
            artifact_hash=self.artifact_hash,
            archetype=self.archetype,
            description=self.description,
            owner=self.owner,
            risk_tier=self.risk_tier,
            interaction=self.interaction,
            execution=self.execution,
            lifecycle=self.lifecycle,
            supported_goals=self.supported_goals,
            input_schema=self.input_schema,
            input_extraction=self.input_extraction,
        )


class SkillCatalog:
    """Watch routing metadata and lazily load immutable SKILL.md artifacts."""

    def __init__(self, directory: Path, poll_seconds: float = 0.5):
        self.directory = Path(directory)
        self.poll_seconds = poll_seconds
        self._lock = threading.RLock()
        self._versions: Dict[Tuple[str, str, str], SkillDefinition] = {}
        self._routes: Dict[str, SkillRoutingDefinition] = {}
        self._active_refs: Dict[str, Tuple[str, str, str]] = {}
        self._artifacts: Dict[Tuple[str, str, str], Path] = {}
        self._index_path = self.directory / "active.yaml"
        self._index_signature: Optional[Tuple[int, int]] = None
        self._errors: Dict[str, str] = {}
        self._revision = 0
        self._stop_event = threading.Event()
        self._watcher: Optional[threading.Thread] = None
        self.directory.mkdir(parents=True, exist_ok=True)
        self.refresh(force=True)

    @property
    def revision(self) -> int:
        with self._lock:
            return self._revision

    @property
    def errors(self) -> Dict[str, str]:
        with self._lock:
            return dict(self._errors)

    def get(
        self,
        name: str,
        version: Optional[str] = None,
        artifact_hash: Optional[str] = None,
    ) -> Optional[SkillDefinition]:
        """Load one exact artifact; routing never requires this full definition."""

        from member_assistant.skill_authoring import SkillMarkdownCompiler

        self.refresh()
        with self._lock:
            if version is None and artifact_hash is None:
                key = self._active_refs.get(name)
            elif version is not None and artifact_hash is not None:
                key = (name, version, artifact_hash)
            else:
                candidates = [
                    candidate
                    for candidate in self._versions
                    if candidate[0] == name
                    and (version is None or candidate[1] == version)
                    and (artifact_hash is None or candidate[2] == artifact_hash)
                ]
                key = candidates[0] if len(candidates) == 1 else None
            if key is None and version is not None and artifact_hash is None:
                path = self.directory / name / version / "SKILL.md"
                if path.is_file():
                    try:
                        compiled = SkillMarkdownCompiler().compile(path)
                    except (OSError, CatalogValidationError, yaml.YAMLError) as exc:
                        self._errors[self._relative(path)] = str(exc)
                        return None
                    key = (
                        compiled.definition.name,
                        compiled.definition.version,
                        compiled.definition.artifact_hash,
                    )
                    self._versions[key] = compiled.definition
                    self._artifacts[key] = path
            if key is None:
                return None
            cached = self._versions.get(key)
            if cached is not None:
                return cached
            path = self._artifacts.get(key) or (
                self.directory / key[0] / key[1] / "SKILL.md"
            )
            try:
                compiled = SkillMarkdownCompiler().compile(path)
                definition = compiled.definition
            except (OSError, CatalogValidationError, yaml.YAMLError) as exc:
                self._errors[self._relative(path)] = str(exc)
                return None
            actual_key = (
                definition.name,
                definition.version,
                definition.artifact_hash,
            )
            if actual_key != key:
                self._errors[self._relative(path)] = (
                    "Artifact identity or content hash does not match the catalog reference"
                )
                return None
            self._versions[key] = definition
            self._artifacts[key] = path
            self._errors.pop(self._relative(path), None)
            return definition

    def list(self) -> List[SkillDefinition]:
        """Convenience for diagnostics that explicitly need every full skill."""

        return [
            definition
            for route in self.routes()
            for definition in [self.get(route.name, route.version, route.artifact_hash)]
            if definition is not None
        ]

    def routes(self) -> List[SkillRoutingDefinition]:
        self.refresh()
        with self._lock:
            return sorted(self._routes.values(), key=lambda skill: skill.name)

    def refresh(self, force: bool = False) -> bool:
        """Refresh the active pointer; invalid updates retain the last-known-good set."""

        with self._lock:
            changed = self._refresh_index_locked(force)
            if changed:
                self._revision += 1
            return changed

    def _refresh_index_locked(self, force: bool) -> bool:
        if not self._index_path.exists():
            changed = bool(self._routes)
            self._routes = {}
            self._active_refs = {}
            self._index_signature = None
            return changed
        stat = self._index_path.stat()
        signature = (stat.st_mtime_ns, stat.st_size)
        if not force and signature == self._index_signature:
            return False
        self._index_signature = signature
        try:
            raw = yaml.safe_load(self._index_path.read_text(encoding="utf-8")) or {}
            if raw.get("apiVersion") != "nexus.catalog/v1":
                raise CatalogValidationError("Unsupported catalog apiVersion")
            entries = raw.get("skills")
            if not isinstance(entries, dict):
                raise CatalogValidationError("Catalog skills must be an object")
            routes: Dict[str, SkillRoutingDefinition] = {}
            active_refs: Dict[str, Tuple[str, str, str]] = {}
            artifacts: Dict[Tuple[str, str, str], Path] = {}
            catalog_root = self.directory.resolve()
            for name, entry in entries.items():
                if not isinstance(entry, dict):
                    raise CatalogValidationError(
                        "Invalid catalog entry for {}".format(name)
                    )
                route = SkillRoutingDefinition.from_dict(entry["routing"])
                if (
                    route.name != name
                    or route.version != str(entry["version"])
                    or route.artifact_hash != str(entry["artifact_hash"])
                ):
                    raise CatalogValidationError(
                        "Catalog routing identity does not match {}".format(name)
                    )
                artifact = (self.directory / str(entry["artifact"])).resolve()
                try:
                    artifact.relative_to(catalog_root)
                except ValueError as exc:
                    raise CatalogValidationError(
                        "Catalog artifact escapes the catalog directory"
                    ) from exc
                if artifact.name != "SKILL.md" or not artifact.is_file():
                    raise CatalogValidationError(
                        "Catalog SKILL.md artifact is missing for {}".format(name)
                    )
                key = (route.name, route.version, route.artifact_hash)
                routes[name] = route
                active_refs[name] = key
                artifacts[key] = artifact
            changed = routes != self._routes or active_refs != self._active_refs
            self._routes = routes
            self._active_refs = active_refs
            # Keep inactive artifact paths already observed so in-flight tasks can
            # resume; a restarted process can also resolve their conventional path.
            self._artifacts.update(artifacts)
            self._errors.pop(self._relative(self._index_path), None)
            return changed
        except (KeyError, OSError, ValueError, TypeError, yaml.YAMLError, CatalogValidationError) as exc:
            self._errors[self._relative(self._index_path)] = str(exc)
            return False

    def start(self) -> None:
        with self._lock:
            if self._watcher and self._watcher.is_alive():
                return
            self._stop_event.clear()
            self._watcher = threading.Thread(
                target=self._watch_loop, name="skill-catalog-watcher", daemon=True
            )
            self._watcher.start()

    def stop(self) -> None:
        self._stop_event.set()
        watcher = self._watcher
        if watcher:
            watcher.join(timeout=max(1.0, self.poll_seconds * 3))

    def _watch_loop(self) -> None:
        while not self._stop_event.wait(self.poll_seconds):
            self.refresh()

    def install(
        self,
        source: Path,
        tool_contracts: Optional[Mapping[str, Tuple[str, ...]]] = None,
    ) -> Path:
        """Validate and publish one SKILL.md without changing the platform."""

        from member_assistant.skill_authoring import (
            FileSkillPublisher,
            SkillMarkdownCompiler,
        )

        source = Path(source)
        if source.name != "SKILL.md":
            raise CatalogValidationError("Only a SKILL.md artifact can be published")
        compiled = SkillMarkdownCompiler().compile(source, tool_contracts)
        receipt = FileSkillPublisher(self.directory).publish(compiled)
        self.refresh(force=True)
        return receipt.artifact_path

    def deactivate(self, name: str) -> bool:
        """Deactivate new routing without deleting versions used by durable tasks."""

        from member_assistant.skill_authoring import FileSkillPublisher

        receipt = FileSkillPublisher(self.directory).deactivate(name)
        self.refresh(force=True)
        return receipt.deactivated

    def _relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.directory))
        except ValueError:
            return str(path)
