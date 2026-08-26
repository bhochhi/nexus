"""Provider-neutral, privacy-safe tracing with console and Langfuse exporters."""

from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
import base64
import hashlib
import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Protocol, Sequence
import uuid


LOGGER = logging.getLogger("member_assistant.trace")
_ACTIVE_CONSOLE_CONTEXT: ContextVar[Optional[Dict[str, str]]] = ContextVar(
    "member_assistant_console_trace", default=None
)
_TRACE_CONTEXT: ContextVar[Dict[str, Any]] = ContextVar(
    "member_assistant_trace_context", default={}
)

_ANSI = {
    "reset": "\033[0m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
}


def _paint(value: str, color: str, enabled: bool) -> str:
    if not enabled:
        return value
    return "{}{}{}".format(_ANSI[color], value, _ANSI["reset"])


def _compact_value(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return "{:.3f}".format(value).rstrip("0").rstrip(".")
    if isinstance(value, list):
        return ",".join(_compact_value(item) for item in value[:3])
    if isinstance(value, Mapping):
        return _json_text(value)
    return str(value)


def _pretty_console_event(event: Mapping[str, Any], color: bool = False) -> str:
    """Render the troubleshooting fields people need during an interactive demo."""

    name = str(event.get("name", "observation"))
    status = str(event.get("status", "ok"))
    palette = "red" if status == "error" else "green"
    symbol = "x" if status == "error" else "✓"
    if name.startswith("llm."):
        palette = "magenta" if status != "error" else "red"
        category = "LLM"
    elif name.startswith("policy."):
        palette = "yellow" if status != "error" else "red"
        category = "POLICY"
    elif name.startswith("skill."):
        palette = "cyan" if status != "error" else "red"
        category = "SKILL"
    elif name.startswith("tool."):
        palette = "blue" if status != "error" else "red"
        category = "TOOL"
    elif name.startswith("skill_gap."):
        palette = "yellow" if status != "error" else "red"
        category = "GAP"
    elif name == "member-assistant.turn":
        category = "TURN"
    else:
        category = "TRACE"

    metadata = dict(event.get("metadata") or {})
    output = event.get("output")
    if isinstance(output, Mapping):
        details = {**output, **metadata}
    else:
        details = metadata

    candidates = details.get("accepted_candidates", details.get("candidates"))
    if isinstance(candidates, list) and candidates:
        details["goals"] = ",".join(
            "{}@{}".format(
                candidate.get("skill", "unknown"),
                _compact_value(candidate.get("confidence", 0)),
            )
            for candidate in candidates[:5]
            if isinstance(candidate, Mapping)
        )

    fields = []
    aliases = {
        "configured_provider": "requested",
        "fallback_used": "fallback",
        "fallback_reason": "reason",
        "selected_skill": "skill",
        "skill_version": "version",
        "skill_artifact_hash": "artifact",
        "outcome_status": "outcome",
        "confirmation_status": "confirmation",
        "goal_clarification_pending": "goal_clarification",
        "handoff_offer_pending": "handoff_offer",
        "no_goal_turn_count": "no_goal_turns",
        "input_tokens": "in_tokens",
        "output_tokens": "out_tokens",
        "api_endpoint": "endpoint",
        "reasoning_effort": "reasoning",
        "provider_status": "http_status",
        "provider_error_code": "error_code",
        "provider_error_param": "error_param",
        "category": "gap_category",
        "objective": "gap_objective",
        "confidence": "gap_confidence",
    }
    keys = (
        "configured_provider",
        "provider",
        "model",
        "api_endpoint",
        "reasoning_effort",
        "fallback_used",
        "fallback_reason",
        "failure_type",
        "provider_status",
        "provider_error_code",
        "provider_error_param",
        "goals",
        "skill",
        "selected_skill",
        "skill_version",
        "skill_artifact_hash",
        "risk_tier",
        "decision",
        "policy_result",
        "outcome_status",
        "confirmation_status",
        "goal_clarification_pending",
        "handoff_offer_pending",
        "no_goal_turn_count",
        "input_tokens",
        "output_tokens",
        "category",
        "objective",
        "confidence",
    )
    seen_labels = set()
    for key in keys:
        value = details.get(key)
        if value is None or value == "":
            continue
        label = aliases.get(key, key)
        if label in seen_labels:
            continue
        seen_labels.add(label)
        compact = (
            str(value)[:12]
            if key == "skill_artifact_hash"
            else _compact_value(value)
        )
        fields.append("{}={}".format(label, compact))

    duration = event.get("duration_ms")
    suffix = " | ".join(fields)
    if duration is not None:
        suffix = (suffix + " | " if suffix else "") + "{}ms".format(
            _compact_value(duration)
        )
    prefix = _paint("{} {:6}".format(symbol, category), palette, color)
    result = "{} {}".format(prefix, name)
    if suffix:
        result += _paint("  " + suffix, "dim", color)
    return result


def _json_value(value: Any) -> Any:
    """Return a bounded JSON-compatible representation for trace fields."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]
    return str(value)


def _json_text(value: Any) -> str:
    return json.dumps(_json_value(value), sort_keys=True, separators=(",", ":"))


def _attribute_key(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", value)


class Observation(Protocol):
    def update(
        self,
        *,
        output: Any = None,
        metadata: Optional[Mapping[str, Any]] = None,
        status: Optional[str] = None,
    ) -> None:
        ...


class TraceSink(Protocol):
    name: str

    def observe(
        self,
        name: str,
        observation_type: str,
        trace_context: Mapping[str, Any],
        input_value: Any,
        metadata: Mapping[str, Any],
    ) -> Any:
        ...

    def close(self) -> None:
        ...

    def describe(self) -> Mapping[str, Any]:
        ...


@dataclass
class _ConsoleObservation:
    event: Dict[str, Any]

    def update(
        self,
        *,
        output: Any = None,
        metadata: Optional[Mapping[str, Any]] = None,
        status: Optional[str] = None,
    ) -> None:
        if output is not None:
            self.event["output"] = _json_value(output)
        if metadata:
            self.event.setdefault("metadata", {}).update(_json_value(metadata))
        if status:
            self.event["status"] = status


class ConsoleTraceSink:
    """Emits compact interactive traces or structured JSON lines."""

    name = "console"

    def __init__(self, level: str = "INFO", format_name: str = "pretty"):
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.format_name = format_name.lower()
        if self.format_name not in {"pretty", "json"}:
            raise ValueError("TRACE_CONSOLE_FORMAT must be pretty or json")
        self.color = sys.stderr.isatty() and "NO_COLOR" not in os.environ

    @contextmanager
    def observe(
        self,
        name: str,
        observation_type: str,
        trace_context: Mapping[str, Any],
        input_value: Any,
        metadata: Mapping[str, Any],
    ) -> Iterator[_ConsoleObservation]:
        parent = _ACTIVE_CONSOLE_CONTEXT.get()
        trace_id = parent["trace_id"] if parent else self._current_otel_trace_id()
        span_id = uuid.uuid4().hex[:16]
        token = _ACTIVE_CONSOLE_CONTEXT.set({"trace_id": trace_id, "span_id": span_id})
        started = time.monotonic()
        event: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "trace_observation",
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent["span_id"] if parent else None,
            "name": name,
            "type": observation_type,
            "status": "ok",
            "trace": _json_value(trace_context),
            "metadata": _json_value(metadata),
        }
        if input_value is not None:
            event["input"] = _json_value(input_value)
        observation = _ConsoleObservation(event)
        try:
            yield observation
        except BaseException as exc:
            observation.update(status="error", metadata={"error_type": type(exc).__name__})
            raise
        finally:
            event["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
            important = (
                name == "member-assistant.turn"
                or name.startswith(
                    ("llm.", "policy.", "skill.", "tool.", "skill_gap.")
                )
            )
            if self.format_name == "json":
                LOGGER.log(self.level, _json_text(event))
            elif self.level <= logging.DEBUG or important or event["status"] == "error":
                LOGGER.log(self.level, _pretty_console_event(event, self.color))
            _ACTIVE_CONSOLE_CONTEXT.reset(token)

    @staticmethod
    def _current_otel_trace_id() -> str:
        try:
            from opentelemetry import trace

            context = trace.get_current_span().get_span_context()
            if context.is_valid:
                return format(context.trace_id, "032x")
        except ImportError:
            pass
        return uuid.uuid4().hex

    def close(self) -> None:
        return None

    def describe(self) -> Mapping[str, Any]:
        return {
            "backend": self.name,
            "status": "enabled",
            "level": logging.getLevelName(self.level),
            "format": self.format_name,
        }


@dataclass
class _MemoryObservation:
    event: Dict[str, Any]

    def update(
        self,
        *,
        output: Any = None,
        metadata: Optional[Mapping[str, Any]] = None,
        status: Optional[str] = None,
    ) -> None:
        if output is not None:
            self.event["output"] = _json_value(output)
        if metadata:
            self.event.setdefault("metadata", {}).update(_json_value(metadata))
        if status:
            self.event["status"] = status


class MemoryTraceSink:
    """Deterministic sink for tests and embedding applications."""

    name = "memory"

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    @contextmanager
    def observe(
        self,
        name: str,
        observation_type: str,
        trace_context: Mapping[str, Any],
        input_value: Any,
        metadata: Mapping[str, Any],
    ) -> Iterator[_MemoryObservation]:
        event = {
            "name": name,
            "type": observation_type,
            "trace": _json_value(trace_context),
            "metadata": _json_value(metadata),
            "input": _json_value(input_value),
            "status": "ok",
        }
        observation = _MemoryObservation(event)
        started = time.monotonic()
        try:
            yield observation
        except BaseException as exc:
            observation.update(status="error", metadata={"error_type": type(exc).__name__})
            raise
        finally:
            event["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
            self.events.append(event)

    def close(self) -> None:
        return None

    def describe(self) -> Mapping[str, Any]:
        return {"backend": self.name, "status": "enabled", "events": len(self.events)}


class _OtelObservation:
    def __init__(self, span: Any):
        self.span = span

    def update(
        self,
        *,
        output: Any = None,
        metadata: Optional[Mapping[str, Any]] = None,
        status: Optional[str] = None,
    ) -> None:
        if output is not None:
            self.span.set_attribute("langfuse.observation.output", _json_text(output))
        if metadata:
            _set_otel_metadata(self.span, metadata, trace_level=False)
            _set_generation_attributes(self.span, metadata)
        if status:
            self.span.set_attribute("langfuse.observation.metadata.status", status)


def _set_otel_metadata(span: Any, metadata: Mapping[str, Any], trace_level: bool) -> None:
    prefix = "langfuse.trace.metadata" if trace_level else "langfuse.observation.metadata"
    for key, value in metadata.items():
        if value is None:
            continue
        safe_value = _json_value(value)
        if not isinstance(safe_value, (bool, int, float, str)):
            safe_value = _json_text(safe_value)
        span.set_attribute("{}.{}".format(prefix, _attribute_key(str(key))), safe_value)


def _set_generation_attributes(span: Any, metadata: Mapping[str, Any]) -> None:
    mappings = {
        "provider": "gen_ai.provider.name",
        "model": "gen_ai.request.model",
        "input_tokens": "gen_ai.usage.input_tokens",
        "output_tokens": "gen_ai.usage.output_tokens",
        "total_tokens": "gen_ai.usage.total_tokens",
    }
    for key, attribute in mappings.items():
        value = metadata.get(key)
        if value is not None:
            span.set_attribute(attribute, value)
    if metadata.get("model") is not None:
        span.set_attribute("langfuse.observation.model.name", metadata["model"])
    usage = {
        key: metadata[key]
        for key in ("input_tokens", "output_tokens", "total_tokens")
        if metadata.get(key) is not None
    }
    if usage:
        span.set_attribute("langfuse.observation.usage_details", _json_text(usage))


class LangfuseOtelSink:
    """Exports standard OTLP/HTTP spans to a Langfuse server."""

    name = "langfuse"

    def __init__(
        self,
        base_url: str,
        public_key: str,
        secret_key: str,
        service_name: str,
    ):
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
        except ImportError as exc:
            raise RuntimeError(
                "Langfuse tracing needs the observability extra: "
                "python -m pip install -e '.[observability]'"
            ) from exc

        auth = base64.b64encode(
            "{}:{}".format(public_key, secret_key).encode("utf-8")
        ).decode("ascii")
        endpoint = base_url.rstrip("/") + "/api/public/otel/v1/traces"
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers={
                "Authorization": "Basic {}".format(auth),
                "x-langfuse-ingestion-version": "4",
            },
            timeout=5,
        )
        self.base_url = base_url.rstrip("/")
        self._provider = TracerProvider(
            resource=Resource.create({"service.name": service_name})
        )
        self._provider.add_span_processor(
            BatchSpanProcessor(exporter, schedule_delay_millis=500, max_export_batch_size=64)
        )
        self._tracer = self._provider.get_tracer("member_assistant", "0.1.0")

    @contextmanager
    def observe(
        self,
        name: str,
        observation_type: str,
        trace_context: Mapping[str, Any],
        input_value: Any,
        metadata: Mapping[str, Any],
    ) -> Iterator[_OtelObservation]:
        from opentelemetry.trace import Status, StatusCode

        with self._tracer.start_as_current_span(name) as span:
            span.set_attribute("langfuse.observation.type", observation_type)
            trace_name = trace_context.get("trace_name")
            if trace_name:
                span.set_attribute("langfuse.trace.name", trace_name)
            session_id = trace_context.get("session_id")
            if session_id:
                span.set_attribute("langfuse.session.id", session_id)
            tags = trace_context.get("tags")
            if tags:
                span.set_attribute("langfuse.trace.tags", list(tags))
            environment = trace_context.get("environment")
            if environment:
                span.set_attribute("langfuse.environment", environment)
            _set_otel_metadata(
                span,
                {
                    key: value
                    for key, value in trace_context.items()
                    if key not in {"trace_name", "session_id", "tags", "environment"}
                },
                trace_level=True,
            )
            _set_otel_metadata(span, metadata, trace_level=False)
            _set_generation_attributes(span, metadata)
            if input_value is not None:
                span.set_attribute("langfuse.observation.input", _json_text(input_value))
            observation = _OtelObservation(span)
            try:
                yield observation
            except BaseException as exc:
                span.set_attribute("error.type", type(exc).__name__)
                span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
                raise

    def close(self) -> None:
        self._provider.force_flush(timeout_millis=5000)
        self._provider.shutdown()

    def describe(self) -> Mapping[str, Any]:
        return {"backend": self.name, "status": "enabled", "url": self.base_url}


@dataclass
class _CompositeObservation:
    observations: Sequence[Observation] = field(default_factory=tuple)

    def update(
        self,
        *,
        output: Any = None,
        metadata: Optional[Mapping[str, Any]] = None,
        status: Optional[str] = None,
    ) -> None:
        for observation in self.observations:
            try:
                observation.update(output=output, metadata=metadata, status=status)
            except Exception:
                LOGGER.warning("Trace observation update failed", exc_info=True)


class Observability:
    """Fans platform observations out to zero or more independent sinks."""

    def __init__(
        self,
        sinks: Iterable[TraceSink] = (),
        *,
        include_content: bool = False,
        environment: str = "local",
        hash_session_id: bool = True,
    ):
        self.sinks = tuple(sinks)
        self.include_content = include_content
        self.environment = environment
        self.hash_session_id = hash_session_id

    def content(self, value: Any, private_summary: Any) -> Any:
        return value if self.include_content else private_summary

    def session_id(self, value: str) -> str:
        if not self.hash_session_id:
            return value
        return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    @contextmanager
    def turn(
        self,
        session_id: str,
        *,
        input_value: Any,
        metadata: Mapping[str, Any],
    ) -> Iterator[_CompositeObservation]:
        trace_context = {
            "trace_name": "member-assistant.turn",
            "session_id": self.session_id(session_id),
            "environment": self.environment,
            "tags": ["member-assistant", "poc", "mock-data"],
        }
        trace_context.update(_json_value(metadata))
        token = _TRACE_CONTEXT.set(trace_context)
        try:
            with self.observe(
                "member-assistant.turn",
                "agent",
                input_value=input_value,
                metadata={"content_capture": self.include_content},
            ) as observation:
                yield observation
        finally:
            _TRACE_CONTEXT.reset(token)

    @contextmanager
    def observe(
        self,
        name: str,
        observation_type: str = "span",
        *,
        input_value: Any = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Iterator[_CompositeObservation]:
        handles: List[Observation] = []
        with ExitStack() as stack:
            for sink in self.sinks:
                try:
                    handle = stack.enter_context(
                        sink.observe(
                            name,
                            observation_type,
                            _TRACE_CONTEXT.get(),
                            input_value,
                            metadata or {},
                        )
                    )
                    handles.append(handle)
                except Exception:
                    LOGGER.warning("Trace backend %s failed to start", sink.name, exc_info=True)
            observation = _CompositeObservation(handles)
            try:
                yield observation
            except BaseException as exc:
                observation.update(status="error", metadata={"error_type": type(exc).__name__})
                raise

    def describe(self) -> Dict[str, Any]:
        return {
            "enabled": bool(self.sinks),
            "include_content": self.include_content,
            "hash_session_id": self.hash_session_id,
            "environment": self.environment,
            "backends": [dict(sink.describe()) for sink in self.sinks],
        }

    def close(self) -> None:
        for sink in self.sinks:
            try:
                sink.close()
            except Exception:
                LOGGER.warning("Trace backend %s failed to close", sink.name, exc_info=True)


def build_observability(settings: Any) -> Observability:
    sinks: List[TraceSink] = []
    backends = set(settings.trace_backends)
    unknown = backends - {"console", "langfuse", "none", "off"}
    if unknown:
        raise ValueError("Unsupported TRACE_BACKENDS: {}".format(", ".join(sorted(unknown))))
    if "langfuse" in backends:
        if not settings.langfuse_public_key or not settings.langfuse_secret_key:
            raise ValueError("LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are required")
        sinks.append(
            LangfuseOtelSink(
                settings.langfuse_base_url,
                settings.langfuse_public_key,
                settings.langfuse_secret_key,
                settings.trace_service_name,
            )
        )
    # Console starts after OTEL so both destinations expose the same trace ID.
    if "console" in backends:
        sinks.append(
            ConsoleTraceSink(settings.trace_log_level, settings.trace_console_format)
        )
    return Observability(
        sinks,
        include_content=settings.trace_include_content,
        environment=settings.trace_environment,
        hash_session_id=settings.trace_hash_session_id,
    )


__all__ = [
    "ConsoleTraceSink",
    "LangfuseOtelSink",
    "MemoryTraceSink",
    "Observability",
    "build_observability",
]
