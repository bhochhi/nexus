"""Provider-neutral and graph-state contracts used across the application."""

from typing import Any, Dict, List, Optional, TypedDict


class Message(TypedDict):
    role: str
    content: str


class PendingClarification(TypedDict):
    task_id: str
    field: str
    question: str


class PendingGoalClarification(TypedDict):
    candidates: List[Dict[str, Any]]
    question: str


class PendingHandoffOffer(TypedDict):
    reason: str
    active_goal: str
    completed_steps: List[str]
    inputs: Dict[str, Any]
    question: str


class PendingTaskTransition(TypedDict):
    task_id: str
    goal_label: str
    question: str


class TaskState(TypedDict, total=False):
    id: str
    skill_name: str
    goal: str
    status: str
    resume_status: str
    inputs: Dict[str, Any]
    completed_steps: List[str]
    missing_field: Optional[str]
    pending_question: Optional[str]
    outcome: Optional[Dict[str, Any]]
    skill_version: str
    skill_artifact_hash: str
    workflow_step: int
    variables: Dict[str, Any]


class ConversationState(TypedDict):
    messages: List[Message]
    active_task: Optional[TaskState]
    queued_tasks: List[TaskState]
    paused_tasks: List[TaskState]
    pending_clarification: Optional[PendingClarification]
    pending_goal_clarification: Optional[PendingGoalClarification]
    pending_handoff_offer: Optional[PendingHandoffOffer]
    pending_task_transition: Optional[PendingTaskTransition]
    member_profile: Dict[str, Any]
    greeted: bool
    no_goal_turn_count: int
    selected_skill: Optional[str]
    last_completed_skill: Optional[str]
    confirmation_status: str
    outcome: Optional[Dict[str, Any]]
    awaiting_resume: bool
    handoff_status: Optional[str]
    sentiment: str
    sentiment_confidence: float
    negative_sentiment_streak: int
    turn_count: int


class WorkflowState(TypedDict, total=False):
    session_id: str
    conversation: ConversationState
    incoming_message: str
    goals: List[Dict[str, Any]]
    next_action: str
    response_parts: List[str]
    reply: str
    audit_events: List[Dict[str, Any]]
    catalog_revision: int
    slot_updates: Dict[str, Any]
    conversation_act: str
    active_goal_relation: str
    slot_attempted: bool
    slot_inputs_before: Dict[str, Any]
    slot_update_fields: List[str]
    slot_correction: bool


def new_conversation_state() -> ConversationState:
    return {
        "messages": [],
        "active_task": None,
        "queued_tasks": [],
        "paused_tasks": [],
        "pending_clarification": None,
        "pending_goal_clarification": None,
        "pending_handoff_offer": None,
        "pending_task_transition": None,
        "member_profile": {},
        "greeted": False,
        "no_goal_turn_count": 0,
        "selected_skill": None,
        "last_completed_skill": None,
        "confirmation_status": "not_required",
        "outcome": None,
        "awaiting_resume": False,
        "handoff_status": None,
        "sentiment": "unknown",
        "sentiment_confidence": 0.0,
        "negative_sentiment_streak": 0,
        "turn_count": 0,
    }
