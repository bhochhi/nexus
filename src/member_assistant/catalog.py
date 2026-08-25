"""Validated, file-based skill discovery with last-known-good reloads."""

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import re
import threading
from typing import Any, Dict, List, Mapping, Optional, Tuple


RISK_TIERS = {"informational", "navigation", "read_only", "consequential", "handoff"}
SKILL_TYPES = {
    "knowledge",
    "guided_resolution",
    "deterministic_workflow",
    "navigation",
    "human_handoff",
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


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    version: str
    skill_type: str
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

    @classmethod
    def from_dict(cls, value: Mapping[str, Any], source: Path) -> "SkillDefinition":
        required = (
            "name",
            "version",
            "type",
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
        if not isinstance(value["name"], str) or not value["name"].strip():
            raise CatalogValidationError("{}: name must be a non-empty string".format(source.name))
        if value["risk_tier"] not in RISK_TIERS:
            raise CatalogValidationError("{}: unsupported risk_tier".format(source.name))
        if value["type"] not in SKILL_TYPES:
            raise CatalogValidationError("{}: unsupported skill type".format(source.name))
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
        if not isinstance(value["input_schema"], dict):
            raise CatalogValidationError("{}: input_schema must be an object".format(source.name))
        if not isinstance(value["allowed_tools"], list):
            raise CatalogValidationError("{}: allowed_tools must be a list".format(source.name))
        if not value["allowed_tools"]:
            raise CatalogValidationError("{}: allowed_tools must be non-empty".format(source.name))
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
            if step["op"] not in TYPE_WORKFLOW_OPERATIONS[value["type"]]:
                raise CatalogValidationError(
                    "{}: operation {} is not allowed for skill type {}".format(
                        source.name, step["op"], value["type"]
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
        if value.get("confirmation_required", False) and value["type"] != "deterministic_workflow":
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
        return cls(
            name=value["name"].strip(),
            version=str(value["version"]),
            skill_type=str(value["type"]),
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
        )

    def public_contract(self) -> Dict[str, Any]:
        return asdict(self)


class SkillCatalog:
    """Loads each JSON file independently and retains its last valid definition."""

    def __init__(self, directory: Path, poll_seconds: float = 0.5):
        self.directory = Path(directory)
        self.poll_seconds = poll_seconds
        self._lock = threading.RLock()
        self._by_path: Dict[Path, SkillDefinition] = {}
        self._signatures: Dict[Path, Tuple[int, int]] = {}
        self._skills: Dict[str, SkillDefinition] = {}
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

    def get(self, name: str) -> Optional[SkillDefinition]:
        self.refresh()
        with self._lock:
            return self._skills.get(name)

    def list(self) -> List[SkillDefinition]:
        self.refresh()
        with self._lock:
            return sorted(self._skills.values(), key=lambda skill: skill.name)

    def refresh(self, force: bool = False) -> bool:
        """Refresh changed files. Invalid edits leave the prior entry active."""

        with self._lock:
            paths = set(self.directory.glob("*.json"))
            changed = False
            for deleted in set(self._by_path) - paths:
                del self._by_path[deleted]
                self._signatures.pop(deleted, None)
                self._errors.pop(deleted.name, None)
                changed = True

            for path in sorted(paths):
                stat = path.stat()
                signature = (stat.st_mtime_ns, stat.st_size)
                if not force and self._signatures.get(path) == signature:
                    continue
                self._signatures[path] = signature
                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                    definition = SkillDefinition.from_dict(raw, path)
                    collision = next(
                        (
                            existing_path
                            for existing_path, existing in self._by_path.items()
                            if existing.name == definition.name and existing_path != path
                        ),
                        None,
                    )
                    if collision is not None:
                        raise CatalogValidationError(
                            "{}: skill name duplicates {}".format(path.name, collision.name)
                        )
                    if self._by_path.get(path) != definition:
                        self._by_path[path] = definition
                        changed = True
                    self._errors.pop(path.name, None)
                except (OSError, json.JSONDecodeError, CatalogValidationError) as exc:
                    self._errors[path.name] = str(exc)

            new_skills = {definition.name: definition for definition in self._by_path.values()}
            if new_skills != self._skills:
                self._skills = new_skills
                changed = True
            if changed:
                self._revision += 1
            return changed

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

    def install(self, source: Path) -> Path:
        """Atomically copy an approved skill definition into the live catalog."""

        source = Path(source)
        raw = json.loads(source.read_text(encoding="utf-8"))
        SkillDefinition.from_dict(raw, source)
        target = self.directory / source.name
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
        os.replace(str(temporary), str(target))
        self.refresh()
        return target
