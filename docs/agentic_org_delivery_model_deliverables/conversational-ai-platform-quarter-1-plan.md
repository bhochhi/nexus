# Conversational AI Platform

## Quarter-One Delivery Plan: One Funded Capability on a Reusable Platform Spine

**Planning horizon:** 12 weeks  
**Repository:** `conversational-ai-platform`  
**Anchor:** One funded business capability, named **Funded Capability** until the business name is supplied  
**Outcome:** Deliver the funded capability to an agreed production-readiness level while proving the smallest reusable platform path for the next capability.

---

## Executive decision

Build the platform through the funded capability. Do not run a broad platform program beside a separate capability project.

> **One repository. One funded capability. One reusable platform spine. Multiple low-scale workstreams in parallel.**

Quarter one is intentionally narrow in implemented scope, but not narrow in architecture. Every shared component must be justified by the funded capability or by a non-negotiable production control. Future sophistication is represented through stable seams, contracts, and ADRs rather than partially implemented frameworks.

The release goal is not “the complete platform.” It is:

1. one end-to-end funded capability that meets business acceptance criteria;
2. one reusable runtime path from channel to goal to capability to governed tool/result to response;
3. one repeatable specification, evaluation, governance, and promotion path;
4. evidence that a second capability can be added without copying or rewriting the core.

## 1. Planning assumptions

- The actual funded capability name and detailed requirements were not present in the source discussion; this plan uses a replaceable **Funded Capability** label.
- The capability has a clear product owner and one or more business SMEs.
- The production environment is AWS, but inference begins OpenAI-first behind a provider abstraction.
- The capability may require eligibility and one or more enterprise API/tool integrations.
- GitLab is the source and CI/CD system.
- Delivery is 12 weeks with progressive scope gates; production release depends on security, risk, environment, and integration readiness.
- The platform is a Python application with LangGraph orchestration.

## 2. Quarter-one scope rule

Build a component now only when at least one of these is true:

- the funded capability cannot meet an acceptance criterion without it;
- it is a non-negotiable control for security, risk, privacy, audit, or operations;
- it is the minimum seam needed to prevent the capability from becoming a one-off;
- it provides release evidence that cannot safely be reconstructed later.

Everything else is documented as a deferred decision or extension point.

## 3. Minimum reusable platform spine

```text
Client / test harness
  -> API and identity context
  -> session + structured state
  -> LangGraph turn orchestration
  -> goal/current-work manager
  -> capability registry + dynamic loader
  -> Funded Capability
  -> policy/eligibility/confirmation checks
  -> governed tool gateway
  -> response intent + composer + output checks
  -> client

Across every step: OpenTelemetry -> Langfuse; audit where required
```

### 3.1 Build now

| Platform slice | Quarter-one minimum | Reuse proof |
|---|---|---|
| Turn API and channel contract | One production channel or representative adapter; correlation and identity context | Channel-independent runtime contract |
| Session and state | Persist active goal, facts, capability/version, step, confirmation, tool result, compact summary | State contract reusable by capability two |
| LangGraph orchestrator | Explicit end-to-end graph, typed nodes, checkpoints, error paths | Shared graph with capability hooks, not copied graph |
| Goal management | Create/update one current goal; pause/resume for an interruption; correct/cancel | Goal lifecycle independent of funded domain |
| Registry and loader | Validate discovery metadata; select one capability; load and pin full package | Add a second fixture capability without runtime edits |
| Provider abstraction | Stable interface plus OpenAI adapter, structured output, retries, usage | Domain code contains no OpenAI-specific calls |
| Execution modes | Conversational/guided/deterministic labels and enforcement; use only modes needed | Mode is declared by capability/step |
| Tool gateway | Typed requests/results, allow list, timeout, idempotency, mock and one real adapter | Capability cannot call integration directly |
| Policy hook | Authentication, eligibility, tool allow list, confirmation, audit obligations as applicable | Policy decision is separate from prompt |
| Response composer | Typed response intent, one versioned response contract, deterministic critical messages | Capability does not return arbitrary final payload |
| Guardrails | Input/output safety, schema checks, data masking, safe fallback/handoff | Controls applied consistently outside capability |
| Observability | OTel trace context, Langfuse traces/evals, essential metrics and redaction | One trace links turn, goal, model, policy, tool, response |
| Evaluation harness | Curated scenarios, deterministic graders, calibrated qualitative grading, baseline report | Same harness runs platform and capability suites |
| Delivery controls | Path-aware GitLab lanes, evidence bundle, staged deployment, rollback | Capability-only change has bounded release path |

### 3.2 Funded Capability deliverables

- signed-off feature specification and measurable business outcome;
- capability manifest, goal definition, required facts, conversation examples, and completion criteria;
- declared risk class, applicable policies, and named business/control owners;
- eligibility logic and enterprise tool bindings required for the funded slice;
- guided and/or deterministic flow for consequential steps;
- response intents, approved language, disclosures, and error/handoff behavior;
- unit, contract, integration, and scenario evaluations;
- runbook, dashboard, release evidence, rollback, and support ownership.

## 4. Explicitly defer

| Defer from quarter one | Preserve now through |
|---|---|
| Sophisticated simultaneous multi-goal decomposition and prioritization | Goal collection and lifecycle schema; current/paused goal support |
| Arbitrary model-authored plans or autonomous tool chains | Typed next-action contract and bounded graph transitions |
| Many production capabilities or a capability marketplace | Registry/manifest contract and a second fixture capability |
| Multiple production inference providers and automatic provider routing | Provider interface, OpenAI adapter, contract tests |
| Full no-code capability authoring portal | Declarative package format and validation CLI/pipeline |
| Per-capability repositories | Strong monorepo boundaries and path-aware CI |
| General-purpose enterprise policy engine | Machine-readable policies plus targeted validators/enforcement hooks |
| Enterprise-wide event streaming platform | Versioned event contracts and local/outbox publisher seam |
| Semantic memory or knowledge graph | Structured state and explicit retrieval interface if funded scope needs it |
| Advanced prompt caching/cost router | Stable/dynamic prompt sections, usage telemetry, provider capability seam |
| Every channel, locale, and modality | Common turn/response contracts and one representative channel |
| Self-service analytics portal | Core metrics, trace views, baseline report, dashboard skeleton |

Deferred means **not implemented this quarter**, not “quietly added if time remains.” Any pull-forward requires sponsor-approved tradeoff against the funded outcome.

## 5. Workstreams and staffing

These are parallel ownership streams inside one integrated team, not six new departments.

| Workstream | Suggested capacity | Quarter-one accountability |
|---|---:|---|
| Product, business specification, and conversation design | Product owner + 1-2 SMEs; 0.5-1 conversation designer/BA | Outcome, scenarios, acceptance, approved responses, decisions within 24-48 hours |
| Runtime platform | 3-4 engineers including technical lead | State, LangGraph, goals, registry/loader, provider, tool gateway, response, controls |
| Funded capability pod | 2-3 engineers | Capability package, eligibility/domain logic, integrations, tests, operational behavior |
| AI Evaluation & Quality Engineering | 1-2 engineers | Scenario dataset, graders, baselines, regression, trace analysis, quality gate |
| Cloud, CI/CD, security, and operations | 1-2 shared engineers | AWS environments, GitLab lanes, secrets, OTel/Langfuse, dashboards, rollback/runbooks |
| Risk/security/compliance | Named part-time decision owners | Risk class, policies, threat model, control evidence, release approval |
| AI Center of Excellence | 0.25-0.5 advisory capacity | Patterns, prompt/eval guidance, calibration, independent architecture review |

Practical team size is approximately 8-11 delivery FTE plus committed product/SME and control-owner time. With fewer people, preserve the sequence and combine roles; do not delete evaluation, operations, or governance ownership.

### 5.1 Required named roles

- Product owner with scope authority.
- Business capability owner accountable after launch.
- Runtime technical lead and capability technical lead.
- AI Evaluation & Quality Engineering lead.
- Security/risk control owner with approval authority.
- Release/operations owner and incident commander role.

### 5.2 Paired Business-IT capability delivery model

Quarter one uses a paired Business-IT capability delivery model. The business capability owner and an IT capability engineer work together from intake through production learning. This avoids two weak operating patterns: expecting business users to become repository developers, or asking IT to translate business intent alone and seek approval only after implementation.

Business ownership means accountability for the member outcome and capability behavior. It does not require business users to work in VS Code, use Copilot, write YAML, or operate Git. During quarter one, the IT capability engineer operates the repository and AI development workflow. Business participants review plain-language specifications, example conversations, preview behavior, and evaluation results.

| Artifact or decision | Business responsibility | IT responsibility | AI development workflow contribution |
|---|---|---|---|
| Member outcome and supported scope | Accountable; defines value, users, supported requests, and exclusions | Challenges ambiguity and identifies feasibility constraints | Structures the intake and identifies missing decisions |
| Examples, business rules, and disclosures | Authors and approves representative behavior | Maps requirements to platform contracts, tools, and controls | Generates variants and checks coverage |
| Acceptance criteria | Co-owns expected behavior and success thresholds | Co-owns executable precision and verification design | Normalizes stable acceptance IDs and creates traceability |
| `CAPABILITY.md` | Approves business meaning | Technical co-author and repository owner | Drafts, analyzes, and validates the specification |
| `SKILL.md`, tools, and platform dependencies | Approves member-visible behavior | Accountable for implementation and technical correctness | Generates or updates the candidate skill, tests, and impact analysis |
| Evaluation scenarios and release decision | Approves expected outcomes and business readiness | Implements the harness and supplies technical release evidence | Expands scenarios, executes evaluations, and assembles evidence |

Business begins with a short capability intent and acceptance template rather than the full technical `CAPABILITY.md` template. The intake records:

- the member outcome and intended users;
- supported questions or actions and explicit exclusions;
- approved information sources, business rules, and disclosures;
- successful, ambiguous, unsupported, unsafe, and failure examples;
- expected clarification, response, navigation, or handoff behavior;
- measurable business and quality outcomes; and
- the accountable business owner and required approvers.

The paired workflow is:

```text
Business capability intake
  -> paired Business-IT specification workshop
  -> AI-assisted CAPABILITY.md and acceptance-scenario draft
  -> business behavior approval and IT dependency approval
  -> AI-assisted SKILL.md, tests, and evaluations
  -> isolated preview and evidence review
  -> business acceptance and controlled publication
```

`CAPABILITY.md` remains the authoritative statement of business intent. `SKILL.md` is the executable implementation of that approved intent. The AI workflow may draft and validate both artifacts, but it cannot approve business meaning, control requirements, or production activation.

The quarter-one process should capture rework, unresolved decisions, review time, and evaluation findings. Those observations become requirements for a future Business Capability Studio where authorized business users can edit intent and scenarios, preview conversations, review evaluation evidence, and request publication without using developer tools. Self-service should begin with low-risk declarative changes; new tools, sensitive data, platform extensions, and consequential actions continue to require engineering and control review.

## 6. Twelve-week delivery roadmap

### Weeks 1-2: Align, specify, and walk the skeleton

**Business and specs**

- define outcome, users, funded boundary, happy path, exclusions, service levels, and handoff;
- assign the Business-IT capability pair and complete the capability intent and acceptance intake;
- write conversation scenarios including corrections, ambiguity, interruption, failure, and unsafe requests;
- define capability, state, tool, response, and policy contracts required for the slice;
- classify risk and name policy/control owners.

**Technical and delivery**

- establish monorepo structure, coding standards, ADRs, environments, secrets, and GitLab skeleton;
- implement a walking skeleton from API through LangGraph to a mock capability/tool and composed response;
- emit an OTel trace to Langfuse and run the first five to ten evaluation scenarios.

**Milestone A - Architecture and scope baseline:** An executable thin slice exists; business accepts capability scope; required controls and contracts have owners.

### Weeks 3-5: Build the reusable spine and vertical happy path

- persist structured state and goal lifecycle;
- validate capability metadata, dynamically load and version-pin the funded package;
- implement the OpenAI provider adapter behind the interface;
- build the tool gateway with mock adapters, allow lists, timeout/error mapping, and idempotency;
- implement policy/eligibility hook and typed response intent/composer;
- connect one real enterprise integration in a non-production environment;
- expand evaluation data before prompt or orchestration tuning.

**Milestone B - Integrated happy path:** The funded capability completes its primary path end to end in a test environment with trace, policy decision, tool simulation/real test call, and response contract.

### Weeks 6-8: Complete funded behavior and conversational resilience

- complete required eligibility, facts, validations, and integrations;
- implement clarification, correction, cancel, safe unsupported request, and tool-error recovery;
- implement one meaningful interruption and resume behavior without full multi-goal optimization;
- enforce guided/deterministic transitions and explicit confirmation where required;
- add input/output guardrails, masking, disclosure, safe fallback, and human handoff;
- conduct threat modeling and failure-mode review.

**Milestone C - Feature complete:** Business acceptance scenarios pass in staging; all consequential paths are controlled and auditable.

### Weeks 9-10: Harden and prove

- run full regression and adversarial/safety evaluation suites;
- tune against an approved dataset; freeze a release candidate baseline;
- test performance, concurrency, dependency failures, duplicate requests, checkpoint recovery, and rollback;
- finalize dashboards for quality, safety, latency, cost, errors, and business outcome;
- perform accessibility, privacy, security, and operational-readiness review.

**Milestone D - Release candidate:** No open critical defects or zero-tolerance evaluation failures; evidence bundle is complete.

### Weeks 11-12: Controlled release and learn

- promote through staging and canary/limited audience;
- run production synthetic checks and heightened telemetry review;
- verify support, incident, rollback, and business-operations handoffs;
- capture decisions and reusable onboarding checklist;
- demonstrate addition of a second fixture capability using the registry/loader without editing runtime routing.

**Milestone E - Quarter outcome:** Funded Capability reaches the approved release level and the reusable spine is proven. If external approval or integration readiness prevents production traffic, the fallback outcome is a production-ready release candidate with explicit owner/date for each dependency—not a claim of launch.

## 7. Critical path and dependencies

```text
Business decisions and examples
  -> signed specification + risk classification
  -> contracts and walking skeleton
  -> real eligibility/tool integration
  -> end-to-end funded behavior
  -> evaluation and control evidence
  -> environment/security approval
  -> controlled release
```

The most likely schedule risks are slow business decisions, unstable enterprise APIs, late risk interpretation, unavailable test data, production environment lead time, and evaluation work beginning too late. Assign dates and owners in week one. Use mocks and contract tests to keep platform and capability work moving while integrations are pending.

## 8. Specifications package for quarter one

`specs/` is the technical source of truth.

### 8.1 Required architecture and ADRs

- quarter-one context and component architecture;
- LangGraph orchestration and checkpoint strategy;
- structured state and goal lifecycle;
- capability registry/loading/version pinning;
- OpenAI-first provider abstraction;
- tool gateway and side-effect boundary;
- execution modes and confirmation boundary;
- response composer/contracts;
- telemetry and sensitive-data handling;
- monorepo and release-lane decision.

### 8.2 Required contracts

- turn request/response;
- conversation state and goal;
- capability discovery record and manifest;
- tool request/result and typed errors;
- policy decision and obligations;
- response intent/composed response;
- essential audit/platform events.

### 8.3 Funded feature specification

The capability specification must include business outcome, actors, preconditions, supported goals, required facts, happy path, alternate and failure paths, eligibility, tool effects, confirmation, responses/disclosures, handoff, non-functional requirements, analytics, acceptance scenarios, and out-of-scope behavior.

## 9. Governance package and enforcement

Quarter one needs a small enforceable set, not a governance library for every future domain.

| Governance artifact | Primary owner | Enforcement this quarter |
|---|---|---|
| Capability risk classification | Business risk + product | Required manifest field and approval gate |
| Approved model/provider policy | AI governance/security | Configuration allow list and pipeline validation |
| Tool authorization policy | Security + platform | Manifest allow list plus gateway enforcement |
| Authentication/eligibility control | Business/risk + capability | Pre-execution policy node and tests |
| Confirmation control, if consequential | Business/risk | State-machine obligation and gateway re-check |
| Data handling/masking policy | Privacy/security | Schema classification, telemetry filter, output validator |
| Audit policy | Risk/operations | Required event fields and evidence check |
| Evaluation/release thresholds | Product + AI quality + risk | GitLab quality gate and approval rule |
| Exception process | Risk + release authority | Time-bound record with compensating controls |

### 9.1 Policy-as-code checkpoints

- **Pre-merge:** policy files and manifest references validate; required tests/evals exist for risk class.
- **Pre-deploy:** approved model/tools, evidence, security scans, compatibility, and threshold checks pass.
- **Runtime before action:** identity, eligibility, tool permission, confirmation, limit, and obligations are evaluated.
- **Tool gateway:** authorization and confirmation are re-checked; idempotency and audit are enforced.
- **Before response:** masking, disclosure, schema, and safety controls pass.
- **Operations:** alerts, kill switch, rollback, and periodic review are available.

Provider guardrails may help with content safety. They do not replace confirmation, eligibility, tool authorization, response obligations, or audit.

## 10. Runtime implementation boundary

### 10.1 Shared runtime code

The Python runtime owns API contracts, state/checkpoints, LangGraph orchestration, goal lifecycle, registry/loader, provider client, policy integration, tool gateway, response composer, guardrails, telemetry, and common typed models.

### 10.2 Capability-owned package

The funded capability owns its manifest, business instructions, goal/fact definitions, response intents, approved tool bindings, policy declarations, domain transforms, tests, and evaluations. It must not create a parallel provider client, state store, orchestration loop, policy engine, response renderer, or telemetry stack.

### 10.3 Goal-driven minimum

The quarter-one goal manager supports one active goal and at least one paused goal, with create, update, wait, pause, resume, cancel, complete, fail, and handoff transitions. Full multi-objective decomposition is deferred.

## 11. CI/CD design

Use one `.gitlab-ci.yml` entry point with reusable templates and path-aware lanes.

For the Q1 AWS publication, account-isolation, S3 artifact, DynamoDB catalog,
Terraform, Lambda refresh, and rollback design, see
[`q1-capability-publication-and-runtime-activation.md`](q1-capability-publication-and-runtime-activation.md).

### 11.1 Platform-change lane

Triggered by `src/`, shared contracts, shared tests, core governance, infrastructure, or pipeline changes.

```text
lint/type/unit/security
 -> contract + graph-path tests
 -> platform safety regression
 -> integration/resilience tests
 -> evidence + approvals
 -> staged platform deployment
```

### 11.2 Capability-change lane

Triggered by `capabilities/funded-capability/`, its feature specs, policy bindings, or capability evaluations.

```text
manifest/spec/policy validation
 -> capability unit + contract tests
 -> affected conversation evaluations
 -> tool simulation/integration tests
 -> evidence + business/control approval
 -> publish capability version / deploy configuration
```

### 11.3 Evaluation lane

Runs on merge requests, scheduled baselines, model/prompt changes, and release candidates.

```text
dataset integrity
 -> deterministic graders
 -> model-assisted graders
 -> safety invariants
 -> comparison to approved baseline
 -> signed report and threshold decision
```

### 11.4 Promotion controls

- immutable runtime, capability, prompt, policy, and evaluation versions;
- environment-specific configuration separated from packages;
- required approvals based on paths and risk;
- canary/limited release, automated health verification, and documented rollback;
- production registry publication only from the controlled pipeline.

## 12. Evaluation strategy

### 12.1 Scenario set

Begin in week one with business-authored examples. By release candidate, cover:

- happy paths and legitimate variations;
- incomplete, ambiguous, colloquial, and contradictory inputs;
- corrections and changed facts;
- interruption and resume;
- cancellation and abandonment;
- ineligible users and policy denial;
- missing/failed/slow tools and duplicate requests;
- prompt injection, sensitive-data requests, unsafe content, and prohibited actions;
- required disclosures, masking, receipts, and handoff;
- latency/cost and long-conversation boundaries.

### 12.2 Measures and gates

| Dimension | Example measure | Gate approach |
|---|---|---|
| Business completion | Required outcomes achieved with correct system-of-record result | Threshold agreed by product; critical paths must pass |
| Goal/capability | Correct goal update and capability selection/abstention | Compare to labeled set; no unsafe false positives |
| Tool safety | Correct tool/arguments; no unapproved execution | Zero unauthorized or unconfirmed consequential calls |
| Response | Grounded, correct, complete, compliant, accessible | Deterministic invariants plus calibrated rubric |
| Resilience | Clarification, correction, interruption, recovery, handoff | Required scenario pass rate; no dead ends |
| Operations | Latency, errors, token use, cost per completed goal | Budget and service thresholds; trend against baseline |

Exact numeric thresholds must be agreed during weeks 1-2 after a baseline exists. The plan does not invent thresholds without business and risk approval.

### 12.3 Evaluation evidence

Every release report records dataset version, model/provider configuration, prompt and capability versions, grader versions, results by risk category, baseline comparison, failures, approvals, and trace links. Human review samples model-graded cases to detect grader drift.

## 13. Observability and production readiness

### 13.1 Quarter-one trace

One trace must connect request, session, goal, capability selection/load, model decision, policy outcome, tool call, response composition, and final delivery. Use OpenTelemetry identifiers across services and export LLM-relevant spans to Langfuse.

### 13.2 Minimum dashboards

- business: started/completed/failed/handed-off goals and verified capability outcomes;
- quality: selection, clarification, correction, interruption/resume, and evaluation trend;
- safety/control: denials, confirmation, guardrail triggers, data masking, unauthorized attempts;
- engineering: latency by node, provider/tool errors, retries, checkpoints, deployment health;
- economics: tokens, model cost, tool cost if relevant, and cost per completed goal.

### 13.3 Production-readiness checklist

- service owner, on-call/support route, SLOs, alerts, dashboards, and runbooks;
- threat model, access review, secrets, scans, data classification, retention, and audit access;
- capacity/load test, dependency timeouts, circuit breakers, recovery, and rollback;
- model/prompt/capability pinning, feature flags, kill switch, and canary;
- evaluation baseline and post-deploy synthetic suite;
- business operations and human-handoff readiness.

## 14. Quarter-one repository structure

```text
conversational-ai-platform/
|-- src/conversational_ai/
|   |-- api/
|   |-- orchestration/
|   |-- conversation/
|   |-- goals/
|   |-- session/
|   |-- capabilities/          # registry, resolver, loader, runtime
|   |-- providers/openai/      # behind provider interface
|   |-- tools/
|   |-- policy/
|   |-- response/
|   |-- guardrails/
|   `-- observability/
|-- capabilities/
|   |-- funded-capability/
|   `-- registry-smoke-fixture/ # proves extensibility; not a production scope item
|-- specs/
|   |-- architecture/
|   |-- adr/
|   |-- features/funded-capability.md
|   `-- contracts/{runtime,capability,tools,events,response}/
|-- workflows/
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
|-- docs/{runbooks,onboarding,operations}/
`-- .gitlab-ci.yml
```

## 15. Development-time workflow in quarter one

Use the workflow on real funded work; do not build an elaborate autonomous software factory.

1. **Impact analysis:** identify affected specs, contracts, capabilities, policies, evals, code, and operations.
2. **Specification:** draft the feature and examples; humans approve business intent and controls.
3. **Implementation planning:** create small, traceable slices mapped to acceptance scenarios.
4. **Implementation:** agents may propose changes; engineers review and own them.
5. **Independent verification:** a separate reviewer/agent checks implementation against specs and governance.
6. **Release evidence:** assemble test/eval/security/policy results and version inventory.
7. **Promotion:** named humans approve according to risk; pipeline deploys immutable artifacts.

Quarter-one success is consistent artifact flow and traceability, not maximum agent autonomy.

## 16. Definition of done

### 16.1 Funded capability

- product owner signs off the funded scope and measurable outcome;
- required paths, errors, denials, disclosures, and handoffs meet acceptance scenarios;
- required enterprise actions are correct, idempotent, authorized, confirmed, and auditable;
- business and operations accept support and runbook arrangements.

### 16.2 Reusable spine

- the runtime has no hard-coded funded-capability routing;
- a second fixture capability registers, resolves, loads, and returns a contract-valid response without core changes;
- provider calls occur only behind the abstraction;
- all tools pass through the gateway and all responses through the composer/controls;
- one trace spans the complete turn; common dashboards and evaluation harness operate.

### 16.3 Delivery system

- specifications and governance are separate, linked, versioned, and consumed by checks;
- the paired Business-IT workflow produces a business-approved `CAPABILITY.md`, traced acceptance scenarios, and an implementation-ready candidate skill without requiring business users to operate developer tools;
- path-aware platform and capability lanes run in GitLab;
- risk-based test/evaluation/security/policy gates block unsafe promotion;
- release evidence identifies every runtime, capability, provider/model, prompt, policy, and dataset version;
- rollback and kill-switch procedures are exercised.

## 17. Scope and delivery scorecard

Review weekly with the sponsor.

| Category | Green signal | Escalation signal |
|---|---|---|
| Business decisions | Acceptance examples and policy decisions resolved within 24-48 hours | Unresolved scope/response/control decisions block build |
| Vertical slice | One tested end-to-end path remains working | Teams build layers without an integrated path |
| Capability | Funded outcomes converge against scenarios | New unfunded scenarios expand the boundary |
| Platform | Shared component is exercised by funded path and fixture | Framework work lacks a current consumer |
| Evaluation | Dataset and regression grow with features | Evaluation is postponed to final weeks |
| Integration | Contract tests/mocks isolate delays | External API instability stops all work |
| Governance | Controls have owner, code/check, and evidence | Policy exists only as prose or prompt text |
| Operations | Trace, dashboard, rollback evolve with the system | Production readiness is a closing-phase activity |

## 18. Sponsor decisions required in week one

1. Confirm the funded capability, users, production-readiness target, and excluded use cases.
2. Name the business capability owner and paired IT capability engineer, plus product/SME, risk/control, and release owners with decision SLAs.
3. Confirm required enterprise integrations, data classes, test data, and environment availability.
4. Confirm the initial inference path and approval to use OpenAI through the provider abstraction.
5. Approve the proposed capacity or explicitly accept the scope/timeline tradeoff.
6. Agree that new platform features require direct quarter-one justification.
7. Agree on the release fallback if external approvals or integrations miss the critical path.

## 19. Message to leadership

The quarter is not funding an isolated bot and it is not funding an unlimited platform program. It is funding one business outcome delivered through a deliberately reusable, governed conversational spine.

At quarter end, the team should be able to say:

> **We delivered the Funded Capability, proved the reusable path for the next capability, and established the specifications, governance, evaluation, observability, and release controls needed to scale responsibly.**
