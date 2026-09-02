"""Stable LangGraph orchestration runtime."""

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import re
import threading
from typing import Any, Callable, Dict, Iterator, List, Optional
import uuid

from langgraph.graph import END, START, StateGraph

from member_assistant.catalog import (
    SkillCatalog,
    SkillDefinition,
    SkillRoutingDefinition,
)
from member_assistant.config import Settings
from member_assistant.events import AssistantEvent
from member_assistant.models import ConversationState, TaskState, WorkflowState
from member_assistant.observability import Observability, build_observability
from member_assistant.policy import PolicyEngine
from member_assistant.providers import (
    DeterministicProvider,
    ModelProvider,
    SkillGap,
    SkillMatch,
    SlotUpdate,
    build_provider,
)
from member_assistant.skills import SkillExecutorRegistry
from member_assistant.skills.base import SkillContext
from member_assistant.state_store import SQLiteConversationStore
from member_assistant.tools import MockTools


RISK_ORDER = {
    "handoff": -1,
    "informational": 0,
    "navigation": 1,
    "read_only": 2,
    "consequential": 3,
}
GOAL_CONFIDENCE_THRESHOLD = 0.5
GOAL_AMBIGUITY_MARGIN = 0.15
IMMEDIATE_HANDOFF_SKILL_GAP_CATEGORIES = {"fraud_reporting"}
SKILL_GAP_CONFIDENCE_THRESHOLD = 0.75
SLOT_CONFIDENCE_THRESHOLD = 0.65


@dataclass(frozen=True)
class AssistantReply:
    text: str
    outcome: Optional[Dict[str, Any]]
    selected_skill: Optional[str]
    catalog_revision: int


class AgentRuntime:
    """Owns shared conversation behavior while skills remain catalog-driven."""

    def __init__(
        self,
        catalog: SkillCatalog,
        store: SQLiteConversationStore,
        provider: ModelProvider,
        tools: MockTools,
        authenticated: bool = True,
        authorizations: Optional[List[str]] = None,
        observability: Optional[Observability] = None,
        handoff_offer_turn_threshold: int = 4,
    ):
        self.catalog = catalog
        self.store = store
        self.provider = provider
        self.tools = tools
        self.authenticated = authenticated
        self.authorizations = authorizations or ["balances:read", "transfers:internal"]
        self.observability = observability or Observability()
        self.handoff_offer_turn_threshold = max(1, handoff_offer_turn_threshold)
        self.executors = SkillExecutorRegistry()
        self.policy = PolicyEngine()
        self.graph = self._build_graph()
        self._session_locks: Dict[str, threading.RLock] = {}
        self._session_locks_guard = threading.Lock()
        self.catalog.start()

    @classmethod
    def from_settings(cls, settings: Optional[Settings] = None) -> "AgentRuntime":
        settings = settings or Settings.from_env()
        catalog = SkillCatalog(settings.catalog_path, settings.catalog_poll_seconds)
        store = SQLiteConversationStore(
            settings.state_db_path,
            session_ttl_seconds=settings.session_ttl_seconds,
        )
        provider = build_provider(settings)
        tools = MockTools.create(settings.knowledge_path)
        observability = build_observability(settings)
        return cls(
            catalog,
            store,
            provider,
            tools,
            observability=observability,
            handoff_offer_turn_threshold=settings.handoff_offer_turn_threshold,
        )

    def chat(
        self,
        session_id: str,
        message: str,
        client_message_id: Optional[str] = None,
    ) -> AssistantReply:
        """Run one turn and aggregate its stream for synchronous callers."""

        completed: Optional[AssistantEvent] = None
        for event in self.stream_chat(
            session_id, message, client_message_id=client_message_id
        ):
            if event.type == "turn.completed":
                completed = event
        if completed is None:
            raise RuntimeError("turn did not produce a completion event")
        return AssistantReply(
            text=str(completed.metadata["reply"]),
            outcome=deepcopy(completed.metadata.get("outcome")),
            selected_skill=completed.metadata.get("selected_skill"),
            catalog_revision=int(
                completed.metadata.get("catalog_revision", self.catalog.revision)
            ),
        )

    def stream_chat(
        self,
        session_id: str,
        message: str,
        *,
        client_message_id: Optional[str] = None,
    ) -> Iterator[AssistantEvent]:
        """Process one turn and yield durable, provider-neutral events.

        The graph still executes exactly once. ``stream_mode=values`` exposes
        stable state boundaries so the runtime can publish member-facing response
        parts without leaking LangGraph node names or provider-specific events.
        """

        if not message or not message.strip():
            raise ValueError("message must not be empty")
        if not session_id or not session_id.strip():
            raise ValueError("session_id must not be empty")
        message = message.strip()
        client_message_id = client_message_id or "msg_{}".format(uuid.uuid4().hex)
        session_lock = self._session_lock(session_id)
        with session_lock:
            proposed_turn_id = "turn_{}".format(uuid.uuid4().hex)
            claim = self.store.begin_turn(
                session_id, client_message_id, proposed_turn_id, message
            )
            turn_id = str(claim["turn_id"])
            if not claim["created"]:
                for event in self.store.stream_events(
                    session_id, turn_id=turn_id
                ):
                    yield event
                return

            sequence = 0

            def new_event(
                event_type: str,
                *,
                content: Optional[str] = None,
                final: bool = False,
                metadata: Optional[Dict[str, Any]] = None,
            ) -> AssistantEvent:
                nonlocal sequence
                sequence += 1
                event = AssistantEvent.create(
                    session_id=session_id,
                    turn_id=turn_id,
                    sequence=sequence,
                    event_type=event_type,
                    content=content,
                    final=final,
                    metadata=metadata,
                )
                self.store.append_event(event)
                return event

            yield new_event(
                "turn.accepted",
                metadata={
                    "client_message_id": client_message_id,
                    "catalog_revision": self.catalog.revision,
                },
            )
            try:
                provider_metadata = self.provider.observability_metadata()
                trace_input = self.observability.content(
                    {"message": message},
                    {"message_length": len(message), "content_redacted": True},
                )
                with self.observability.turn(
                    session_id,
                    input_value=trace_input,
                    metadata={
                        "turn_id": turn_id,
                        "client_message_id": client_message_id,
                        "catalog_revision": self.catalog.revision,
                        "provider": provider_metadata.get("provider"),
                        "model": provider_metadata.get("model"),
                    },
                ) as turn_observation:
                    with self.observability.observe(
                        "state.load", "span"
                    ) as state_observation:
                        conversation = deepcopy(self.store.load(session_id))
                        state_observation.update(
                            output={
                                "turn_count": conversation["turn_count"],
                                "active_task": bool(conversation.get("active_task")),
                                "paused_task_count": len(
                                    conversation.get("paused_tasks", [])
                                ),
                            }
                        )
                    initial_state = {
                        "session_id": session_id,
                        "conversation": conversation,
                        "incoming_message": message,
                        "goals": [],
                        "response_parts": [],
                        "audit_events": [],
                        "catalog_revision": self.catalog.revision,
                    }
                    result: Optional[WorkflowState] = None
                    emitted_part_count = 0
                    emitted_message_count = 0
                    for snapshot in self.graph.stream(
                        initial_state, stream_mode="values"
                    ):
                        result = snapshot
                        response_parts = snapshot.get("response_parts", [])
                        while emitted_part_count < len(response_parts):
                            part_index = emitted_part_count
                            part = str(response_parts[part_index]).strip()
                            emitted_part_count += 1
                            if not part:
                                continue
                            event_type, message_kind = self._stream_message_type(
                                snapshot["conversation"],
                                is_latest=part_index == len(response_parts) - 1,
                            )
                            content = self._stream_message_content(
                                part,
                                snapshot["conversation"],
                                is_first=part_index == 0,
                            )
                            active_task = snapshot["conversation"].get("active_task")
                            emitted_message_count += 1
                            yield new_event(
                                event_type,
                                content=content,
                                metadata={
                                    "message_kind": message_kind,
                                    "selected_skill": snapshot["conversation"].get(
                                        "selected_skill"
                                    ),
                                    "task_id": active_task.get("id")
                                    if active_task
                                    else None,
                                },
                            )
                    if result is None or "reply" not in result:
                        raise RuntimeError("graph did not produce a final state")
                    final_conversation = result["conversation"]
                    final_reply = str(result["reply"]).strip()
                    if not emitted_message_count and final_reply:
                        event_type, message_kind = self._stream_message_type(
                            final_conversation,
                            is_latest=True,
                        )
                        active_task = final_conversation.get("active_task")
                        yield new_event(
                            event_type,
                            content=final_reply,
                            metadata={
                                "message_kind": message_kind,
                                "selected_skill": final_conversation.get(
                                    "selected_skill"
                                ),
                                "task_id": active_task.get("id")
                                if active_task
                                else None,
                            },
                        )
                    self._persist_turn(session_id, result)
                    final_metadata = {
                        "client_message_id": client_message_id,
                        "reply": result["reply"],
                        "selected_skill": final_conversation.get("selected_skill"),
                        "outcome": deepcopy(final_conversation.get("outcome")),
                        "outcome_status": (
                            final_conversation.get("outcome") or {}
                        ).get("status"),
                        "confirmation_status": final_conversation[
                            "confirmation_status"
                        ],
                        "catalog_revision": result.get(
                            "catalog_revision", self.catalog.revision
                        ),
                        "turn": final_conversation["turn_count"],
                        "sentiment": final_conversation.get("sentiment", "unknown"),
                        "sentiment_confidence": final_conversation.get(
                            "sentiment_confidence", 0.0
                        ),
                        **self.provider.observability_metadata(),
                    }
                    completed_event = new_event(
                        "turn.completed", final=True, metadata=final_metadata
                    )
                    self.store.complete_turn(turn_id, "completed")
                    turn_observation.update(
                        output=self.observability.content(
                            {"reply": result["reply"]},
                            {
                                "reply_length": len(result["reply"]),
                                "content_redacted": True,
                            },
                        ),
                        metadata={
                            "turn_id": turn_id,
                            "selected_skill": final_conversation.get(
                                "selected_skill"
                            ),
                            "outcome_status": final_metadata["outcome_status"],
                            "confirmation_status": final_metadata[
                                "confirmation_status"
                            ],
                            "goal_clarification_pending": bool(
                                final_conversation.get("pending_goal_clarification")
                            ),
                            "handoff_offer_pending": bool(
                                final_conversation.get("pending_handoff_offer")
                            ),
                            "task_transition_pending": bool(
                                final_conversation.get("pending_task_transition")
                            ),
                            "no_goal_turn_count": final_conversation.get(
                                "no_goal_turn_count", 0
                            ),
                            "sentiment": final_conversation.get(
                                "sentiment", "unknown"
                            ),
                            "negative_sentiment_streak": final_conversation.get(
                                "negative_sentiment_streak", 0
                            ),
                            "turn": final_conversation["turn_count"],
                        },
                    )
                    yield completed_event
            except Exception as exc:
                failed_event = new_event(
                    "turn.failed",
                    content="I couldn't complete that request safely. Please try again.",
                    final=True,
                    metadata={
                        "client_message_id": client_message_id,
                        "error_type": type(exc).__name__,
                    },
                )
                self.store.complete_turn(turn_id, "failed")
                yield failed_event
                raise

    def _session_lock(self, session_id: str) -> threading.RLock:
        with self._session_locks_guard:
            return self._session_locks.setdefault(session_id, threading.RLock())

    def _persist_turn(self, session_id: str, result: WorkflowState) -> None:
        final_conversation = result["conversation"]
        with self.observability.observe(
            "state.persist",
            "span",
            metadata={"audit_event_count": len(result.get("audit_events", [])) + 1},
        ) as state_observation:
            self.store.save(session_id, final_conversation)
            for event in result.get("audit_events", []):
                self.store.append_audit(
                    session_id, event["event_type"], event["payload"]
                )
            self.store.append_audit(
                session_id,
                "turn_completed",
                {
                    "turn": final_conversation["turn_count"],
                    "selected_skill": final_conversation["selected_skill"],
                    "confirmation_status": final_conversation["confirmation_status"],
                    "outcome_status": (final_conversation.get("outcome") or {}).get(
                        "status"
                    ),
                    "goal_clarification_pending": bool(
                        final_conversation.get("pending_goal_clarification")
                    ),
                    "handoff_offer_pending": bool(
                        final_conversation.get("pending_handoff_offer")
                    ),
                    "task_transition_pending": bool(
                        final_conversation.get("pending_task_transition")
                    ),
                    "no_goal_turn_count": final_conversation.get(
                        "no_goal_turn_count", 0
                    ),
                    "sentiment": final_conversation.get("sentiment", "unknown"),
                    "sentiment_confidence": final_conversation.get(
                        "sentiment_confidence", 0.0
                    ),
                    "negative_sentiment_streak": final_conversation.get(
                        "negative_sentiment_streak", 0
                    ),
                    "catalog_revision": result.get(
                        "catalog_revision", self.catalog.revision
                    ),
                },
            )
            state_observation.update(output={"status": "saved"})

    @staticmethod
    def _stream_message_content(
        content: str, conversation: ConversationState, *, is_first: bool
    ) -> str:
        if is_first and not conversation.get("greeted"):
            preferred_name = conversation.get("member_profile", {}).get(
                "preferred_name", "Member"
            )
            greeting = "Hi {}.".format(preferred_name)
            if not content.casefold().startswith(greeting.casefold()):
                return "{} {}".format(greeting, content)
        return content

    @staticmethod
    def _stream_message_type(
        conversation: ConversationState, *, is_latest: bool
    ) -> tuple:
        if not is_latest:
            return "assistant.message", "informational"
        active_task = conversation.get("active_task")
        if conversation.get("pending_handoff_offer"):
            return "handoff.offered", "handoff_offer"
        if conversation.get("pending_task_transition") or (
            active_task and active_task.get("status") == "awaiting_confirmation"
        ):
            return "assistant.request_confirmation", "confirmation"
        if (
            conversation.get("pending_goal_clarification")
            or conversation.get("pending_clarification")
            or (active_task and active_task.get("status") == "awaiting_input")
        ):
            return "assistant.request_input", "elicitation"
        return "assistant.message", "informational"

    def inspect_state(self, session_id: str) -> ConversationState:
        return self.store.inspect(session_id)

    def set_member_name(self, session_id: str, name: str) -> ConversationState:
        """Persist the UI-supplied display name without changing session identity."""

        clean_name = " ".join(str(name).split())[:80]
        if not clean_name:
            raise ValueError("member name must not be empty")
        with self._session_lock(session_id):
            conversation = self.store.load(session_id)
            conversation["member_profile"] = {
                **conversation.get("member_profile", {}),
                "member_ref": session_id,
                "first_name": clean_name.split()[0],
                "preferred_name": clean_name,
            }
            self.store.save(session_id, conversation)
        return deepcopy(conversation)

    def analyze_live_sentiment(self, session_id: str, message: str) -> Dict[str, Any]:
        """Classify a live member utterance while preserving conversational context."""

        conversation = self.store.load(session_id)
        context = {
            "previous_sentiment": conversation.get("sentiment", "unknown"),
            "negative_sentiment_streak": conversation.get(
                "negative_sentiment_streak", 0
            ),
            "recent_member_messages": [
                item.get("content", "")[:240]
                for item in conversation.get("messages", [])[-8:]
                if item.get("role") == "user"
            ],
        }
        with self.observability.observe(
            "llm.live_sentiment",
            "generation",
            input_value=self.observability.content(
                {"message": message, "context": context},
                {
                    "message_length": len(message),
                    "context_message_count": len(context["recent_member_messages"]),
                    "content_redacted": True,
                },
            ),
            metadata=self.provider.observability_metadata(),
        ) as observation:
            fallback_used = False
            try:
                analysis = self.provider.understand_turn(message, [], context)
            except Exception:
                fallback_used = True
                analysis = DeterministicProvider().understand_turn(
                    message, [], context
                )
            observation.update(
                output={
                    "sentiment": analysis.sentiment,
                    "confidence": analysis.sentiment_confidence,
                },
                metadata={
                    **self.provider.observability_metadata(),
                    "fallback_used": fallback_used,
                },
            )
        if analysis.sentiment == "unknown":
            fallback = DeterministicProvider().understand_turn(message, [], context)
            sentiment = fallback.sentiment
            confidence = fallback.sentiment_confidence
        else:
            sentiment = analysis.sentiment
            confidence = analysis.sentiment_confidence
        with self._session_lock(session_id):
            conversation = self.store.load(session_id)
            conversation["messages"].append({"role": "user", "content": message})
            self._apply_sentiment(conversation, sentiment, confidence)
            self.store.save(session_id, conversation)
            self.store.append_audit(
                session_id,
                "live_sentiment_updated",
                {
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "negative_sentiment_streak": conversation.get(
                        "negative_sentiment_streak", 0
                    ),
                },
            )
        return {"sentiment": sentiment, "confidence": confidence}

    def end_handoff(self, session_id: str, ended_by: str) -> Dict[str, Any]:
        """Return a member to the virtual assistant and emit a durable welcome-back."""

        content = (
            "You're back with the virtual assistant. What else can I help you with?"
        )
        with self._session_lock(session_id):
            conversation = self.store.load(session_id)
            conversation["handoff_status"] = "ended"
            conversation["selected_skill"] = None
            conversation["outcome"] = {
                "status": "ended",
                "ended_by": ended_by,
            }
            conversation["messages"].append(
                {"role": "assistant", "content": content}
            )
            self.store.save(session_id, conversation)
            turn_id = "turn_live_end_{}".format(uuid.uuid4().hex)
            event = AssistantEvent.create(
                session_id=session_id,
                turn_id=turn_id,
                sequence=1,
                event_type="assistant.message",
                content=content,
                final=True,
                metadata={"message_kind": "handoff_return", "ended_by": ended_by},
            )
            self.store.append_event(event)
            self.store.append_audit(
                session_id,
                "live_handoff_ended",
                {"ended_by": ended_by},
            )
        return event.as_dict()

    def handoff_summary(
        self,
        session_id: str,
        reason: str,
        structured_summary: str = "",
    ) -> str:
        """Build structured fields plus one grounded paragraph for the assigned MSR."""

        conversation = self.store.load(session_id)
        transcript = [
            {
                "role": "member" if item.get("role") == "user" else "assistant",
                "content": " ".join(str(item.get("content", "")).split())[:500],
            }
            for item in conversation.get("messages", [])[-24:]
            if item.get("role") in {"user", "assistant"}
            and str(item.get("content", "")).strip()
        ]
        clean_reason = " ".join(reason.split())[:300] or "member requested live support"
        fields = "\n".join(
            " ".join(line.split())
            for line in structured_summary.splitlines()
            if line.strip()
        )[:1200]
        if not fields:
            fields = "Goal: {0}\nReason: {0}\nCompleted: none".format(clean_reason)

        fallback_paragraph = (
            "The member is requesting help with {} No additional completed actions "
            "or outcomes were recorded for the handoff."
        ).format(clean_reason.rstrip(".") + ".")
        facts = {
            "structured_handoff": fields,
            "reason": clean_reason,
            "transcript": transcript,
            # The deterministic provider renders this safe availability fallback.
            "template": fallback_paragraph,
        }
        instruction = (
            "Write one concise paragraph for a human support representative summarizing "
            "the member's discussion. Use only the supplied transcript and structured "
            "handoff facts. State the issue, relevant context already discussed, what the "
            "assistant completed or explained, and what remains unresolved when those facts "
            "are present. Ignore greetings, yes/no handoff confirmation, queue-selection "
            "logistics, and the final connection notice. Do not invent facts, decisions, "
            "causes, or outcomes. Do not repeat the Goal, Reason, or Completed labels. Return "
            "one plain-text paragraph of two to four sentences and at most 800 characters."
        )
        with self.observability.observe(
            "llm.handoff_summary",
            "generation",
            input_value=self.observability.content(
                facts,
                {
                    "transcript_message_count": len(transcript),
                    "content_redacted": True,
                },
            ),
            metadata=self.provider.observability_metadata(),
        ) as observation:
            fallback_used = False
            try:
                paragraph = self.provider.generate_response(instruction, facts)
            except Exception:
                fallback_used = True
                paragraph = fallback_paragraph
            paragraph = " ".join(str(paragraph).split())
            if paragraph.casefold().startswith("summary:"):
                paragraph = paragraph.split(":", 1)[1].strip()
            paragraph = paragraph[:800].rstrip() or fallback_paragraph
            observation.update(
                output={"summary_length": len(paragraph)},
                metadata={
                    **self.provider.observability_metadata(),
                    "fallback_used": fallback_used,
                },
            )
        return "{}\n\nSummary: {}".format(fields, paragraph)[:2200]

    def close(self) -> None:
        self.catalog.stop()
        self.store.close()
        self.observability.close()

    def _build_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("understand", self._traced_node("understand", self._understand))
        graph.add_node("plan_goals", self._traced_node("plan_goals", self._plan_goals))
        graph.add_node("supply_input", self._traced_node("supply_input", self._supply_input))
        graph.add_node(
            "handle_confirmation",
            self._traced_node("handle_confirmation", self._handle_confirmation),
        )
        graph.add_node("handle_resume", self._traced_node("handle_resume", self._handle_resume))
        graph.add_node("policy", self._traced_node("policy", self._check_policy))
        graph.add_node("execute_skill", self._traced_node("execute_skill", self._execute_skill))
        graph.add_node("advance", self._traced_node("advance", self._advance))
        graph.add_node("finalize", self._traced_node("finalize", self._finalize))

        graph.add_edge(START, "understand")
        graph.add_conditional_edges(
            "understand",
            lambda state: state["next_action"],
            {
                "plan": "plan_goals",
                "supply_input": "supply_input",
                "confirmation": "handle_confirmation",
                "resume": "handle_resume",
                "policy": "policy",
                "finalize": "finalize",
            },
        )
        graph.add_conditional_edges(
            "plan_goals",
            lambda state: state["next_action"],
            {"policy": "policy", "finalize": "finalize"},
        )
        graph.add_edge("supply_input", "policy")
        graph.add_conditional_edges(
            "handle_confirmation",
            lambda state: state["next_action"],
            {"policy": "policy", "advance": "advance", "finalize": "finalize"},
        )
        graph.add_edge("handle_resume", "finalize")
        graph.add_conditional_edges(
            "policy",
            lambda state: state["next_action"],
            {"execute": "execute_skill", "advance": "advance", "finalize": "finalize"},
        )
        graph.add_edge("execute_skill", "advance")
        graph.add_conditional_edges(
            "advance",
            lambda state: state["next_action"],
            {"policy": "policy", "finalize": "finalize"},
        )
        graph.add_edge("finalize", END)
        return graph.compile()

    def _traced_node(
        self,
        name: str,
        function: Callable[[WorkflowState], Dict[str, Any]],
    ) -> Callable[[WorkflowState], Dict[str, Any]]:
        def invoke(state: WorkflowState) -> Dict[str, Any]:
            conversation = state.get("conversation", {})
            active = conversation.get("active_task") if conversation else None
            with self.observability.observe(
                "graph.{}".format(name),
                "chain",
                metadata={
                    "node": name,
                    "active_skill": active.get("skill_name") if active else None,
                    "task_status": active.get("status") if active else None,
                },
            ) as observation:
                result = function(state)
                updated = result.get("conversation", conversation)
                updated_active = updated.get("active_task") if updated else None
                observation.update(
                    output={
                        "next_action": result.get("next_action"),
                        "goal_count": len(result.get("goals", state.get("goals", []))),
                        "selected_skill": updated.get("selected_skill") if updated else None,
                        "task_status": updated_active.get("status")
                        if updated_active
                        else None,
                    }
                )
                return result

        return invoke

    def _understand(self, state: WorkflowState) -> Dict[str, Any]:
        conversation = state["conversation"]
        message = state["incoming_message"]
        conversation["messages"].append({"role": "user", "content": message})
        if not conversation.get("active_task") and not conversation.get("awaiting_resume"):
            conversation["selected_skill"] = None
            conversation["outcome"] = None
            conversation["confirmation_status"] = "not_required"
        # New-goal understanding uses the small hot-reloadable routing index. An
        # in-flight task also contributes its exact pinned input contract so it can
        # finish naturally after that version is deactivated for new requests.
        catalog = self.catalog.routes()
        active = conversation.get("active_task")
        pending_transition = conversation.get("pending_task_transition")
        queued = conversation.get("queued_tasks", [])
        pending_task = (
            queued[0]
            if pending_transition
            and queued
            and queued[0].get("id") == pending_transition.get("task_id")
            else None
        )
        understanding_task = active or pending_task
        understanding_definition = (
            self._task_definition(understanding_task) if understanding_task else None
        )
        active_route = next(
            (
                route
                for route in catalog
                if active and route.name == active.get("skill_name")
            ),
            None,
        )
        understanding_catalog = list(catalog)
        if active and active_route is None:
            active_definition = self._task_definition(active)
            if active_definition is not None:
                active_route = active_definition.routing_definition()
                understanding_catalog.append(active_route)
        understanding_route = next(
            (
                route
                for route in understanding_catalog
                if understanding_task
                and route.name == understanding_task.get("skill_name")
            ),
            None,
        )
        if understanding_task and understanding_route is None:
            if understanding_definition is not None:
                understanding_route = understanding_definition.routing_definition()
                understanding_catalog.append(understanding_route)
        goal_context = {
            "active_skill": (
                understanding_task.get("skill_name") if understanding_task else None
            ),
            "active_goal": (
                understanding_task.get("goal") if understanding_task else None
            ),
            "last_selected_skill": conversation.get("last_completed_skill"),
            "task_status": (
                "pending_transition"
                if pending_task and not active
                else (understanding_task.get("status") if understanding_task else None)
            ),
            "missing_field": (
                understanding_task.get("missing_field") if understanding_task else None
            ),
            "pending_question": (
                understanding_task.get("pending_question")
                if understanding_task
                else None
            ),
            "current_inputs": (
                dict(understanding_task.get("inputs", {}))
                if understanding_task
                else {}
            ),
            "active_input_schema": (
                dict(understanding_route.input_schema) if understanding_route else {}
            ),
            # A v2 Markdown body is the model-facing Tier 2 activation contract.
            # Legacy v1 bodies may contain executable YAML, so they stay runtime-only.
            "active_skill_instructions": (
                understanding_definition.activation_instructions[:5000]
                if understanding_definition is not None
                and understanding_definition.api_version
                in {"nexus.skills/v2", "nexus.skills/v3"}
                else ""
            ),
            "recent_messages": [
                {
                    "role": str(item.get("role", "")),
                    "content": " ".join(str(item.get("content", "")).split())[:500],
                }
                for item in conversation.get("messages", [])[-8:]
                if item.get("role") in {"user", "assistant"}
            ],
            "awaiting_resume": conversation.get("awaiting_resume", False),
            "pending_goal_candidates": [
                candidate.get("skill_name")
                for candidate in (
                    conversation.get("pending_goal_clarification") or {}
                ).get("candidates", [])
            ],
            "pending_task_transition": bool(pending_transition),
            "pending_task_transition_question": (
                pending_transition.get("question") if pending_transition else None
            ),
            "previous_sentiment": conversation.get("sentiment", "unknown"),
            "negative_sentiment_streak": conversation.get(
                "negative_sentiment_streak", 0
            ),
        }
        with self.observability.observe(
            "llm.turn_understanding",
            "generation",
            input_value=self.observability.content(
                {"message": message, "available_skills": [skill.name for skill in catalog]},
                {
                    "message_length": len(message),
                    "available_skill_count": len(catalog),
                    "content_redacted": True,
                },
            ),
            metadata=self.provider.observability_metadata(),
        ) as generation:
            provider_analysis = self.provider.understand_turn(
                message, understanding_catalog, goal_context
            )
            if provider_analysis.safety_intervened:
                provider_metadata = self.provider.observability_metadata()
                generation.update(
                    output={
                        "safety_intervened": True,
                        "skill_match_count": 0,
                        "accepted_skill_match_count": 0,
                    },
                    metadata=provider_metadata,
                )
                self._ensure_member_profile(conversation)
                conversation["outcome"] = {
                    "status": provider_metadata.get("stop_reason")
                    or "safety_intervened"
                }
                return {
                    "conversation": conversation,
                    "goals": [],
                    "slot_updates": {},
                    "conversation_act": "unknown",
                    "active_goal_relation": "none",
                    "catalog_revision": self.catalog.revision,
                    "next_action": "finalize",
                    "response_parts": [
                        provider_analysis.safety_response
                        or "I'm sorry, but I can't help with that request."
                    ],
                    "audit_events": state.get("audit_events", [])
                    + [
                        {
                            "event_type": "provider_safety_intervention",
                            "payload": {
                                "provider": provider_metadata.get("provider"),
                                "model": provider_metadata.get("model"),
                                "stop_reason": provider_metadata.get("stop_reason"),
                                "guardrail_intervened": provider_metadata.get(
                                    "guardrail_intervened", False
                                ),
                            },
                        }
                    ],
                }
            (
                provider_matches,
                _,
                rejected_provider_skills,
            ) = self._normalize_skill_matches(
                provider_analysis.skill_matches, understanding_catalog
            )
            provider_metadata = self.provider.observability_metadata()
            # The configured provider already owns fallback behavior. Mixing a
            # second deterministic interpretation into every successful LLM turn
            # can overwrite semantics with shape- or keyword-based guesses.
            # Preserve deterministic candidates only when that provider actually
            # handled this turn (offline mode or an explicit availability fallback).
            deterministic_turn = (
                provider_metadata.get("understanding_mode") != "semantic"
            )
            deterministic_matches = provider_matches if deterministic_turn else []
            goal_matches = provider_matches
            accepted_matches = [
                match
                for match in goal_matches
                if match.confidence >= GOAL_CONFIDENCE_THRESHOLD
            ]
            skill_gap = provider_analysis.skill_gap
            accepted_skill_gap = (
                skill_gap
                if skill_gap
                and skill_gap.confidence >= SKILL_GAP_CONFIDENCE_THRESHOLD
                else None
            )
            conversation_act = provider_analysis.conversation_act
            active_goal_relation = provider_analysis.active_goal_relation
            slot_updates: Dict[str, Any] = {}
            rejected_slot_updates = 0
            if understanding_route and understanding_task:
                # Goal inputs describe a newly requested goal. During an active
                # task, only explicitly bound slot updates may change task inputs;
                # recycling routing extraction here can turn a shape match (for
                # example, a four-digit identifier) into the wrong field.
                slot_updates, rejected_slot_updates = self._normalize_slot_updates(
                    list(provider_analysis.slot_updates),
                    understanding_route,
                    pending_field=str(understanding_task.get("missing_field") or ""),
                    conversation_act=conversation_act,
                    current_inputs=dict(understanding_task.get("inputs", {})),
                    prior_member_messages=[
                        str(item.get("content", ""))
                        for item in conversation.get("messages", [])[:-1]
                        if item.get("role") == "user"
                    ][-8:],
                )
            sentiment = provider_analysis.sentiment
            sentiment_confidence = provider_analysis.sentiment_confidence
            self._apply_sentiment(
                conversation, sentiment, sentiment_confidence
            )
            generation_output = {
                "skill_match_count": len(goal_matches),
                "candidates": [
                    {
                        "skill": match.skill_name,
                        "confidence": match.confidence,
                    }
                    for match in goal_matches
                ],
                "accepted_skill_match_count": len(accepted_matches),
                "accepted_candidates": [
                    {
                        "skill": match.skill_name,
                        "confidence": match.confidence,
                    }
                    for match in accepted_matches
                ],
                "rejected_candidate_count": len(goal_matches)
                - len(accepted_matches),
                "skill_gap_detected": bool(accepted_skill_gap),
                "skill_gap": (
                    accepted_skill_gap.as_dict() if accepted_skill_gap else None
                ),
                "conversation_act": conversation_act,
                "active_goal_relation": active_goal_relation,
                "understanding_mode": (
                    "deterministic_fallback" if deterministic_turn else "semantic"
                ),
                "sentiment": sentiment,
                "sentiment_confidence": sentiment_confidence,
                "negative_sentiment_streak": conversation.get(
                    "negative_sentiment_streak", 0
                ),
                "slot_update_count": len(slot_updates),
                "slot_update_fields": [
                    field_name
                    for field_name in (
                        active_route.input_schema.get("properties", {}).keys()
                        if active_route
                        else []
                    )
                    if field_name in slot_updates
                ],
            }
            if rejected_slot_updates:
                generation_output["rejected_slot_update_count"] = (
                    rejected_slot_updates
                )
            if rejected_provider_skills:
                generation_output["rejected_provider_skill_count"] = (
                    rejected_provider_skills
                )
            generation.update(
                output=generation_output,
                metadata=provider_metadata,
            )
        self._ensure_member_profile(conversation)
        goals = [
            {**match.as_dict(), "goal": match.skill_name}
            for match in accepted_matches
        ]
        deterministic_goals = [
            {**match.as_dict(), "goal": match.skill_name}
            for match in deterministic_matches
            if match.confidence >= GOAL_CONFIDENCE_THRESHOLD
        ]
        updates: Dict[str, Any] = {
            "conversation": conversation,
            "goals": goals,
            "slot_updates": slot_updates,
            "conversation_act": conversation_act,
            "active_goal_relation": active_goal_relation,
            "catalog_revision": self.catalog.revision,
        }
        # Reception is a runtime capability, not a catalog skill. Do not let a
        # speculative provider skill-gap turn a clear "what can you do?" request
        # into an unsupported-objective response or audit event.
        is_reception_turn = not goals and self._is_greeting_or_capability_question(
            message
        )
        if accepted_skill_gap and not is_reception_turn:
            self._record_skill_gap(
                updates,
                state,
                accepted_skill_gap,
                catalog,
                provider_metadata,
            )

        pending_handoff = conversation.get("pending_handoff_offer")
        if pending_handoff:
            if self._is_affirmative(message):
                handoff_goal = self._handoff_goal(catalog, pending_handoff)
                conversation["pending_handoff_offer"] = None
                conversation["no_goal_turn_count"] = 0
                if not handoff_goal:
                    updates.update(
                        next_action="finalize",
                        response_parts=["Live-agent support is not currently available."],
                    )
                else:
                    updates.update(goals=[handoff_goal], next_action="plan")
                return updates
            if self._is_negative(message):
                conversation["pending_handoff_offer"] = None
                conversation["no_goal_turn_count"] = 0
                updates.update(
                    next_action="finalize",
                    response_parts=[
                        "Okay, I won't connect a live agent. Tell me what you'd like to accomplish, "
                        "and I'll keep helping here."
                    ],
                )
                return updates
            conversation["pending_handoff_offer"] = None

        pending_goal = conversation.get("pending_goal_clarification")
        if pending_goal:
            pending_candidates, _, _ = self._normalize_goal_dicts(
                list(pending_goal.get("candidates", [])), catalog
            )
            if not pending_candidates:
                conversation["pending_goal_clarification"] = None
                updates.update(
                    goals=[],
                    next_action="finalize",
                    response_parts=[
                        "That previously discussed capability is no longer available. "
                        "Tell me what you'd like help with."
                    ],
                )
                return updates
            pending_goal = {**pending_goal, "candidates": pending_candidates}
            conversation["pending_goal_clarification"] = pending_goal
            resolved = self._resolve_pending_goal_clarification(
                message, goals, deterministic_goals, pending_goal
            )
            if resolved is None:
                if accepted_skill_gap:
                    return self._respond_to_skill_gap(
                        updates,
                        conversation,
                        accepted_skill_gap,
                        continuation=pending_goal["question"],
                    )
                response = pending_goal["question"]
                # An affirmative answer is meaningful for a confirmation, but it
                # does not identify one item from two alternatives. Repeating the
                # same either/or question leaves the member with no new guidance.
                if self._is_affirmative(message) and len(pending_candidates) > 1:
                    labels = [
                        self._goal_label(candidate["skill_name"], candidate["goal"])
                        for candidate in pending_candidates[:2]
                    ]
                    response = (
                        "I can help with either. Please choose one first: say "
                        "‘{}’ or ‘{}’."
                    ).format(labels[0], labels[1])
                updates.update(
                    goals=[],
                    next_action="finalize",
                    response_parts=[response],
                )
                return updates
            conversation["pending_goal_clarification"] = None
            goals = resolved
            updates["goals"] = goals

        # Handoff is a governed catalog goal, not a deterministic-only route.
        # A semantic provider's accepted match must trigger the same consent
        # boundary as an offline deterministic match.
        handoff_candidates = [
            goal
            for goal in goals + deterministic_goals
            if self._is_handoff_goal(goal, catalog)
        ]
        handoff_requested = bool(handoff_candidates)
        sentiment_escalation = (
            conversation.get("sentiment") == "frustrated"
            or int(conversation.get("negative_sentiment_streak", 0)) >= 2
        )
        active_is_handoff = bool(active_route and active_route.risk_tier == "handoff")
        if (
            not active_is_handoff
            and (handoff_requested or self._is_frustrated(message) or sentiment_escalation)
        ):
            handoff_inputs = next(
                (
                    goal.get("inputs", {})
                    for goal in handoff_candidates
                    if goal.get("inputs", {}).get("queue")
                ),
                {},
            )
            return self._offer_handoff(
                updates,
                conversation,
                reason=(
                    "member explicitly requested a live agent"
                    if handoff_requested
                    else "member sentiment indicates additional support is appropriate"
                ),
                inputs=handoff_inputs,
            )

        pending_transition = conversation.get("pending_task_transition")
        if pending_transition:
            queued = conversation.get("queued_tasks", [])
            next_task = queued[0] if queued else None
            if not next_task or next_task.get("id") != pending_transition.get("task_id"):
                conversation["pending_task_transition"] = None
            elif self._is_affirmative(message):
                # The same semantic turn may confirm the transition and recover
                # still-missing queued-task inputs from evidenced conversation
                # history. Apply them before deterministic execution begins.
                if slot_updates:
                    next_task.setdefault("inputs", {}).update(slot_updates)
                conversation["active_task"] = queued.pop(0)
                conversation["pending_task_transition"] = None
                conversation["selected_skill"] = next_task["skill_name"]
                conversation["outcome"] = None
                conversation["confirmation_status"] = "not_required"
                conversation["no_goal_turn_count"] = 0
                updates.update(goals=[], next_action="policy")
                return updates
            elif self._is_negative(message):
                discarded = queued.pop(0)
                conversation["pending_task_transition"] = None
                conversation["outcome"] = {
                    "status": "discarded",
                    "task_id": discarded["id"],
                }
                response_parts = [
                    "Okay, I won't continue with that {} request.".format(
                        pending_transition["goal_label"]
                    )
                ]
                if queued:
                    transition = self._new_task_transition(queued[0])
                    conversation["pending_task_transition"] = transition
                    response_parts.append(transition["question"])
                updates.update(
                    goals=[], next_action="finalize", response_parts=response_parts
                )
                return updates
            elif goals:
                for queued_task in queued:
                    queued_task["resume_status"] = queued_task.get("status", "ready")
                    queued_task["status"] = "paused"
                    conversation["paused_tasks"].append(queued_task)
                conversation["queued_tasks"] = []
                conversation["pending_task_transition"] = None
                return self._route_goal_candidates(
                    updates, conversation, message, goals, deterministic_goals
                )
            else:
                updates.update(
                    goals=[],
                    next_action="finalize",
                    response_parts=[pending_transition["question"]],
                )
                return updates

        if is_reception_turn and active:
            continuation = active.get("pending_question")
            if active.get("status") == "awaiting_confirmation":
                continuation = self._confirmation_copy(
                    active,
                    "retry_response",
                    "Your current request is still waiting. Please answer yes to continue "
                    "or no to cancel it.",
                )
            updates.update(
                goals=[],
                next_action="finalize",
                response_parts=[
                    "{} Your current request is still here. {}".format(
                        self._reception_response(conversation, catalog),
                        continuation or "What information would you like to provide next?",
                    )
                ],
            )
            return updates

        if active and active.get("status") == "awaiting_confirmation":
            if self._is_yes_or_no(message):
                updates["next_action"] = "confirmation"
            elif self._has_explicit_new_goal(active, message, goals, deterministic_goals):
                return self._route_goal_candidates(
                    updates, conversation, message, goals, deterministic_goals
                )
            elif slot_updates:
                updates.update(next_action="supply_input", slot_correction=True)
            elif accepted_skill_gap:
                return self._respond_to_skill_gap(
                    updates,
                    conversation,
                    accepted_skill_gap,
                    continuation=self._confirmation_copy(
                        active,
                        "retry_response",
                        "Your current request is still waiting. Please answer yes to continue "
                        "or no to cancel it.",
                    ),
                )
            else:
                updates.update(
                    next_action="finalize",
                    response_parts=[
                        self._confirmation_copy(
                            active,
                            "retry_response",
                            "Please answer yes to continue the reviewed action or no to cancel it.",
                        )
                    ],
                )
            return updates

        if active and active.get("status") == "awaiting_input":
            if (
                not active_is_handoff
                and self._has_explicit_new_goal(
                    active, message, goals, deterministic_goals
                )
            ):
                return self._route_goal_candidates(
                    updates, conversation, message, goals, deterministic_goals
                )
            if accepted_skill_gap:
                return self._respond_to_skill_gap(
                    updates,
                    conversation,
                    accepted_skill_gap,
                    continuation=(
                        "Your current request is still here. {}".format(
                            active.get("pending_question")
                            or "What information would you like to provide next?"
                        )
                    ),
                )
            if active_goal_relation == "ambiguous" and not slot_updates:
                updates.update(
                    goals=[],
                    next_action="finalize",
                    response_parts=[
                        active.get("pending_question")
                        or "Could you clarify the information for your current request?"
                    ],
                )
                return updates
            if not slot_updates:
                # Do not assign arbitrary raw text to the field that happens to
                # be pending. The turn-understanding provider must establish the
                # semantic field/value binding first; otherwise keep eliciting.
                updates.update(
                    goals=[],
                    next_action="finalize",
                    response_parts=[
                        active.get("pending_question")
                        or "Could you clarify the information for your current request?"
                    ],
                )
                return updates
            correction = bool(
                conversation_act == "correction"
                and any(
                    field_name in active.get("inputs", {})
                    and active.get("inputs", {}).get(field_name) != value
                    for field_name, value in slot_updates.items()
                )
            )
            updates.update(
                goals=[], next_action="supply_input", slot_correction=correction
            )
            return updates

        if conversation.get("awaiting_resume"):
            if self._is_resume_or_discard(message):
                updates["next_action"] = "resume"
            elif goals:
                return self._route_goal_candidates(
                    updates, conversation, message, goals, deterministic_goals
                )
            elif accepted_skill_gap:
                return self._respond_to_skill_gap(
                    updates,
                    conversation,
                    accepted_skill_gap,
                    continuation=(
                        "Your paused request is still available. Please say resume to continue "
                        "it or discard to remove it."
                    ),
                )
            else:
                updates.update(
                    next_action="finalize",
                    response_parts=[
                        "Please say resume to continue the paused task or discard to remove it."
                    ],
                )
            return updates

        if is_reception_turn:
            updates.update(
                next_action="finalize",
                response_parts=[self._reception_response(conversation, catalog)],
            )
            return updates

        if goals:
            if accepted_skill_gap:
                updates["response_parts"] = [
                    self._skill_gap_response(accepted_skill_gap)
                ]
            return self._route_goal_candidates(
                updates, conversation, message, goals, deterministic_goals
            )

        if accepted_skill_gap:
            return self._respond_to_skill_gap(
                updates, conversation, accepted_skill_gap
            )
        conversation["no_goal_turn_count"] = int(
            conversation.get("no_goal_turn_count", 0)
        ) + 1
        if conversation["no_goal_turn_count"] >= self.handoff_offer_turn_threshold:
            return self._offer_handoff(
                updates,
                conversation,
                reason="several turns did not produce a supported goal",
            )
        updates.update(
            next_action="finalize",
            response_parts=[
                self._unmatched_reception_response(conversation, message, catalog)
            ],
        )
        return updates

    def _record_skill_gap(
        self,
        updates: Dict[str, Any],
        state: WorkflowState,
        skill_gap: SkillGap,
        catalog: List[SkillRoutingDefinition],
        provider_metadata: Dict[str, Any],
    ) -> None:
        payload = {
            "category": skill_gap.category,
            "objective": skill_gap.objective,
            "confidence": skill_gap.confidence,
            "catalog_revision": self.catalog.revision,
            "available_skill_count": len(catalog),
            "provider": provider_metadata.get("provider"),
            "model": provider_metadata.get("model"),
        }
        updates["audit_events"] = state.get("audit_events", []) + [
            {"event_type": "skill_gap", "payload": payload}
        ]
        with self.observability.observe(
            "skill_gap.detected",
            "event",
            metadata=payload,
        ) as observation:
            observation.update(output={"recorded": True})

    @staticmethod
    def _skill_gap_response(skill_gap: SkillGap) -> str:
        return (
            "I understand that you'd like to {}. I'm sorry, but I don't currently have "
            "the ability to help with that."
        ).format(skill_gap.objective.rstrip("."))

    def _respond_to_skill_gap(
        self,
        updates: Dict[str, Any],
        conversation: ConversationState,
        skill_gap: SkillGap,
        continuation: Optional[str] = None,
    ) -> Dict[str, Any]:
        conversation["no_goal_turn_count"] = int(
            conversation.get("no_goal_turn_count", 0)
        ) + 1
        response_parts = [self._skill_gap_response(skill_gap)]
        if continuation:
            response_parts.append(continuation)
        if (
            skill_gap.category in IMMEDIATE_HANDOFF_SKILL_GAP_CATEGORIES
            or conversation["no_goal_turn_count"] >= self.handoff_offer_turn_threshold
        ):
            offer = self._new_handoff_offer(
                conversation,
                (
                    "member requested an unavailable fraud-reporting capability"
                    if skill_gap.category in IMMEDIATE_HANDOFF_SKILL_GAP_CATEGORIES
                    else "repeated requests need an unavailable capability"
                ),
            )
            conversation["pending_handoff_offer"] = offer
            response_parts.append(offer["question"])
        updates.update(
            goals=[], next_action="finalize", response_parts=response_parts
        )
        return updates

    def _plan_goals(self, state: WorkflowState) -> Dict[str, Any]:
        conversation = state["conversation"]
        goals = state.get("goals", [])
        routes = {skill.name: skill for skill in self.catalog.routes()}
        valid_goals = [goal for goal in goals if goal["skill_name"] in routes]
        if not valid_goals:
            return {
                "conversation": conversation,
                "response_parts": ["That capability is not currently available."],
                "next_action": "finalize",
            }

        current = conversation.get("active_task")
        if current:
            self._pause_current_work(conversation)
        conversation["awaiting_resume"] = False
        conversation["pending_clarification"] = None
        conversation["pending_goal_clarification"] = None
        conversation["pending_task_transition"] = None
        conversation["confirmation_status"] = "not_required"
        conversation["no_goal_turn_count"] = 0

        handoff_goal = next(
            (
                goal
                for goal in valid_goals
                if routes[goal["skill_name"]].risk_tier == "handoff"
            ),
            None,
        )
        if handoff_goal:
            valid_goals = [handoff_goal]
            active_context = current or (
                conversation["paused_tasks"][0] if conversation["paused_tasks"] else None
            )
            handoff_goal["context"] = {
                "prior_task": {
                    "goal": (
                        self._task_label(active_context)
                        if active_context
                        else "general assistance"
                    ),
                    "completed_steps": (
                        list(active_context.get("completed_steps", []))
                        if active_context
                        else []
                    ),
                }
            }

        valid_goals.sort(
            key=lambda goal: RISK_ORDER[routes[goal["skill_name"]].risk_tier]
        )
        tasks = []
        for goal in valid_goals:
            route = routes[goal["skill_name"]]
            definition = self.catalog.get(
                route.name, route.version, route.artifact_hash
            )
            if definition is not None:
                tasks.append(self._task_from_goal(goal, definition))
        if not tasks:
            return {
                "conversation": conversation,
                "response_parts": [
                    "That capability could not be loaded safely; no action was taken."
                ],
                "next_action": "finalize",
            }
        conversation["active_task"] = tasks[0]
        conversation["queued_tasks"] = tasks[1:]
        response_parts = list(state.get("response_parts", []))
        if len(tasks) > 1:
            first_label = self._goal_label(tasks[0]["skill_name"], tasks[0]["goal"])
            next_label = self._goal_label(tasks[1]["skill_name"], tasks[1]["goal"])
            response_parts.append(
                "I can help with both. I'll start by helping you {}, then continue "
                "by helping you {}.".format(
                    first_label, next_label
                )
            )
        return {
            "conversation": conversation,
            "response_parts": response_parts,
            "next_action": "policy",
        }

    def _supply_input(self, state: WorkflowState) -> Dict[str, Any]:
        conversation = state["conversation"]
        task = conversation.get("active_task")
        if not task:
            return {
                "conversation": conversation,
                "response_parts": ["There is no active task awaiting information."],
            }
        definition = self._task_definition(task)
        executor = self.executors.get(definition.archetype) if definition else None
        if not definition or not executor:
            task["status"] = "failed"
            return {
                "conversation": conversation,
                "response_parts": ["The paused capability is no longer available."],
            }
        inputs_before = dict(task.get("inputs", {}))
        if state.get("slot_correction"):
            # A correction invalidates prior derived variables and review state.
            # Re-run the pinned declarative workflow with the corrected inputs.
            task["workflow_step"] = 0
            task["variables"] = {}
            task["completed_steps"] = []
            task["missing_field"] = None
            task["pending_question"] = None
            task["outcome"] = None
            conversation["confirmation_status"] = "not_required"
        slot_updates = dict(state.get("slot_updates", {}))
        task.setdefault("inputs", {}).update(slot_updates)
        task["status"] = "ready"
        conversation["pending_clarification"] = None
        changed = {
            field_name
            for field_name, value in task.get("inputs", {}).items()
            if inputs_before.get(field_name) != value
        }
        declared_order = list(
            definition.input_schema.get("properties", {}).keys()
        )
        changed_fields = [
            field_name for field_name in declared_order if field_name in changed
        ]
        if changed_fields:
            task["updated_input_fields"] = changed_fields
        return {
            "conversation": conversation,
            "slot_attempted": True,
            "slot_inputs_before": inputs_before,
            "slot_update_fields": changed_fields,
            "slot_correction": bool(state.get("slot_correction")),
        }

    def _handle_confirmation(self, state: WorkflowState) -> Dict[str, Any]:
        conversation = state["conversation"]
        message = state["incoming_message"]
        task = conversation.get("active_task")
        if not task:
            return {
                "conversation": conversation,
                "response_parts": ["There is no action awaiting confirmation."],
                "next_action": "finalize",
            }
        if self._is_affirmative(message):
            conversation["confirmation_status"] = "confirmed"
            return {"conversation": conversation, "next_action": "policy"}
        if self._is_negative(message):
            task["status"] = "cancelled"
            conversation["confirmation_status"] = "declined"
            conversation["outcome"] = {"status": "cancelled"}
            return {
                "conversation": conversation,
                "response_parts": [
                    self._confirmation_copy(
                        task,
                        "decline_response",
                        "The reviewed action was cancelled; no action was taken.",
                    )
                ],
                "next_action": "advance",
                "audit_events": state.get("audit_events", [])
                + [
                    {
                        "event_type": "confirmation_declined",
                        "payload": {"skill": task["skill_name"], "task_id": task["id"]},
                    }
                ],
            }
        return {
            "conversation": conversation,
            "response_parts": [
                self._confirmation_copy(
                    task,
                    "retry_response",
                    "Please answer yes to continue or no to cancel.",
                )
            ],
            "next_action": "finalize",
        }

    def _handle_resume(self, state: WorkflowState) -> Dict[str, Any]:
        conversation = state["conversation"]
        paused = conversation["paused_tasks"]
        if not paused:
            conversation["awaiting_resume"] = False
            return {
                "conversation": conversation,
                "response_parts": ["There is no paused task to resume."],
            }
        if self._is_affirmative(state["incoming_message"], resume_words=True):
            task = paused.pop(0)
            task["status"] = task.pop("resume_status", "awaiting_input")
            conversation["active_task"] = task
            conversation["awaiting_resume"] = False
            conversation["selected_skill"] = task["skill_name"]
            conversation["outcome"] = task.get("outcome")
            question = task.get("pending_question")
            if task["status"] == "awaiting_input" and question:
                conversation["pending_clarification"] = {
                    "task_id": task["id"],
                    "field": task.get("missing_field") or "input",
                    "question": question,
                }
            elif task["status"] == "awaiting_confirmation":
                conversation["confirmation_status"] = "pending"
            return {
                "conversation": conversation,
                "response_parts": [
                    "Resuming your {} request. {}".format(
                        self._task_label(task), question or ""
                    )
                ],
            }

        discarded = paused.pop(0)
        conversation["awaiting_resume"] = bool(paused)
        conversation["outcome"] = {"status": "discarded", "task_id": discarded["id"]}
        suffix = (
            " Would you like to resume or discard your paused {} request?".format(
                self._task_label(paused[0])
            )
            if paused
            else ""
        )
        return {
            "conversation": conversation,
            "response_parts": [
                "I discarded the paused {} request.{}".format(
                    self._task_label(discarded), suffix
                )
            ],
        }

    def _check_policy(self, state: WorkflowState) -> Dict[str, Any]:
        conversation = state["conversation"]
        task = conversation.get("active_task")
        if not task:
            return {"conversation": conversation, "next_action": "finalize"}
        definition = self._task_definition(task)
        executor = self.executors.get(definition.archetype) if definition else None
        if not definition or not executor:
            task["status"] = "failed"
            conversation["outcome"] = {"status": "skill_unavailable"}
            return {
                "conversation": conversation,
                "response_parts": state.get("response_parts", [])
                + ["That skill is no longer available; no action was taken."],
                "next_action": "advance",
            }
        with self.observability.observe(
            "policy.evaluate",
            "guardrail",
            metadata={
                "skill": definition.name,
                "skill_version": definition.version,
                "skill_artifact_hash": definition.artifact_hash,
                "risk_tier": definition.risk_tier,
                "task_status": task["status"],
                "confirmation_status": conversation["confirmation_status"],
                "authentication_present": self.authenticated,
            },
        ) as policy_observation:
            decision = self.policy.evaluate(
                definition=definition,
                required_tools=executor.required_tools(definition),
                authenticated=self.authenticated,
                authorizations=self.authorizations,
                task_status=task["status"],
                confirmation_status=conversation["confirmation_status"],
                dependencies_available=all(
                    self.tools.supports(str(step["tool"]), str(step["action"]))
                    for step in definition.workflow.get("steps", [])
                    if step.get("op") == "call_tool"
                ),
            )
            policy_observation.update(
                output={"allowed": decision.allowed, "decision": decision.event}
            )
        audit_events = state.get("audit_events", []) + [
            {
                "event_type": decision.event,
                "payload": {
                    "skill": definition.name,
                    "skill_version": definition.version,
                    "skill_artifact_hash": definition.artifact_hash,
                    "risk_tier": definition.risk_tier,
                    "allowed": decision.allowed,
                },
            }
        ]
        if decision.allowed:
            return {
                "conversation": conversation,
                "next_action": "execute",
                "audit_events": audit_events,
            }
        if decision.event == "confirmation_denied":
            return {
                "conversation": conversation,
                "response_parts": state.get("response_parts", []) + [decision.reason],
                "next_action": "finalize",
                "audit_events": audit_events,
            }
        task["status"] = "failed"
        conversation["outcome"] = {"status": "policy_denied", "reason": decision.event}
        return {
            "conversation": conversation,
            "response_parts": state.get("response_parts", []) + [decision.reason],
            "next_action": "advance",
            "audit_events": audit_events,
        }

    def _execute_skill(self, state: WorkflowState) -> Dict[str, Any]:
        conversation = state["conversation"]
        task = conversation["active_task"]
        if task is None:
            return {"conversation": conversation}
        definition = self._task_definition(task)
        executor = self.executors.get(definition.archetype) if definition else None
        if not definition or not executor:
            task["status"] = "failed"
            conversation["outcome"] = {"status": "skill_unavailable"}
            return {
                "conversation": conversation,
                "response_parts": state.get("response_parts", [])
                + ["That skill became unavailable; no action was taken."],
            }
        conversation["selected_skill"] = definition.name
        completed_before = len(task.get("completed_steps", []))
        accepted_slot_fields: List[str] = []
        try:
            with self.observability.observe(
                "skill.{}".format(definition.name),
                "agent",
                metadata={
                    "skill": definition.name,
                    "skill_version": definition.version,
                    "skill_artifact_hash": definition.artifact_hash,
                    "archetype": definition.archetype,
                    "risk_tier": definition.risk_tier,
                    "goal": task["goal"],
                    "task_id": task["id"],
                },
            ) as skill_observation:
                result = executor.execute(task, self._skill_context(state, definition))
                inputs_before = state.get("slot_inputs_before", {})
                accepted_slot_fields = [
                    field_name
                    for field_name in state.get("slot_update_fields", [])
                    if field_name in result.inputs
                    and result.inputs.get(field_name) != inputs_before.get(field_name)
                ]
                skill_observation.update(
                    output={
                        "status": result.status,
                        "completed_step_count": len(result.completed_steps),
                        "slot_update_fields": state.get("slot_update_fields", []),
                        "accepted_slot_fields": accepted_slot_fields,
                    }
                )
        except Exception:
            task["status"] = "failed"
            conversation["outcome"] = {"status": "tool_error"}
            return {
                "conversation": conversation,
                "response_parts": state.get("response_parts", [])
                + [
                    "The mock integration could not complete that request. "
                    "No financial action was taken."
                ],
                "audit_events": state.get("audit_events", [])
                + [
                    {
                        "event_type": "tool_error",
                        "payload": {
                            "skill": definition.name,
                            "tools": list(executor.required_tools(definition)),
                        },
                    }
                ],
            }

        task["status"] = result.status
        task["inputs"] = result.inputs
        task["missing_field"] = result.missing_field
        task["pending_question"] = result.pending_question
        task["completed_steps"] = result.completed_steps
        task["outcome"] = result.outcome
        conversation["outcome"] = result.outcome
        if state.get("slot_attempted"):
            made_progress = bool(accepted_slot_fields) or (
                len(result.completed_steps) > completed_before
            )
            if result.status == "awaiting_input" and not made_progress:
                conversation["no_goal_turn_count"] = int(
                    conversation.get("no_goal_turn_count", 0)
                ) + 1
            else:
                conversation["no_goal_turn_count"] = 0
        if result.status == "awaiting_input":
            conversation["pending_clarification"] = {
                "task_id": task["id"],
                "field": result.missing_field or "input",
                "question": result.pending_question or result.response,
            }
            conversation["confirmation_status"] = "not_required"
        elif result.status == "awaiting_confirmation":
            conversation["pending_clarification"] = None
            conversation["confirmation_status"] = "pending"
        elif result.status == "completed":
            conversation["pending_clarification"] = None
            if definition.confirmation_required:
                conversation["confirmation_status"] = "consumed"
            if definition.risk_tier == "handoff":
                conversation["handoff_status"] = (result.outcome or {}).get("status")
        audit = {
            "event_type": "skill_result",
            "payload": {
                "skill": definition.name,
                "skill_version": definition.version,
                "skill_artifact_hash": definition.artifact_hash,
                "status": result.status,
                "tools": list(executor.required_tools(definition)),
            },
        }
        response = result.response
        if result.status == "awaiting_input" and accepted_slot_fields:
            labels = [field.replace("_", " ") for field in accepted_slot_fields]
            response = "Thanks, I have the {}. {}".format(
                " and ".join(labels), result.response
            )
        elif (
            result.status == "awaiting_confirmation"
            and state.get("slot_correction")
            and accepted_slot_fields
        ):
            labels = [field.replace("_", " ") for field in accepted_slot_fields]
            response = "I've updated the {}. {}".format(
                " and ".join(labels), result.response
            )
        response_parts = state.get("response_parts", []) + [response]
        if (
            result.status == "awaiting_input"
            and conversation.get("no_goal_turn_count", 0)
            >= self.handoff_offer_turn_threshold
            and not conversation.get("pending_handoff_offer")
        ):
            offer = self._new_handoff_offer(
                conversation, "several attempts did not provide the needed information"
            )
            conversation["pending_handoff_offer"] = offer
            response_parts.append(offer["question"])
        return {
            "conversation": conversation,
            "response_parts": response_parts,
            "audit_events": state.get("audit_events", []) + [audit],
        }

    def _advance(self, state: WorkflowState) -> Dict[str, Any]:
        conversation = state["conversation"]
        task = conversation.get("active_task")
        if task and task.get("status") in {"awaiting_input", "awaiting_confirmation"}:
            return {"conversation": conversation, "next_action": "finalize"}
        if task and task.get("status") not in {"completed", "failed", "cancelled"}:
            return {"conversation": conversation, "next_action": "finalize"}

        completed_was_handoff = False
        if task:
            definition = self._task_definition(task)
            completed_was_handoff = bool(definition and definition.risk_tier == "handoff")
            if definition and definition.risk_tier == "read_only":
                conversation["last_completed_skill"] = definition.name
            conversation["active_task"] = None

        if conversation["queued_tasks"]:
            # These tasks came from work the member already requested in the
            # same objective. Advancing them is not a new consent boundary;
            # each task still enforces its own policy and confirmation gates.
            next_task = conversation["queued_tasks"].pop(0)
            next_task["status"] = next_task.pop("resume_status", "ready")
            conversation["active_task"] = next_task
            conversation["selected_skill"] = next_task["skill_name"]
            conversation["outcome"] = None
            conversation["pending_task_transition"] = None
            conversation["confirmation_status"] = "not_required"
            return {
                "conversation": conversation,
                "response_parts": state.get("response_parts", []),
                "next_action": "policy",
            }

        response_parts = state.get("response_parts", [])
        if conversation["paused_tasks"] and not completed_was_handoff:
            conversation["awaiting_resume"] = True
            paused = conversation["paused_tasks"][0]
            response_parts = response_parts + [
                "Would you like to resume or discard your paused {} request?".format(
                    self._task_label(paused)
                )
            ]
        return {
            "conversation": conversation,
            "response_parts": response_parts,
            "next_action": "finalize",
        }

    def _finalize(self, state: WorkflowState) -> Dict[str, Any]:
        conversation = state["conversation"]
        parts = [part.strip() for part in state.get("response_parts", []) if part.strip()]
        reply = "\n\n".join(parts) if parts else "I wasn't able to produce a safe response."
        if not conversation.get("greeted"):
            preferred_name = conversation.get("member_profile", {}).get(
                "preferred_name", "Member"
            )
            greeting = "Hi {}.".format(preferred_name)
            if not reply.casefold().startswith(greeting.casefold()):
                reply = "{} {}".format(greeting, reply)
            conversation["greeted"] = True
        conversation["messages"].append({"role": "assistant", "content": reply})
        conversation["turn_count"] += 1
        return {"conversation": conversation, "reply": reply}

    def _skill_context(
        self, state: WorkflowState, definition: SkillDefinition
    ) -> SkillContext:
        return SkillContext(
            definition=definition,
            session_id=state["session_id"],
            member_ref="mock-member-001",
            authenticated=self.authenticated,
            authorizations=list(self.authorizations),
            confirmation_status=state["conversation"]["confirmation_status"],
            tools=self.tools,
            provider=self.provider,
            observability=self.observability,
            member_profile=dict(state["conversation"].get("member_profile", {})),
            execution_context=dict(
                (state["conversation"].get("active_task") or {}).get("context", {})
            ),
        )

    @staticmethod
    def _task_from_goal(goal: Dict[str, Any], definition: SkillDefinition) -> TaskState:
        return {
            "id": str(uuid.uuid4()),
            "skill_name": definition.name,
            "skill_version": definition.version,
            "skill_artifact_hash": definition.artifact_hash,
            "goal": goal["goal"],
            "status": "ready",
            "inputs": dict(goal.get("inputs", {})),
            "completed_steps": [],
            "missing_field": None,
            "pending_question": None,
            "outcome": None,
            "workflow_step": 0,
            "variables": {},
            "context": dict(goal.get("context", {})),
        }

    @staticmethod
    def _pause_current_work(conversation: ConversationState) -> None:
        active = conversation.get("active_task")
        if active:
            active["resume_status"] = active.get("status", "ready")
            active["status"] = "paused"
            conversation["paused_tasks"].append(active)
        for queued in conversation["queued_tasks"]:
            queued["resume_status"] = queued.get("status", "ready")
            queued["status"] = "paused"
            conversation["paused_tasks"].append(queued)
        conversation["active_task"] = None
        conversation["queued_tasks"] = []

    @staticmethod
    def _normalize_input_updates(
        updates: Dict[str, Any], route: SkillRoutingDefinition
    ) -> Dict[str, Any]:
        """Keep only values accepted by the skill's declared input schema."""

        properties = route.input_schema.get("properties", {})
        normalized: Dict[str, Any] = {}
        for field_name, value in updates.items():
            field = properties.get(field_name)
            if not isinstance(field, dict) or value is None or value == "":
                continue
            expected_type = field.get("type", "string")
            if expected_type == "string":
                if isinstance(value, (dict, list, tuple, set)):
                    continue
                text = " ".join(str(value).split())
                if not text:
                    continue
                candidate: Any = text[:500]
            elif expected_type == "array" and isinstance(value, list):
                candidate = value[:50]
            elif expected_type == "object" and isinstance(value, dict):
                candidate = dict(value)
            elif expected_type in {"number", "integer"} and isinstance(
                value, (int, float, str)
            ):
                try:
                    candidate = float(value)
                    if expected_type == "integer":
                        if not candidate.is_integer():
                            continue
                        candidate = int(candidate)
                except (TypeError, ValueError):
                    continue
            elif expected_type == "boolean" and isinstance(value, bool):
                candidate = value
            else:
                continue
            enum = field.get("enum")
            if isinstance(enum, list) and candidate not in enum:
                continue
            pattern = field.get("pattern")
            if isinstance(pattern, str) and isinstance(candidate, str):
                try:
                    if re.fullmatch(pattern, candidate) is None:
                        continue
                except re.error:
                    continue
            normalized[field_name] = candidate
        return normalized

    @classmethod
    def _normalize_slot_updates(
        cls,
        updates: List[SlotUpdate],
        route: SkillRoutingDefinition,
        *,
        pending_field: str = "",
        conversation_act: str = "unknown",
        current_inputs: Optional[Dict[str, Any]] = None,
        prior_member_messages: Optional[List[str]] = None,
    ) -> tuple:
        accepted: Dict[str, Any] = {}
        confidences: Dict[str, float] = {}
        existing = dict(current_inputs or {})
        prior_member_text = [
            " ".join(message.casefold().split())
            for message in (prior_member_messages or [])
        ]
        rejected = 0
        for update in updates:
            confidence = max(0.0, min(1.0, float(update.confidence)))
            binding = str(update.binding or "inferred").strip().casefold()
            if binding not in {
                "pending_answer",
                "explicit",
                "correction",
                "context_recovery",
            }:
                rejected += 1
                continue
            if binding == "pending_answer" and (
                not pending_field or str(update.field) != pending_field
            ):
                rejected += 1
                continue
            if binding == "correction" and conversation_act != "correction":
                rejected += 1
                continue
            if binding == "context_recovery":
                evidence = " ".join(str(update.evidence or "").casefold().split())
                if (
                    existing.get(str(update.field)) not in {None, ""}
                    or not evidence
                    or not any(evidence in message for message in prior_member_text)
                ):
                    rejected += 1
                    continue
            normalized = cls._normalize_input_updates(
                {str(update.field): update.value}, route
            )
            if confidence < SLOT_CONFIDENCE_THRESHOLD or not normalized:
                rejected += 1
                continue
            field_name, value = next(iter(normalized.items()))
            if confidence >= confidences.get(field_name, -1.0):
                accepted[field_name] = value
                confidences[field_name] = confidence
        return accepted, rejected

    @classmethod
    def _normalize_skill_matches(
        cls,
        matches: List[SkillMatch],
        catalog: List[SkillRoutingDefinition],
    ) -> tuple:
        """Constrain provider output to active skills and declared input schemas."""

        routes = {route.name: route for route in catalog}
        normalized: List[SkillMatch] = []
        rejected = 0
        for match in matches:
            route = routes.get(match.skill_name)
            if route is None:
                rejected += 1
                continue
            normalized.append(
                SkillMatch(
                    skill_name=match.skill_name,
                    confidence=max(0.0, min(1.0, float(match.confidence))),
                    inputs=cls._normalize_input_updates(dict(match.inputs), route),
                )
            )
        return normalized, 0, rejected

    @classmethod
    def _normalize_goal_dicts(
        cls,
        goals: List[Dict[str, Any]],
        catalog: List[SkillRoutingDefinition],
    ) -> tuple:
        matches = [
            SkillMatch(
                skill_name=str(goal.get("skill_name", "")),
                confidence=float(goal.get("confidence", 0.0)),
                inputs=dict(goal.get("inputs", {})),
            )
            for goal in goals
        ]
        normalized, canonicalized, rejected = cls._normalize_skill_matches(
            matches, catalog
        )
        merged = cls._merge_skill_matches(normalized, [])
        return (
            [{**match.as_dict(), "goal": match.skill_name} for match in merged],
            canonicalized,
            rejected,
        )

    @staticmethod
    def _merge_skill_matches(
        provider_matches: List[SkillMatch], deterministic_matches: List[SkillMatch]
    ) -> List[SkillMatch]:
        merged: Dict[str, SkillMatch] = {}
        for match in provider_matches + deterministic_matches:
            key = match.skill_name
            existing = merged.get(key)
            if existing is None:
                merged[key] = match
                continue
            merged[key] = SkillMatch(
                skill_name=match.skill_name,
                confidence=max(existing.confidence, match.confidence),
                # The semantic provider is first in the merge order. Let the
                # deterministic router supplement missing inputs, but never
                # overwrite the provider's field/value interpretation.
                inputs={**match.inputs, **existing.inputs},
            )
        return sorted(merged.values(), key=lambda item: item.confidence, reverse=True)

    def _route_goal_candidates(
        self,
        updates: Dict[str, Any],
        conversation: ConversationState,
        message: str,
        goals: List[Dict[str, Any]],
        deterministic_goals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        catalog = self.catalog.routes()
        goals = [goal for goal in goals if not self._is_handoff_goal(goal, catalog)]
        if not goals:
            updates.update(goals=[], next_action="finalize")
            return updates

        deterministic_keys = {
            (goal["skill_name"], goal["goal"])
            for goal in deterministic_goals
            if not self._is_handoff_goal(goal, catalog)
        }
        if self._is_explicit_multi_goal(message) and (
            len(deterministic_keys) > 1 or len(goals) > 1
        ):
            selected = (
                [
                    goal
                    for goal in goals
                    if (goal["skill_name"], goal["goal"]) in deterministic_keys
                ]
                if len(deterministic_keys) > 1
                else goals
            )
            conversation["pending_goal_clarification"] = None
            conversation["no_goal_turn_count"] = 0
            updates.update(goals=selected, next_action="plan")
            return updates

        ranked = sorted(goals, key=lambda goal: float(goal.get("confidence", 0)), reverse=True)
        if len(ranked) == 1 or (
            float(ranked[0].get("confidence", 0))
            - float(ranked[1].get("confidence", 0))
            >= GOAL_AMBIGUITY_MARGIN
        ):
            conversation["pending_goal_clarification"] = None
            conversation["no_goal_turn_count"] = 0
            updates.update(goals=[ranked[0]], next_action="plan")
            return updates

        candidates = ranked[:2]
        labels = [
            self._goal_label(candidate["skill_name"], candidate["goal"])
            for candidate in candidates
        ]
        question = "Did you want to {} or {}?".format(labels[0], labels[1])
        conversation["pending_goal_clarification"] = {
            "candidates": candidates,
            "question": question,
        }
        updates.update(goals=[], next_action="finalize", response_parts=[question])
        return updates

    @staticmethod
    def _resolve_pending_goal_clarification(
        message: str,
        goals: List[Dict[str, Any]],
        deterministic_goals: List[Dict[str, Any]],
        pending: Dict[str, Any],
    ) -> Optional[List[Dict[str, Any]]]:
        candidates = list(pending.get("candidates", []))
        candidate_keys = {
            (candidate["skill_name"], candidate["goal"]): candidate
            for candidate in candidates
        }
        normalized = " ".join(re.findall(r"[a-z0-9]+", message.casefold()))
        if normalized in {"yes", "yeah", "yep", "correct", "please do"} and len(
            candidates
        ) == 1:
            return [candidates[0]]
        if normalized in {"both", "both please", "all of them"} and len(candidates) > 1:
            return candidates
        if normalized in {"first", "first one", "option one", "one"} and candidates:
            return [candidates[0]]
        if normalized in {"second", "second one", "option two", "two"} and len(candidates) > 1:
            return [candidates[1]]

        matching = []
        for goal in goals + deterministic_goals:
            key = (goal["skill_name"], goal["goal"])
            if key in candidate_keys and key not in {
                (item["skill_name"], item["goal"]) for item in matching
            }:
                matching.append(goal)
        if len(matching) == 1:
            return matching
        if len(matching) > 1 and AgentRuntime._is_explicit_multi_goal(message):
            return matching

        message_tokens = set(normalized.split())
        lexical = []
        for candidate in candidates:
            candidate_tokens = set(
                re.findall(
                    r"[a-z0-9]+",
                    "{} {}".format(
                        candidate["skill_name"], candidate["goal"]
                    ).casefold(),
                )
            )
            if message_tokens.intersection(candidate_tokens):
                lexical.append(candidate)
        if len(lexical) == 1:
            return lexical

        unrelated = [
            goal
            for goal in goals
            if (goal["skill_name"], goal["goal"]) not in candidate_keys
        ]
        return unrelated or None

    def _has_explicit_new_goal(
        self,
        active: TaskState,
        message: str,
        goals: List[Dict[str, Any]],
        deterministic_goals: List[Dict[str, Any]],
    ) -> bool:
        different_deterministic = [
            goal
            for goal in deterministic_goals
            if goal["skill_name"] != active.get("skill_name")
        ]
        if different_deterministic:
            return True
        different = sorted(
            [goal for goal in goals if goal["skill_name"] != active.get("skill_name")],
            key=lambda goal: float(goal.get("confidence", 0)),
            reverse=True,
        )
        if not different:
            return False
        normalized = message.casefold()
        if any(
            marker in normalized
            for marker in ("instead", "actually", "new question", "forget that", "stop that")
        ):
            return True
        top = float(different[0].get("confidence", 0))
        runner_up = float(different[1].get("confidence", 0)) if len(different) > 1 else 0.0
        request_cue = re.search(
            r"\b(i need|i want|can you|could you|how|what|forgot|help me)\b", normalized
        )
        return bool(request_cue and top >= 0.85 and top - runner_up >= 0.2)

    def _offer_handoff(
        self,
        updates: Dict[str, Any],
        conversation: ConversationState,
        reason: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        offer = self._new_handoff_offer(conversation, reason, inputs)
        conversation["pending_handoff_offer"] = offer
        updates.update(
            goals=[],
            next_action="finalize",
            response_parts=[offer["question"]],
        )
        return updates

    def _new_handoff_offer(
        self,
        conversation: ConversationState,
        reason: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        active = conversation.get("active_task")
        if not active and conversation.get("paused_tasks"):
            active = conversation["paused_tasks"][0]
        question = (
            "I understand you'd like to talk with a live agent. Would you like me to "
            "connect you now? Please answer yes or no."
            if reason == "member explicitly requested a live agent"
            else (
                "It looks like you may benefit from additional help. Would you like me to "
                "connect you with a live agent? Please answer yes or no."
            )
        )
        return {
            "reason": reason,
            "active_goal": self._task_label(active) if active else "general assistance",
            "completed_steps": list(active.get("completed_steps", [])) if active else [],
            "inputs": dict(inputs or {}),
            "question": question,
        }

    @staticmethod
    def _handoff_goal(
        catalog: List[SkillRoutingDefinition], offer: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        definition = next((item for item in catalog if item.risk_tier == "handoff"), None)
        if not definition:
            return None
        return {
            "skill_name": definition.name,
            "goal": definition.name,
            "confidence": 1.0,
            "inputs": dict(offer.get("inputs", {})),
            "context": {
                "prior_task": {
                    "goal": offer["active_goal"],
                    "completed_steps": list(offer.get("completed_steps", [])),
                }
            },
        }

    @staticmethod
    def _is_handoff_goal(
        goal: Dict[str, Any], catalog: List[SkillRoutingDefinition]
    ) -> bool:
        definition = next(
            (item for item in catalog if item.name == goal.get("skill_name")), None
        )
        return bool(definition and definition.risk_tier == "handoff")

    def _ensure_member_profile(self, conversation: ConversationState) -> None:
        if conversation.get("member_profile"):
            return
        with self.observability.observe(
            "tool.mock_member_profile.get",
            "tool",
            input_value={"member_ref": "redacted"},
            metadata={"tool": "mock_member_profile", "action": "get"},
        ) as observation:
            try:
                profile = self.tools.invoke(
                    "mock_member_profile", "get", {"member_ref": "mock-member-001"}
                )
                observation.update(
                    output={"profile_loaded": True}, metadata={"tool_status": "success"}
                )
            except Exception:
                profile = {
                    "member_ref": "mock-member-001",
                    "first_name": "Member",
                    "preferred_name": "Member",
                }
                observation.update(
                    output={"profile_loaded": False}, status="error"
                )
        conversation["member_profile"] = profile

    def _reception_response(
        self,
        conversation: ConversationState,
        catalog: List[SkillRoutingDefinition],
    ) -> str:
        name = conversation.get("member_profile", {}).get("preferred_name", "Member")
        capabilities = self._member_capability_list(catalog)
        if not capabilities:
            return (
                "Hi {}. I'm glad you reached out. Tell me what you need help with, and I'll "
                "do my best to point you in the right direction."
            ).format(name)
        templates = (
            "I'm glad you reached out. I can currently help you {capabilities}. "
            "What can I help you with today?",
            "I can help you {capabilities}. What would you like to take care of today?",
            "You can ask me to {capabilities}. Where would you like to begin?",
        )
        variant = conversation.get("reception_variant")
        if not isinstance(variant, int) or not 0 <= variant < len(templates):
            variant = uuid.uuid4().int % len(templates)
        # Cycle controlled templates so capability questions do not get the same
        # canned reply throughout a session. The wording remains catalog-derived.
        conversation["reception_variant"] = (variant + 1) % len(templates)
        opening = "Hi {}. ".format(name) if not conversation.get("greeted") else ""
        conversation["greeted"] = True
        return opening + templates[variant].format(
            capabilities=self._join_choices(capabilities)
        )

    def _unmatched_reception_response(
        self,
        conversation: ConversationState,
        message: str,
        catalog: List[SkillRoutingDefinition],
    ) -> str:
        name = conversation.get("member_profile", {}).get("preferred_name", "Member")
        capabilities = self._member_capability_list(catalog)
        capability_text = self._join_choices(capabilities)
        is_first_response = not conversation.get("greeted", False)
        greeting = "Hi {member_name}. " if is_first_response else ""
        if capabilities:
            fallback = (
                greeting
                + "Thanks for explaining. I want to make sure I point you in "
                "the right direction. I can currently help you {capability_text}. Could you "
                "tell me a little more about what you need?"
            )
        else:
            fallback = (
                greeting
                + "Thanks for explaining. I want to make sure I understand. "
                "Could you tell me a little more about what you need?"
            )
        facts = {
            "member_name": name,
            "member_message": message,
            "available_services": capabilities,
            "capability_text": capability_text,
            "is_first_response": is_first_response,
            "template": fallback,
        }
        # This lane-setting response is deliberately rendered from controlled
        # copy.  The model may understand a turn and select an approved skill,
        # but it is never asked to answer an unsupported financial question from
        # its training data.
        with self.observability.observe(
            "response.controlled_reception",
            "chain",
            input_value={
                "available_service_count": len(capabilities),
                "content_redacted": True,
            },
            metadata={"model_used": False, "controlled_copy": True},
        ) as observation:
            response = fallback.format(**facts)
            observation.update(output={"response_length": len(response)})
        if is_first_response:
            normalized = response.casefold().lstrip()
            if not normalized.startswith(
                ("hi {}".format(name.casefold()), "hello {}".format(name.casefold()))
            ):
                response = "Hi {}. {}".format(name, response)
            conversation["greeted"] = True
        return response

    def _member_capability_list(
        self, catalog: List[SkillRoutingDefinition]
    ) -> List[str]:
        labels: List[str] = []
        for skill in catalog:
            # Handoff remains discoverable through an explicit request, frustration, or the
            # turn threshold; it is not proactively advertised by the receptionist.
            if skill.risk_tier == "handoff":
                continue
            if skill.display_name not in labels:
                labels.append(skill.display_name)
        return labels

    @staticmethod
    def _join_choices(values: List[str]) -> str:
        if not values:
            return ""
        if len(values) == 1:
            return values[0]
        if len(values) == 2:
            return "{} or {}".format(values[0], values[1])
        return "{}, or {}".format(", ".join(values[:-1]), values[-1])

    @staticmethod
    def _is_greeting_or_capability_question(message: str) -> bool:
        normalized = " ".join(re.findall(r"[a-z]+", message.casefold()))
        greeting = normalized in {
            "hi",
            "hello",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
        }
        capability_phrase = any(
            phrase in normalized
            for phrase in ("what can you do", "how can you help", "what are your skills")
        )
        # Accept conversational word-order variants such as "what can else you
        # do?" as a request for the installed capability list, not as an
        # unrecognized banking request.
        words = set(normalized.split())
        capability_variant = bool(
            # Natural wording may place "else" before "you can" (for example,
            # "what else you can do?"). The intent is still unambiguous.
            "what" in words
            and "do" in words
            and ({"you", "u"} & words)
            and ({"can", "else"} & words)
        ) or "what other services" in normalized
        return greeting or capability_phrase or capability_variant

    @staticmethod
    def _is_frustrated(message: str) -> bool:
        normalized = message.casefold()
        return any(
            phrase in normalized
            for phrase in (
                "not helping",
                "this is useless",
                "so frustrated",
                "i am frustrated",
                "terrible service",
            )
        )

    @staticmethod
    def _apply_sentiment(
        conversation: ConversationState, sentiment: str, confidence: float
    ) -> None:
        normalized = sentiment if sentiment in {
            "positive",
            "neutral",
            "negative",
            "frustrated",
            "unknown",
        } else "unknown"
        conversation["sentiment"] = normalized
        conversation["sentiment_confidence"] = max(
            0.0, min(1.0, float(confidence))
        )
        if normalized == "frustrated":
            conversation["negative_sentiment_streak"] = max(
                2, int(conversation.get("negative_sentiment_streak", 0)) + 1
            )
        elif normalized == "negative":
            conversation["negative_sentiment_streak"] = int(
                conversation.get("negative_sentiment_streak", 0)
            ) + 1
        elif normalized in {"positive", "neutral"}:
            conversation["negative_sentiment_streak"] = 0

    @staticmethod
    def _is_explicit_multi_goal(message: str) -> bool:
        return bool(
            re.search(r"\b(and|also|then|as well as|but|both)\b", message.casefold())
        )

    def _goal_label(self, skill_name: str, goal_name: str) -> str:
        definition = next(
            (route for route in self.catalog.routes() if route.name == skill_name), None
        )
        if definition:
            return definition.display_name
        return goal_name.replace("_", " ")

    def _new_task_transition(self, task: TaskState) -> Dict[str, str]:
        label = self._task_label(task)
        return {
            "task_id": task["id"],
            "goal_label": label,
            "question": (
                "That request is complete. Would you like me to continue and {}?"
            ).format(label),
        }

    def _task_label(self, task: TaskState) -> str:
        definition = self._task_definition(task)
        if definition is not None:
            return definition.display_name
        return self._goal_label(task["skill_name"], task["goal"])

    def _confirmation_copy(self, task: TaskState, key: str, default: str) -> str:
        definition = self._task_definition(task)
        if not definition:
            return default
        step_index = int(task.get("workflow_step", 0))
        steps = definition.workflow.get("steps", [])
        if step_index < len(steps) and steps[step_index].get("op") == "confirm":
            return str(steps[step_index].get(key, default))
        return default

    def _task_definition(self, task: TaskState) -> Optional[SkillDefinition]:
        """Resolve the immutable artifact originally selected for a durable task.

        Every task stores the version and content hash. Missing identity fails
        closed; the runtime never substitutes whatever version happens to be active.
        """

        name = task["skill_name"]
        version = task.get("skill_version")
        artifact_hash = task.get("skill_artifact_hash")
        if version and artifact_hash:
            return self.catalog.get(name, version, artifact_hash)
        return None

    @staticmethod
    def _is_affirmative(message: str, resume_words: bool = False) -> bool:
        normalized = re.sub(r"[^a-z ]", "", message.lower()).strip()
        words = {
            "yes",
            "yes please",
            "y",
            "confirm",
            "approve",
            "proceed",
            "do it",
        }
        if resume_words:
            words.update({"resume", "continue", "pick it back up"})
        return normalized in words

    @staticmethod
    def _is_negative(message: str) -> bool:
        normalized = re.sub(r"[^a-z ]", "", message.lower()).strip()
        return normalized in {"no", "n", "cancel", "decline", "stop", "discard"}

    @classmethod
    def _is_yes_or_no(cls, message: str) -> bool:
        return cls._is_affirmative(message) or cls._is_negative(message)

    @classmethod
    def _is_resume_or_discard(cls, message: str) -> bool:
        return cls._is_affirmative(message, resume_words=True) or cls._is_negative(message)
