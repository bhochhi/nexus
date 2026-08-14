# Codex / AI Coding Agent Project Instructions

You are the principal engineer implementing the **Agentic Conversational Platform** described in `Architecture.md`.

## Mandatory first step

Read `Architecture.md` completely before creating or modifying application code. Treat it as the source of truth.

## Mission

Build a modular, reusable, spec-driven banking/insurance conversational platform with:

- OpenAI GPT models for natural-language understanding and per-turn orchestration decisions;
- LangGraph as the durable workflow/orchestration runtime;
- a Session Manager for conversation-level state;
- a Job Manager for member-objective/work lifecycle;
- a dynamic Skill Registry and generic Skill Runtime;
- typed Tool Registry/Executor adapters;
- deterministic/policy-controlled execution for consequential actions;
- a separate Response Composer;
- first-class live-agent handoff;
- FastAPI HTTP + WebSocket server supporting both member and live-agent clients;
- automated unit, contract, conversation, integration, and E2E tests.

## Core architecture rules

1. **Do not build a traditional intent-classifier-first architecture.**
2. The member has an **objective**. The platform owns **jobs** that track work toward that objective. Do not describe the LLM as having business goals.
3. The OpenAI model makes a **structured ConversationDecision** each turn. Use a Pydantic/JSON Schema contract; never use free-form text as control flow.
4. The LLM may understand, extract facts, select candidate skills, recommend the next action, and generate constrained language.
5. The LLM must never directly execute money movement or other consequential side effects.
6. All side-effecting actions go through deterministic policy validation, required confirmation, typed tool execution, idempotency, and audit logging.
7. The orchestrator must remain generic. Never add business branching such as `if skill_id == "money_transfer"` to central orchestration code.
8. Skills are declarative, versioned specifications dynamically loaded through the Skill Registry.
9. A new skill using existing tools/workflow primitives must be addable without changing orchestrator code.
10. If a skill requires a new downstream capability, implement a new typed tool adapter rather than putting integration logic into the skill or prompt.
11. Persist structured session/job state. Chat history alone is not state.
12. Use LangGraph checkpointing/interrupts for resumable workflows and confirmation/human-input boundaries.
13. Live-agent handoff is a required platform feature, not an afterthought.
14. Keep response wording/style separate from workflow/business logic.
15. Do not hard-code the OpenAI model name. Read `OPENAI_MODEL`, `OPENAI_DECISION_MODEL`, and `OPENAI_RESPONSE_MODEL` from configuration.
16. Read `OPENAI_API_KEY` from the environment only. Never log it or commit `.env`.

## Technology direction

Use a modern Python project with:

- Python 3.12+ unless local constraints require otherwise;
- FastAPI;
- Pydantic v2;
- LangGraph;
- official OpenAI Python SDK;
- YAML skill specifications;
- pytest;
- async I/O for model/network/WebSocket paths;
- PostgreSQL-ready repository interfaces, with in-memory implementations first;
- Redis only as an optional distributed presence/pub-sub layer, never the sole durable business record.

Use current stable APIs supported by the installed dependency versions. Do not copy obsolete examples.

## OpenAI integration

Prefer the current OpenAI Responses API for new model calls unless an explicit project constraint requires otherwise.

The decision call must produce a strict typed structure similar to:

```python
class ConversationDecision(BaseModel):
    decision: DecisionType
    member_objective_summary: str | None = None
    target_job_id: str | None = None
    candidate_skill_id: str | None = None
    fact_updates: dict[str, Any] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    side_question: bool = False
    requires_confirmation: bool = False
    handoff_reason: str | None = None
    response_directive: str | None = None
    confidence: float = Field(ge=0, le=1)
```

Decision enum:

```text
ANSWER_DIRECT
ASK_CLARIFYING
START_JOB
CONTINUE_JOB
SUSPEND_AND_START
RESUME_JOB
CANCEL_JOB
REPLACE_JOB
REQUEST_CONFIRMATION
HANDOFF_LIVE_AGENT
COMPLETE_JOB
DECLINE_OR_BLOCK
```

Validate all model output before application state changes.

## Initial vertical slices

Implement in this order:

### Slice 1 — Skeleton
- project/package structure;
- settings and `.env.example`;
- FastAPI app + health endpoint;
- typed domain models;
- repository interfaces + in-memory implementations;
- Skill Registry/loader;
- OpenAI client abstraction;
- LangGraph skeleton;
- test harness.

### Slice 2 — Account Balance
Load `skills/account_balance/skill.yaml` dynamically and fulfill through a fake `get_account_balance` tool. Support natural clarification when more than one account matches.

### Slice 3 — FAQ
Load `skills/faq/skill.yaml`. Use an approved fake knowledge adapter and grounded response composition.

### Slice 4 — Money Transfer
Load `skills/money_transfer/skill.yaml`. Collect facts naturally, validate deterministically, require explicit confirmation via LangGraph interrupt, and execute through an idempotent fake tool.

### Slice 5 — Interruption / resume
During an in-progress transfer, support a balance side question, preserve transfer facts, answer balance, then resume the transfer.

### Slice 6 — Live agent
Implement WebSockets for member and live-agent clients. The member can request a person at any point. Persist the active job, create a handoff context summary, transition to agent-active mode, and relay messages.

## WebSocket protocol

Start with:

```text
/ws/member/{session_id}
/ws/agent/{session_id}
```

All frames use a typed event envelope:

```json
{
  "event_id": "evt_123",
  "session_id": "session_123",
  "type": "message.created",
  "actor": "member",
  "timestamp": "2026-08-06T12:00:00Z",
  "payload": {}
}
```

Implement events from `Architecture.md` and keep the WebSocket hub transport-focused. It must not decide business workflows.

## Skill contract

Each skill must at minimum define:

- id/version/domain/name/description;
- representative natural-language examples;
- required/optional facts;
- fact validation;
- allowed tools;
- workflow mode and steps;
- policy/confirmation requirements;
- completion criteria;
- response constraints;
- test cases.

Validate every skill at startup. Unknown tools or invalid workflows fail fast.

## Testing expectations

For each slice add:

- unit tests;
- skill contract tests;
- multi-turn conversation tests;
- negative/policy tests;
- fake tool failure tests;
- WebSocket tests when relevant.

Minimum critical scenarios:

1. balance request with one account;
2. balance request requiring account clarification;
3. transfer with all facts in one utterance;
4. transfer with facts supplied over several turns;
5. correction of amount/account mid-conversation;
6. balance side question during transfer, followed by resume;
7. transfer cancellation;
8. explicit confirmation required before execution;
9. duplicate/retry does not duplicate transfer;
10. live-agent request at the beginning, middle, and failure state;
11. live-agent connection/disconnection/reconnection;
12. model emits invalid decision → application rejects safely.

## Working style

- Keep the repository runnable after every implementation step.
- Prefer small modules and explicit interfaces.
- Do not introduce abstractions that are not serving a documented requirement.
- When you make a significant architecture choice, create/update an ADR under `docs/adr/`.
- Update `Architecture.md` when the implemented contract intentionally changes.
- At the end of each coding task, report files changed, tests added, and architecture decisions made.

## First task

Create the project skeleton from `Architecture.md`, then implement **Slice 1 only**. Do not jump directly to all use cases. Run the tests and make the skeleton clean before implementing Slice 2.


Based on our altimate desire to build the architecture for Agentic Conversatonal Platform for USAA following spec-driven development. we need to built two design document at least 2 design diagrams: development workflow, and runtime application. development workflow should show agentic workflow where user interact with copilot agent to build the specs, then implement (after specs are approved) and then validate(pass means ready to ship/publish). And our runtime application mean the platform that our  built time copilot agent has built the chat bot app. we need to build the architecture diagram for this chat app we call it agentic chatbot. we have experimented with various ways.. creating multiple agents, creating one agent with multiple skills. what we stood up lately for our runtime chatbot app is one Agent we call is orchrestrator Agent, which will use LangGraph. it will able to management session using its session manager, it will have skills manager which will help to register new skill and discover new skills and load skills as needed to complete the goal. And we will ahve goal/plan manager which will help to create th plan with one or more goals based on user/member's utterances/objective understood. we will be leveraging Amazon Bedrock to integrate with LLM needed. We will also need GuardRails which will plan to integrate with Amazon Bedrock. what else? we will will also need observability telemery need to know standard metrics and logs so we know what is happening in the system. 
Your first goal is to come up with diagram. previous we built that arch png diagram 7 layered. refer to that ver5 folder /Users/bhochhi/projects/arch/ver5/diagrams/architecture-overview.png  I like that... then we can use mermaid or something easy for me to edit as neeeded. Please also reference to /Users/bhochhi/projects/agentic-chat-platform-blueprint/Architecture.md (not complete but close to what we am mentioning above)
you goal is to create this two or more diagrams that is easy to understand for business about out strategic platform. 
