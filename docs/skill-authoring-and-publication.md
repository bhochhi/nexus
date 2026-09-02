# Nexus skill architecture, authoring, and publication

This POC treats a skill as a business-owned, versioned capability while keeping
the LangGraph runtime stable. Business authors and the runtime share one
portable `SKILL.md` artifact; there is no second author-maintained JSON skill
representation.

This document defines the target flattened `nexus.skills/v3` authoring
standard. The compiler reads flattened v3 artifacts while retaining immutable
v1 and v2 compatibility. The implementation sequence and compatibility rules
are recorded in [`skill-schema-migration-plan.md`](skill-schema-migration-plan.md). New v3
skills should start from the copyable
[`SKILL.template.md`](../skills/templates/SKILL.template.md).

## Objective, skill, goal, and task model

These terms describe different layers and should not be used interchangeably:

| Term | Meaning | Lifetime |
| --- | --- | --- |
| member objective | The outcome expressed by the member, possibly spanning several capabilities. | conversation-specific |
| skill | An immutable, discoverable capability and its governed execution contract. | authored and versioned |
| goal | A platform-managed unit of outcome derived from a selected skill. | created at runtime |
| task | The durable execution instance for a goal, including inputs, progress, version, and artifact hash. | runtime state |

The standard authoring rule is **one skill means one goal**. Authors therefore
do not declare a second goal name. For a single-goal skill, the platform derives
the goal identity from `skill.name`:

```text
member objective -> selected skill -> goal named for the skill -> durable task
```

One member objective may still create several goals when it selects several
skills. For example, “check my balance, then transfer $200” creates one goal
from the balance skill and one from the internal-transfer skill.

The name `goals` is reserved for a possible future cohesive capability package
that genuinely exposes multiple independently executable outcomes. It is not a
way to enumerate RAG topics, utterance variants, workflow steps, or input
values. It is not implemented in v3 today: the compiler rejects any authored
`goals` field. If introduced later, every goal would need its own complete
input, governance, and execution contract; a list of labels sharing one
workflow would remain invalid. All active Nexus skills are single-goal.

## Three-tier skill architecture

Progressive disclosure is both a model-context rule and a runtime-loading rule.
The runtime may read or validate more data than the model sees. Loading an
artifact into the application process does not mean injecting the artifact into
the model prompt.

| Tier | Contents | Consumer | Loading rule |
| --- | --- | --- | --- |
| 1. Discovery | name, display name, description, and compact examples | turn-understanding model and deterministic fallback router | loaded for every active skill; keep small |
| 2. Activation | the selected skill's Markdown instructions plus its input schema and current task state | turn-understanding model | loaded only for the active or pending skill and bounded to 5,000 characters in this POC |
| 3. Execution | governance, tool allowlist, configuration, workflow, validators, confirmation rules, and tool results | policy engine and declarative executor | loaded by exact version and hash when a task is created or resumed; not automatically placed in model context |

Nexus currently performs discovery and initial input interpretation in one
semantic call, so the compact input schemas remain present in that bounded
request. After a task exists, the exact v2 Markdown body is supplied as
`active_skill_instructions`. A future two-call router could make the first turn
strictly metadata-only, but it would add latency and cost. The important current
boundary is that executable workflow and tool configuration never become
general model instructions.

### Tier 1: description and examples

The description is the authoritative capability boundary. It must say:

- what the skill accomplishes;
- when a member request should activate it;
- important nearby requests it does not support.

V3 makes `description` and `examples` first-class, flattened fields. There is no
`intent` wrapper and a single-goal skill does not repeat its name inside every
example:

```yaml
name: internal_transfer
display_name: make an internal transfer
description: Moves money between eligible accounts owned by the authenticated member. Use for requests to transfer, move, send, or put funds between those accounts; do not use for external-bank transfers or payments to another person.
examples:
  - Move $200 from savings 2003 to checking 1002.
  - Put fifty dollars in my other checking account.
```

Examples are positive semantic demonstrations, not exact phrases or a keyword
list. The member does not have to repeat an example exactly. Authors should use
two to eight short, diverse utterances that cover real paraphrases, omitted
product jargon, and common speech patterns. A long list wastes discovery
context and can over-bias routing toward superficial wording. Deterministic
fallback hints, when required, belong in a separate fallback configuration and
must not become the semantic definition of the skill. `acceptance` scenarios
are executable publication tests and are not a substitute for discovery
examples.

### Tier 2: activated conversational instructions

For v3, the Markdown body is model-facing after activation. It should contain
these headings:

- `When to use`: the detailed positive and negative boundary;
- `Inputs and interpretation`: the business meaning of every input, valid
  evidence, multi-input utterances, corrections, contextual references, and
  ambiguity rules;
- `Conversation behavior`: how to acknowledge, clarify, and avoid making the
  member repeat known information;
- `Safety and boundaries`: what remains grounded or deterministic and what the
  model must never claim or decide.

The body should not contain executable YAML, secrets, raw tool responses, or a
copy of the complete workflow. Tier 2 guides semantic interpretation and
natural conversation. JSON Schema still controls which inputs can enter task
state, and Tier 3 remains authoritative for validity and side effects.

### Tier 3: governed execution and tools

`implementation.tools` is the skill's runtime allowlist. Workflow `call_tool`
steps must name a tool from that list, and publication verifies that the tool
and action are installed. In the current architecture the LLM does not invoke
these tools directly; the declarative executor calls them after policy and
workflow checks.

That is why tool names belong in Tier 3, not Tier 2. Tier 2 may explain the
member-visible purpose of a lookup—for example, “eligible accounts are checked
before asking the member to choose”—but it must not teach the model to simulate
the tool or trust an unvalidated result.

If a future archetype allows model-selected tool calls, the same Tier 3
allowlist remains authoritative. After activation, the platform would expose
only policy-approved tool/action schemas for that skill to the provider. Tool
descriptions shown to the model would be a filtered execution view, not a
second author-maintained list in the Markdown body.

## Preflight checks before input collection

Some capabilities require a safe lookup before the runtime knows what inputs to
request. This is already expressible by putting a read-only `call_tool` and a
`validate` step before the first `collect` step. Guided balance, for example,
retrieves eligible accounts before deciding whether account type or account
number must be elicited.

Preflight is distinct from discovery:

```text
semantic request
      |
      v
ranked skill candidate
      |
      v
policy gate + safe read-only preflight
      |
      +---- eligible ------> collect only unresolved inputs
      |
      +---- unavailable ---> explain governed failure or alternate channel
      |
      +---- not applicable -> optionally consider the next ranked candidate
```

The platform should not call preflight tools for every skill in the catalog.
It first identifies a semantic candidate, then loads that exact artifact and
runs its governed preflight. Preflight results have different meanings:

- `eligible`: continue the selected workflow;
- `unavailable`: the capability is understood but cannot currently execute;
- `not applicable`: evidence proves the candidate does not apply, so a planner
  may consider the next already-ranked skill candidate;
- `denied` or `error`: fail safely; never disguise policy denial or a dependency
  failure as a different goal.

The current POC supports read-only calls and validation before collection, but
does not yet implement a general `not applicable -> try next ranked skill`
transition. Authors must therefore use an explicit safe failure response today.
The generic candidate-rejection transition is a platform enhancement, not
something an individual skill should emulate with prompting.

## Flattened v3 authoring schema

The primary skill identity is intentionally visible at the root. `name` and
`version` are not miscellaneous metadata: together with the artifact hash they
identify the immutable capability selected by routing and pinned by durable
tasks. `schema_version` identifies the parser contract, while `version`
identifies a release of this particular skill.

```yaml
---
schema_version: nexus.skills/v3
name: internal_transfer
version: 3.0.0

display_name: make an internal transfer
description: >
  Moves money between eligible accounts owned by the authenticated member.
  Use for requests to transfer, move, send, or put funds between those
  accounts; do not use for external-bank transfers or payments to another
  person.
examples:
  - Transfer $50 from checking to savings.
  - Move $200 from savings 2003 to checking 1002.

metadata:
  owner: money-movement-team
  domain: banking
  category: money-movement
  tags: [authenticated, transactional]

input_schema:
  type: object
  required: [source_account, destination_account, amount]
  properties: {}

behavior:
  archetype: deterministic_workflow
  interaction: guided
  execution: workflow
  lifecycle: synchronous

governance:
  risk_tier: consequential
  auth_required: true
  confirmation_required: true
  failure_behavior: safe_reject

implementation:
  tools: [mock_accounts, mock_internal_transfer]
  workflow: {}

acceptance: []
---
```

| Section | Required | Tier | Purpose |
| --- | --- | --- | --- |
| `schema_version` | yes | compiler | Skill schema contract. New work uses `nexus.skills/v3`; this is independent of the skill release. |
| `name` | yes | identity/1 | Stable lower-snake-case machine identity used for routing, storage, and the default goal identity. |
| `version` | yes | identity/3 | Immutable semantic version of this skill release. |
| `display_name` | yes | 1/UI | Short member-facing capability phrase. |
| `description` | yes | 1 | Capability, activation conditions, and meaningful exclusions; maximum 1,024 characters. |
| `examples` | yes | 1 | Two to eight positive member utterances, each at most 200 characters. |
| `metadata` | yes | catalog | Accountable owner plus optional business domain, category, and tags. Metadata must not control runtime behavior. |
| `input_schema` | yes for a single-goal skill | 1/2 | Allowed task inputs, requiredness, types, constraints, and semantic field descriptions. |
| `fallback` | optional | fallback | Conservative, declarative offline routing or extraction hints; semantic providers remain preferred. |
| `goals` | no (reserved) | future | Rejected by the current v3 compiler. A future extension would require complete per-goal contracts. |
| `behavior` | yes | catalog/3 | Authoring archetype plus independent interaction, execution, and lifecycle dimensions. |
| `governance` | yes | 3 | Risk, authentication, authorization, confirmation, disclosure, and failure behavior. |
| `implementation.tools` | yes, may be empty | 3 | Runtime tool allowlist; it is not an automatic LLM tool list. |
| `implementation.config` | optional | 3 | Versioned, non-secret business configuration. |
| `implementation.workflow` or recipe | yes | 3 | Safe declarative execution using allowlisted operations and tools. |
| `implementation.response_template` | yes | 3 | Grounded fallback or deterministic response shape. |
| `acceptance` | yes | publication | At least one deterministic routing and contract scenario. |
| Markdown body | yes | 2 | Activated conversational instructions using the four standard headings. |

Schema field descriptions are part of semantic slot interpretation. Describe
business meaning and ambiguity, not merely data type. For example, “the account
the money leaves” is useful; “a string containing an account” is not.

### Metadata is classification, not behavior

`metadata.owner` identifies the accountable team. It is not interchangeable
with a business domain or category. If the organization uses COSA or another
enterprise taxonomy, represent it explicitly as `metadata.cosa`, `domain`, or
`category` instead of overloading `owner`. Metadata may drive catalog browsing,
RBAC, approval, and reporting, but it must never select workflows, tools, slot
names, or policy behavior.

### Reserved multi-goal extension

The required current form omits `goals`. The compiler derives a single
goal whose stable name and display name are the skill's `name` and
`display_name`. This removes duplicate identifiers from model output,
acceptance scenarios, task creation, and examples.

If a future schema version supports several goals, its root discovery fields
would describe the cohesive capability package and each goal would own a
complete contract. The following is conceptual and does not compile today:

```yaml
name: account_information
display_name: view account information
description: Retrieves account balances, recent transactions, or account details.
examples:
  - Show my checking balance.
  - List my recent savings transactions.

goals:
  - name: check_balance
    display_name: check an account balance
    description: Retrieves the available balance for a selected account.
    examples:
      - How much do I have in checking?
    input_schema: {}
    behavior: {}
    governance: {}
    implementation: {}

  - name: list_recent_transactions
    display_name: view recent transactions
    description: Lists recent transactions for a selected account.
    examples:
      - Show my latest savings transactions.
    input_schema: {}
    behavior: {}
    governance: {}
    implementation: {}
```

The single-goal root execution fields and `goals` are mutually exclusive. This
avoids implicit inheritance and makes the policy and workflow selected for each
goal auditable. The first v3 implementation may reserve this shape behind a
validation feature flag, but it must not accept the old shallow form where
several goal labels silently share one execution contract.

## Standard flow

```text
member utterance
      |
      v
Tier 1 catalog discovery (description + examples)
      |
      v
ranked skill candidate(s)
      |
      v
load exact versioned artifact and Tier 2 instructions
      |
      v
derive one goal per selected single-goal skill
      |
      v
policy / optional safe preflight
      |
      v
LLM maps language to schema inputs and corrections
      |
      v
workflow elicits only unresolved or ambiguous inputs
      |
      v
Tier 3 validation / review / confirmation / tool execution
      |
      v
grounded response and durable outcome
```

## Publication and call flow

```text
authoring tool / Git
        |
        v
 candidate SKILL.md
        |
        | validate schema, acceptance, governance, tool dependencies
        v
 immutable versioned SKILL.md ------> active.yaml routing index
                                           |
                              catalog poll / future event
                                           |
                                           v
member utterance -> semantic turn understanding -> routing metadata
                         |                            |
              schema-declared slot updates           v
                         |                    exact artifact
                         +------> durable task <------+
                                      |
                              generic executor
```

1. `SKILL.md` contains YAML frontmatter for machine-readable behavior and a
   Markdown body for business documentation.
2. The compiler normalizes it in memory to the small governed workflow
   contract. The authored source remains the immutable artifact.
3. Publication validates structure, deterministic acceptance routing, expected
   outcomes, confirmation rules, and installed tool/action dependencies.
4. The artifact is stored as `<name>/<version>/SKILL.md`; its SHA-256 content
   hash is recorded in the active index. Different content cannot overwrite the
   same name/version.
5. One small active index contains only routing metadata and the selected
   artifact reference. Updating this file is atomic.
6. Running assistants poll the index and route new work to the new version
   without restarting or rebuilding the LangGraph.
7. The full artifact is loaded only after skill selection. A durable task pins
   its original version and hash, so a clarification, pause, restart, or resume
   cannot silently switch workflow behavior.
8. Publication, activation, rollback, and deactivation append timestamped,
   actor-attributed events containing the exact version, hash, and catalog
   revision to `catalog-events.yaml`.

At runtime the active skill's JSON input schema is also the contract for semantic
slot interpretation. The provider may understand several fields or a correction
from one natural utterance, but only schema-declared, sufficiently confident
values enter durable task state. Tools and workflow validators remain the
authority for account resolution, value validity, policy, confirmation, and
execution. This separation keeps language flexible without making the workflow
probabilistic.

For this local POC the artifact store is `skills/catalog/<name>/<version>/` and
the routing index is `skills/catalog/active.yaml`. A production catalog would
put the same artifacts and pointers behind an authenticated publication API and
durable object store, then notify runtimes through an event or
cache-invalidation channel.

## One authoring file, not four required files

The frontmatter groups the information an authoring UI would collect:

- root identity: schema version, stable skill name, and immutable skill version;
- root discovery: member-facing display name, description, and first-class
  examples;
- `metadata`: accountable owner plus optional domain, category, and tags;
- root input contract and optional conservative fallback hints;
- `behavior`: an authoring archetype plus independent interaction, execution,
  and lifecycle dimensions;
- `governance`: risk, authentication, authorization, confirmation, disclosure,
  and failure behavior;
- `implementation`: approved tools, configuration, response design, and an
  optional workflow;
- `acceptance`: member utterances and expected skill, outcome, and confirmation
  behavior. A goal expectation is needed only for the optional multi-goal form.

For v3, the Markdown body is the activated model instruction surface. It
explains purpose, input semantics, conversation behavior, and safety boundaries
in business language.
Acceptance scenarios live in the same file for the POC; a future authoring tool
can render them as form fields instead of exposing YAML.

Simple skills do not need authors to write a workflow. `static_response`,
`tool_response`, `guided_selection`, and `navigation` recipes compile to the
safe shared operation set. Only a journey needing precise ordered controls—such
as internal transfer—authors a workflow inline. More reusable recipes can be
added to the compiler without changing the catalog or runtime contract.

See `skills/available/online_id_recovery/SKILL.md` for the navigation example.

## Archetypes are presets, not a closed capability taxonomy

The built-in presets remain useful authoring shortcuts:

- `knowledge`
- `guided_resolution`
- `deterministic_workflow`
- `navigation`
- `human_handoff`

Every preset uses the same v3 envelope and Tier 2 Markdown headings. Only the
Tier 3 recipe changes:

| Archetype | Typical implementation | Input/preflight pattern | Control boundary |
| --- | --- | --- | --- |
| `knowledge` | `tool_response` or lookup workflow | complete question, then approved retrieval | answer only from grounded sources |
| `guided_resolution` | `guided_selection` or workflow | read-only lookup may precede selection and collection | runtime resolves choices and validates returned data |
| `deterministic_workflow` | explicit ordered workflow | collect any unresolved inputs; preflight may occur before or between collection steps | runtime owns validation, review, confirmation, idempotency, and side effects |
| `navigation` | `navigation` recipe | collect only parameters required to build an approved destination | runtime owns destination allowlist and navigation action |
| `human_handoff` | handoff workflow | collect or derive minimized reason and queue | runtime owns consent, minimization, queue validation, and case creation |

Start from [`skills/templates/SKILL.template.md`](../skills/templates/SKILL.template.md),
then replace its explicit workflow with the smallest recipe supported by the
chosen archetype. The four active v2 examples demonstrate knowledge, guided
resolution, deterministic workflow, and human handoff; the staged online-ID
recovery skill demonstrates navigation.

They are not business intents such as “balance” or “transfer,” and the runtime
does not reject a new archetype name. Behavior is also described on separate
axes:

| Axis | Current examples | Why it is separate |
| --- | --- | --- |
| interaction | `direct`, `guided` | Whether the member receives one response or participates in slot collection/clarification. |
| execution | `response`, `knowledge_retrieval`, `tool_query`, `navigation`, `workflow`, `handoff` | The broad execution mechanism. |
| lifecycle | `synchronous` | Duration/continuation model; long-running and event-driven work would require future platform lifecycle support. |
| risk tier | `informational`, `navigation`, `read_only`, `consequential`, `handoff` | Deterministic governance and policy handling, independent of the conversation shape. |

A custom archetype can publish when it compiles to the existing allowlisted
operations. A genuinely new control primitive or lifecycle is a platform
extension; a new business capability composed from existing primitives is not.

## Commands

Validate without changing the catalog:

```bash
member-assistant-skills validate skills/available/online_id_recovery/SKILL.md
```

Publish and activate atomically:

```bash
member-assistant-skills publish skills/available/online_id_recovery/SKILL.md
```

Stage an artifact without routing new work to it:

```bash
member-assistant-skills publish skills/available/online_id_recovery/SKILL.md --staged
```

Inspect the active metadata and all immutable versions:

```bash
member-assistant-skills active
member-assistant-skills versions --name online_id_recovery
```

Activate a prior version (rollback) using values returned by `versions`:

```bash
member-assistant-skills activate online_id_recovery 3.0.0 <artifact-hash>
```

Deactivate new routing while retaining immutable versions for audit and
in-flight tasks:

```bash
member-assistant-skills deactivate online_id_recovery
```

Use `--catalog PATH` before the subcommand to target a different registry. All
commands read the same project `.env` and `~/.secrets/dev.env` configuration as
the chat CLI. The runtime never reads `.env.example`.

## What a production platform still needs

The contracts in this POC establish the boundary, but automatic enterprise
publication also needs:

- an authenticated authoring and catalog API with owner/approver RBAC;
- draft, review, approval, staging, canary, activation, and rollback states;
- artifact signing, provenance, malware/content scanning, and an append-only
  publication audit;
- a schema/compatibility registry for production tool inputs and outputs;
- richer offline evaluations, red-team suites, policy approval, and regression
  gates before activation;
- event-driven distribution, cache coherence, health checks, and fleet-level
  rollout status;
- version retention rules that preserve artifacts referenced by durable tasks;
- monitoring by skill version, outcome, latency, error, abandonment, and skill
  gap, with automatic rollback thresholds where appropriate.

The local file publisher deliberately represents these control points without
pretending to be that production control plane.
