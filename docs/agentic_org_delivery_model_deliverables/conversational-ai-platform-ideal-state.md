# Enterprise Conversational AI Platform

## Ideal-State Platform and Capabilities Architecture

**Status:** Target architecture  
**Audience:** Business sponsors, product leaders, architecture, engineering, risk, security, operations, and AI quality teams  
**Purpose:** Define the durable operating and technical model for a goal-driven conversational AI platform that can safely host many independently governed business capabilities.

---

## Executive summary

The target is not a collection of independent bots. It is one enterprise conversational platform that maintains conversation state, recognizes and manages user goals, selects and loads business capabilities, controls tool execution, composes governed responses, and produces the evidence needed to operate safely.

The model may interpret, recommend, plan, and draft. The platform owns state, authorization, policy decisions, execution, validation, audit, and release controls. In short:

> **The model advises. The platform decides and executes.**

Business behavior is delivered as modular capabilities. A lightweight catalog exposes metadata for discovery; the runtime loads the full capability package only after selection. This preserves a coherent conversational experience while allowing capability teams to release business functionality without rebuilding the core runtime.

The architecture separates two systems that use agentic techniques for different purposes:

1. The **development-time agentic workflow** helps teams move from business intent to specifications, plans, implementation, independent verification, evidence, and promotion.
2. The **runtime agentic conversational platform** serves users, manages goals and state, selects capabilities, invokes tools through policy-controlled boundaries, and composes responses.

The initial inference implementation is OpenAI-first. A provider abstraction keeps model calls, structured output, streaming, retries, usage, and provider-specific optimizations behind a stable interface so another inference provider can be introduced without redesigning the platform. OpenTelemetry is the telemetry standard; Langfuse is the default LLM trace and evaluation experience.

## 1. Outcomes and non-goals

### 1.1 Target outcomes

- One consistent conversational surface across many business domains.
- Goal-driven, multi-turn interactions that can clarify, correct, pause, resume, and hand off.
- Business capabilities that are discoverable, versioned, testable, governed, and independently promotable.
- Deterministic control over consequential actions even when an LLM participates in understanding or planning.
- Portable inference integration with an OpenAI-first reference implementation.
- Continuous evidence through tests, evaluations, policy checks, traces, metrics, and audit events.
- A development system that makes the safe path the fast path for capability teams.

### 1.2 Non-goals

- A fully autonomous model with unrestricted tool access.
- A separate production agent, orchestration stack, or policy implementation for every capability.
- Storing the entire transcript in every model prompt by default.
- Encoding business policy only in prompts or relying on provider guardrails as the complete governance system.
- Treating a capability catalog as a marketplace or no-code authoring portal in the initial platform.

## 2. Architecture principles

1. **Goal-driven, not intent-only.** Persist what the user is trying to accomplish, its status, required facts, current step, and outcome.
2. **State belongs to the platform.** Models are stateless; the platform persists structured state and sends the minimum useful context for each decision.
3. **Model advises; platform decides.** Model output is a proposal that must satisfy contracts, authorization, policy, and state-transition rules.
4. **Capabilities are modular business behavior.** The runtime is shared; capabilities declare what they do, what they require, and which controls apply.
5. **Metadata first, details on demand.** Use catalog metadata for selection and dynamically load the complete capability only when relevant.
6. **Deterministic where consequences increase.** Move from conversational flexibility to guided and deterministic execution as risk rises.
7. **Contracts before coupling.** Runtime, capability, tool, event, state, and response boundaries are versioned specifications.
8. **Governance is enforceable.** Important policies have a machine-readable form, an owner, and at least one enforcement point.
9. **Evaluation is a release discipline.** AI behavior is evaluated continuously, not deferred to manual QA.
10. **Observability is part of correctness.** Every turn and consequential action is traceable without exposing protected data.
11. **OpenAI-first, provider-agnostic.** Optimize the first implementation without leaking provider semantics into domain code.
12. **Design for scale; activate complexity only when evidence requires it.**

## 3. The two agentic systems

### 3.1 Development-time agentic workflow

This system operates on the repository and delivery lifecycle. It is not deployed into the customer conversation path.

```text
Business intent
    -> impact analysis
    -> feature specification and contracts
    -> implementation plan
    -> implementation
    -> independent verification
    -> evaluations and release evidence
    -> governed promotion
```

Its inputs are specifications, ADRs, governance policies, code, tests, evaluation scenarios, and prior release evidence. Its outputs are reviewable artifacts and changes. Humans retain approval authority for material business, architecture, risk, and production decisions.

### 3.2 Runtime agentic conversational platform

This system operates during live interactions.

```text
Channel -> API -> session/state -> understand latest turn
        -> goal manager -> capability selection/loading
        -> policy decision -> orchestration/execution
        -> response composer -> output guardrails -> channel
```

It may use model reasoning at bounded decision points, but platform code controls every state transition and external side effect.

### 3.3 Why the separation matters

The two systems can share contracts, policies, evaluation assets, and observability conventions, but they have different identities, permissions, threat models, release cadences, and failure modes. A development agent can propose code; a runtime orchestrator can propose a tool action. Neither proposal is authority to merge, deploy, or execute a consequential action.

## 4. Logical platform architecture

```text
Users and channels
        |
Channel adapters / API / identity context
        |
Conversation runtime (LangGraph)
  +-- session and structured conversation state
  +-- goal manager and interruption/resume
  +-- understanding and decision nodes
  +-- capability registry, resolver, loader
  +-- execution-mode controller
  +-- policy decision and enforcement
  +-- tool gateway and integration adapters
  +-- response composer and response contracts
  +-- input/output guardrails
        |
Enterprise APIs, data, events, and human handoff

Cross-cutting: provider abstraction | OpenTelemetry | Langfuse | audit | security
```

### 4.1 Channel and API layer

Normalizes web, mobile, voice, messaging, and internal channel requests into a common turn contract. It establishes correlation identifiers, authenticated subject context, locale, channel capabilities, and streaming preferences. Channel-specific rendering remains outside business capability logic.

### 4.2 Session and conversation state

The state store maintains the authoritative, versioned representation of the conversation. Raw transcripts remain available according to retention policy for audit and analysis, but they are not the primary memory mechanism.

Minimum state domains include:

- session, actor, authentication strength, locale, channel, and correlation data;
- active, paused, completed, abandoned, and failed goals;
- facts/entities with provenance, confidence, sensitivity, and validation status;
- selected capability and version;
- execution mode, current step, pending confirmation, and idempotency key;
- tool outcomes, policy decisions, response obligations, and handoff state;
- a compact running summary and limited recent turns when nuance is needed.

### 4.3 Goal manager

A **goal** is a persistent unit of user work, not merely a predicted intent label. A goal has an objective, owner, lifecycle status, facts, dependencies, current step, capability binding, and outcome.

Recommended lifecycle:

```text
PROPOSED -> ACTIVE -> WAITING_FOR_INPUT -> READY_TO_EXECUTE
         -> EXECUTING -> COMPLETED
                      -> FAILED / HANDED_OFF / ABANDONED

ACTIVE <-> PAUSED when another goal temporarily takes focus
```

The goal manager creates or updates goals from structured understanding output, determines whether the latest turn continues, corrects, interrupts, or cancels current work, and prevents invalid transitions. Sophisticated multi-goal optimization is optional; explicit current and paused goals are foundational.

### 4.4 LangGraph orchestration

LangGraph is the reference orchestration framework because it supports explicit state, conditional routing, checkpoints, interruption, and resumable workflows. The graph should coordinate typed platform services rather than becoming the place where all business logic accumulates.

Representative nodes are receive turn, apply input controls, understand turn, reconcile goals, resolve capability, load capability, assess policy, collect facts, plan next step, request confirmation, execute tool, validate outcome, compose response, apply output controls, persist state, and emit telemetry.

Graph transitions are explicit and testable. Nodes use structured inputs and outputs. Side-effecting nodes require a policy decision and idempotency boundary. Checkpoints are persisted before and after consequential actions.

### 4.5 Capability registry and dynamic loading

At startup or refresh, the registry loads small, validated discovery records—not every capability’s complete prompt and implementation context. A discovery record contains identifier, version, description, examples, supported goals, eligibility/risk hints, execution modes, required facts, and package location.

Selection occurs against metadata. After the resolver selects a capability, the loader verifies integrity and compatibility, loads its full manifest and resources, binds approved tools and policies, and pins the chosen version to the goal. Registry changes are versioned and observable; invalid or revoked capabilities fail closed.

### 4.6 Capability runtime

The shared capability runtime validates manifests, resolves dependencies, binds configuration, exposes bounded orchestration hooks, and translates capability declarations into runtime behavior. It prevents each business team from creating its own agent loop.

Capabilities may contain declarative configuration and narrowly scoped code where domain transformation is genuinely required. They should not own platform session management, provider clients, generic tool execution, telemetry, or policy engines.

### 4.7 Tool gateway

All external actions pass through a tool gateway that provides:

- schema validation and typed error mapping;
- authentication and authorization propagation;
- allow-list enforcement by capability and environment;
- timeouts, retry policy, circuit breaking, and idempotency;
- masking and data minimization;
- pre-execution confirmation checks;
- audit events and trace correlation;
- simulation/mocking for tests and evaluations.

The LLM never receives direct network credentials and cannot bypass the gateway.

### 4.8 Inference provider abstraction

The provider interface exposes business-neutral operations such as generate structured decision, generate text, stream response, count/record usage, and report provider capabilities. It normalizes model identifiers, timeouts, retryable failures, structured outputs, safety signals, token use, and trace context.

The first adapter targets OpenAI. Additional adapters can target another inference service without changing goal, policy, capability, or response contracts. Provider-specific caching, routing, batch execution, and safety controls are optional capabilities behind the interface—not core architecture dependencies.

### 4.9 Response composer and contracts

Capabilities return a typed **response intent**, not final ungoverned prose. The response composer combines:

- verified business facts and tool results;
- goal and step status;
- channel and locale requirements;
- required disclosures and prohibited content;
- supported user actions and handoff instructions;
- tone and accessibility rules.

A response contract can include message, title, status, disclosures, actions, citations/provenance, channel hints, and metadata. Deterministic templates are preferred for confirmations, receipts, legal disclosures, and high-risk outcomes. Model-assisted wording is suitable only inside allowed fields and is validated before release to the channel.

### 4.10 Guardrails

Guardrails are layered controls, not a single vendor feature:

- **Input:** injection screening, data classification, content safety, rate/abuse controls.
- **Decision:** structured-output validation, confidence thresholds, capability allow lists, policy evaluation.
- **Execution:** authorization, eligibility, confirmation, limits, idempotency, audit.
- **Output:** grounding checks, sensitive-data masking, disclosure enforcement, response-schema validation.
- **Operational:** kill switches, model/capability rollback, anomaly monitoring, human handoff.

Provider guardrails can implement part of input/output safety. Business controls remain in platform policy and execution code.

## 5. Execution modes

The runtime selects an execution mode for each capability or step based on declared behavior and risk.

| Mode | Model role | Platform behavior | Typical use |
|---|---|---|---|
| Conversational | Interpret and draft within bounds | Flexible dialogue; no consequential side effect | Education, discovery, FAQ, exploration |
| Guided | Interpret choices and help collect required facts | Enforced steps, validations, eligibility, and bounded tools | Intake, troubleshooting, pre-transaction flow |
| Deterministic | Optional extraction or phrasing only | Fixed state machine, explicit confirmation, authorized execution, deterministic receipt | Money movement, enrollment, account changes |

A conversation can move between modes. For example, it can begin conversationally, enter guided fact collection, then use deterministic confirmation and execution. Mode escalation is a platform decision and cannot be overridden by the model.

## 6. Context and memory strategy

Each model call receives the smallest context needed for its bounded task:

1. stable platform instructions and relevant contracts;
2. current identity and policy-safe session context;
3. active goal, current step, known facts, and pending obligations;
4. selected capability details only after selection;
5. compact conversation summary and a few recent turns when required;
6. the latest user input.

The raw conversation is transformed into structured state rather than replayed verbatim. This improves cost, latency, privacy, evaluation, and provider portability. Prompt caching is treated as a provider optimization; context minimization remains the architectural control.

## 7. Capability model

### 7.1 Capability package

Each capability is a versioned package with:

- manifest and discovery metadata;
- business feature specification and acceptance examples;
- goal types, required facts, clarification rules, and completion criteria;
- supported execution modes and response intents;
- approved tool bindings and typed schemas;
- policy/risk declarations and disclosure references;
- prompts or instruction fragments where appropriate;
- deterministic domain transforms when required;
- tests, evaluation scenarios, ownership, support, and release metadata.

### 7.2 Manifest example

```yaml
id: funds-transfer
version: 1.3.0
owner: payments-product
supports_goals: [transfer_funds]
execution_modes: [guided, deterministic]
required_facts: [source_account, destination_account, amount]
tools: [account_lookup, transfer_preview, transfer_execute]
risk_class: consequential_action
policies:
  - authenticated-session
  - explicit-confirmation
  - financial-action-audit
response_contract: financial-action-v1
```

### 7.3 Capability lifecycle

```text
Propose -> specify -> risk classify -> implement -> verify
        -> evaluate -> approve -> publish -> observe -> revise/retire
```

A capability is publishable only when its manifest, contracts, policies, tests, eval results, owners, and rollback information are complete. Registry publication is a controlled release event.

## 8. Specifications versus governance

**Specifications define what the system is and how it should behave. Governance defines what the system is permitted to do and what controls or evidence are mandatory.**

| Artifact or requirement | Home | Reason |
|---|---|---|
| Architecture descriptions and ADRs | `specs/architecture`, `specs/adr` | Defines structure and decisions |
| Feature behavior and acceptance examples | `specs/features` | Defines what to build |
| Runtime, state, tool, event, capability, response schemas | `specs/contracts` | Defines component communication |
| Mandatory confirmation for consequential actions | `governance/controls` | Constraint that must always hold |
| Approved models/tools and data handling | `governance/policies` | Enterprise permission and restriction |
| Risk classification and approval thresholds | `governance/risk`, `governance/approvals` | Determines required controls/evidence |
| AI behavior scenarios and graders | `evals/` | Proves probabilistic behavior |
| Deterministic code correctness | `tests/` | Proves software behavior |

A feature specification references policy identifiers; it does not copy policy text. A policy references applicable contracts or risk classes; it does not redefine those schemas.

### 8.1 Decision test

- If the question is **“What should it do or how do components communicate?”**, put it in specifications.
- If the question is **“What must always be allowed, denied, controlled, recorded, or approved?”**, put it in governance.
- If it is both, keep the behavior in the spec and reference the reusable control in governance.

## 9. Policy as code and enforcement points

Machine-readable governance is consumed in several places.

| Stage | Consumer | Representative enforcement |
|---|---|---|
| Design | Product, architecture, risk, development agents | Required sections, ownership, risk classification, policy references |
| Build | Linters, test harnesses, verification agents | Schema validity, approved dependencies, policy coverage, security checks |
| CI/CD | Pipeline policy evaluator and approvers | Eval thresholds, contract compatibility, evidence completeness, separation of duties |
| Runtime decision | Policy decision service | Capability/tool allow lists, authentication, eligibility, limits, confirmation |
| Runtime execution | Tool gateway | Re-check decision, idempotency, audit, data minimization |
| Runtime response | Composer and output controls | Required disclosure, masking, response-contract conformance |
| Operations | Monitoring, risk, platform operations | Drift/anomaly alerts, kill switch, rollback, periodic review |

Not every policy must be a general-purpose rules engine. Some controls are schema validations, some are runtime code, some are provider safety features, and some remain human approvals. Every mandatory rule should identify its owner, scope, representation, enforcement point, evidence, and exception process.

## 10. Contracts and events

Core contracts should be versioned, generated where practical, and compatibility-tested.

- **TurnRequest / TurnResponse:** normalized channel interaction.
- **ConversationState / Goal:** persisted state and valid transitions.
- **CapabilityManifest / CapabilityContext:** discovery and loaded execution context.
- **ToolRequest / ToolResult:** authorized integration boundary, errors, idempotency, provenance.
- **PolicyDecision:** allow/deny/obligations/reason/evidence.
- **ResponseIntent / ComposedResponse:** business result separated from presentation.
- **Domain and platform events:** goal created/paused/resumed/completed, capability selected, confirmation requested/received, tool proposed/executed, policy denied, handoff initiated.

Events must carry correlation, causation, schema version, tenant/environment, actor reference, sensitivity classification, and timestamp. Sensitive payloads should be referenced or minimized rather than copied into telemetry.

## 11. Evaluation and testing model

Traditional tests and AI evaluations are complementary.

### 11.1 Tests

- unit tests for state transitions, policy evaluators, composers, and adapters;
- contract and backward-compatibility tests;
- graph-path and checkpoint/resume tests;
- integration tests with deterministic tool simulators;
- security, performance, resilience, and disaster-recovery tests.

### 11.2 Evaluations

- goal recognition and goal-update accuracy;
- capability selection precision/recall and abstention;
- fact extraction, clarification quality, and correction handling;
- interruption, pause, resume, and cancellation behavior;
- tool proposal accuracy and prohibited-tool rate;
- groundedness, hallucination, disclosure, masking, tone, and accessibility;
- task completion, turns to completion, containment/handoff quality;
- latency, token use, and cost per completed goal.

Evaluation suites combine deterministic checks, domain graders, model-assisted graders with calibration, and periodic human review. Results are segmented by capability, model, prompt, language, risk class, and relevant user cohorts. Production traces can be sampled into curated regression cases only under data and consent policy.

### 11.3 Release quality gates

No release relies on one aggregate score. High-risk invariants such as unauthorized execution, missing confirmation, data leakage, or missing disclosure have zero-tolerance or explicitly approved thresholds. Quality trends are compared to an approved baseline; material regressions block promotion.

## 12. Observability and operations

OpenTelemetry is the common instrumentation layer for traces, metrics, and logs. Langfuse is the default LLM observability and evaluation surface. Provider, orchestration, capability, tool, policy, and response spans share trace context.

### 12.1 Required telemetry

- session, turn, goal, capability, policy decision, model call, tool, and response spans;
- prompt/model/capability versions and structured decision outcomes;
- latency by stage, token use, cost, retries, and error class;
- goal completion, abandonment, handoff, clarification, interruption, and recovery rates;
- confirmation and denial outcomes for consequential actions;
- redacted audit records for side effects and policy changes.

### 12.2 Data discipline

Telemetry schemas classify fields and define allowed destinations. Protected data is redacted or tokenized before export. Prompts and completions are captured only under explicit environment and data-policy controls. Operational traces and legally significant audit records have separate retention and access rules.

### 12.3 Operational controls

Use feature flags, canary releases, model/prompt/capability pinning, rollback, rate and budget limits, dependency health, circuit breakers, and kill switches. Runbooks cover provider degradation, policy-service failure, registry corruption, tool outage, unsafe output, evaluation regression, and security incident.

## 13. CI/CD and release model

The monorepo can have distinct path-aware lanes while preserving an integrated release view.

1. **Change classification:** identify platform, capability, contract, governance, eval, and infrastructure impact.
2. **Fast validation:** formatting, types, unit tests, schemas, policy linting, secrets and dependency scans.
3. **Affected integration:** contract compatibility, graph paths, provider/tool simulations.
4. **Evaluation:** affected capability suites plus platform safety regression.
5. **Evidence assembly:** immutable versions, results, risk classification, approvals, change summary, rollback plan.
6. **Progressive promotion:** development, test, staging, canary, production.
7. **Post-deploy verification:** synthetic goals, telemetry health, quality and safety watch.

Platform releases are slower and broadly governed. Capability releases can become faster when they remain compatible with stable contracts and pass capability-specific policies and evaluations. Contract or governance changes trigger wider review.

## 14. Target repository structure

```text
conversational-ai-platform/
|-- src/conversational_ai/              # deployed Python runtime
|   |-- api/                            # turn/channel interfaces
|   |-- orchestration/                  # LangGraph graphs and nodes
|   |-- conversation/                   # turn handling and summaries
|   |-- goals/                          # goal lifecycle and focus
|   |-- session/                        # state persistence/checkpoints
|   |-- capabilities/                   # registry, resolver, loader, runtime
|   |-- tools/                          # gateway and adapters
|   |-- providers/                      # inference provider interface/adapters
|   |-- policy/                         # runtime policy decisions
|   |-- response/                       # composer and rendering
|   |-- guardrails/                     # layered input/output controls
|   |-- observability/                  # OTel and Langfuse integration
|   `-- models/                         # internal typed models
|-- capabilities/                       # versioned business capability packages
|   `-- <capability>/
|       |-- capability.yaml
|       |-- instructions/
|       |-- responses/
|       |-- bindings/
|       |-- policies.yaml
|       |-- tests/
|       `-- evals/
|-- specs/                              # technical source of truth
|   |-- architecture/
|   |-- adr/
|   |-- features/
|   `-- contracts/{runtime,capability,tools,events,response}/
|-- workflows/                          # development-time agentic workflows
|   |-- impact-analysis/
|   |-- specification/
|   |-- implementation-planning/
|   |-- implementation/
|   |-- independent-verification/
|   |-- promotion/
|   `-- release-evidence/
|-- evals/{datasets,scenarios,graders,regression,reports,baselines}/
|-- governance/{policies,risk,controls,approvals,exceptions}/
|-- tests/{unit,contract,integration,resilience,performance}/
|-- infra/{modules,environments,observability}/
|-- docs/{runbooks,operations,onboarding}/
`-- .gitlab-ci.yml
```

The boundaries are semantic even while everything lives in one repository:

- `src/` tells the platform **how to operate**.
- `capabilities/` tells the runtime **what business work it can perform**.
- `specs/` tells teams **what must be built and how parts communicate**.
- `workflows/` tells development agents **how to analyze, build, verify, and promote**.
- `evals/` proves **AI behavior**.
- `governance/` defines **what is permitted and what evidence is mandatory**.
- `tests/` proves **deterministic software behavior**.

## 15. Operating model and ownership

| Concern | Accountable owner | Key collaborators |
|---|---|---|
| Runtime, contracts, shared controls | Conversational platform team | Architecture, security, SRE |
| Business capability and outcomes | Product/capability owner | SMEs, capability engineers, platform |
| Mandatory policy and risk acceptance | Business risk/control owner | Compliance, security, legal, platform |
| Evaluation framework and quality gates | AI Evaluation & Quality Engineering | Product, QA, platform, COE |
| Cloud, reliability, incident response | Platform operations/SRE | Security, provider teams, capability owners |
| Patterns, enablement, independent guidance | AI Center of Excellence | All delivery teams |
| Production promotion | Named release authority | Product, engineering, risk, operations |

The AI Center of Excellence enables every team to build AI; it does not become the only team allowed to build AI. It curates patterns, calibration methods, reference implementations, training, and specialist review. Product and capability teams remain accountable for business outcomes.

## 16. Security, privacy, and resilience

- Propagate authenticated identity; never delegate authorization to the model.
- Use least-privilege service identities and per-tool permissions.
- Separate secrets from prompts, state, capability packages, and telemetry.
- Classify and minimize data at ingestion, persistence, provider calls, tools, responses, and traces.
- Protect against prompt injection through trust boundaries, content provenance, tool isolation, and deny-by-default execution.
- Encrypt data in transit and at rest; define retention, deletion, access review, and legal hold.
- Threat-model capability publishing, registry poisoning, model output manipulation, replay, duplicate execution, and cross-tenant leakage.
- Fail closed for policy, authorization, registry-integrity, and confirmation uncertainty; degrade gracefully for optional model assistance.
- Verify backup, restore, provider failover posture, and recovery objectives.

## 17. Architecture decisions to formalize

Recommended initial ADRs:

1. LangGraph as the reference stateful orchestrator.
2. Structured conversation state and goals as primary memory.
3. Model-advises/platform-decides control boundary.
4. Capability manifest, registry, selection, loading, and version pinning.
5. Execution-mode model: conversational, guided, deterministic.
6. OpenAI-first provider adapter behind a vendor-agnostic interface.
7. Response intent/composer/contract separation.
8. Policy-as-code representation and enforcement architecture.
9. OpenTelemetry semantic conventions and Langfuse default integration.
10. Monorepo modular boundaries and extraction criteria.
11. Test versus evaluation ownership and release gates.
12. State, transcript, telemetry, and audit retention model.

## 18. Ideal-state success measures

The platform is successful when it improves outcomes and leverage without weakening control. Track:

- completed goals and verified business outcomes;
- completion without avoidable handoff, plus appropriate handoff rate;
- turns, latency, and cost per completed goal;
- capability-selection precision and safe abstention;
- correction, interruption, resume, and recovery success;
- prohibited execution, missing confirmation, leakage, and policy violations;
- evaluation escape rate and production regressions;
- time from approved specification to capability release;
- percentage of capabilities using shared contracts, tools, controls, and eval infrastructure;
- mean time to detect, contain, roll back, and recover.

## 19. Definition of the target state

The ideal state is achieved when a funded team can add a new governed capability primarily by supplying a specification, manifest, approved bindings, policies, response intents, tests, and evaluation scenarios—while reusing the platform’s state, goals, orchestration, provider, tool, policy, response, telemetry, and release controls.

That is the central leverage of the architecture: **many business capabilities, one governed conversational platform, and one repeatable delivery system.**
