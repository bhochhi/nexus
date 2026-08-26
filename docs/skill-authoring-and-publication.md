# Nexus Skill v1: authoring and publication

This POC treats a skill as a business-owned, versioned capability while keeping
the LangGraph runtime stable. Business authors and the runtime share one
portable `SKILL.md` artifact; there is no second JSON skill representation.

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
member utterance -> routing metadata -> exact artifact -> generic executor
                                             |
                                  task stores version + hash
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
7. The full artifact is loaded only after goal selection. A durable task pins
   its original version and hash, so a clarification, pause, restart, or resume
   cannot silently switch workflow behavior.
8. Publication, activation, rollback, and deactivation append timestamped,
   actor-attributed events containing the exact version, hash, and catalog
   revision to `catalog-events.yaml`.

For this local POC the artifact store is `skills/catalog/<name>/<version>/` and
the routing index is `skills/catalog/active.yaml`. A production catalog would
put the same artifacts and pointers behind an authenticated publication API and
durable object store, then notify runtimes through an event or
cache-invalidation channel.

## One authoring file, not four required files

The frontmatter groups the information an authoring UI would collect:

- `metadata`: stable name, immutable semantic version, accountable owner;
- `intent`: description, goals, examples/keywords, input contract and optional
  extraction hints;
- `behavior`: an authoring archetype plus independent interaction, execution,
  and lifecycle dimensions;
- `governance`: risk, authentication, authorization, confirmation, disclosure,
  and failure behavior;
- `implementation`: approved tools, configuration, response design, and an
  optional workflow;
- `acceptance`: member utterances and expected skill, goal, outcome, and
  confirmation behavior.

The Markdown body explains purpose, policy, and examples in business language.
Acceptance scenarios live in the same file for the POC; a future authoring tool
can render them as form fields instead of exposing YAML.

Simple skills do not need authors to write a workflow. `static_response`,
`tool_response`, `guided_selection`, and `navigation` recipes compile to the
safe shared operation set. Only a journey needing precise ordered controls—such
as internal transfer—authors a workflow inline. More reusable recipes can be
added to the compiler without changing the catalog or runtime contract.

See `skills/available/online_id/SKILL.md` for the navigation example.

## Archetypes are presets, not a closed capability taxonomy

The built-in presets remain useful authoring shortcuts:

- `knowledge`
- `guided_resolution`
- `deterministic_workflow`
- `navigation`
- `human_handoff`

They are not business intents such as “balance” or “transfer,” and the runtime
does not reject a new archetype name. Behavior is also described on separate
axes:

| Axis | Current examples | Why it is separate |
| --- | --- | --- |
| interaction | `direct`, `guided` | Whether the member receives one response or participates in slot collection/clarification. |
| execution | `response`, `knowledge_retrieval`, `tool_query`, `navigation`, `workflow`, `handoff` | The broad execution mechanism. |
| lifecycle | `synchronous` | Duration/continuation model; long-running and event-driven work would require future platform lifecycle support. |
| risk tier | `informational`, `navigation`, `read_only`, `consequential`, `handoff` | Deterministic governance and policy handling, independent of the conversation shape. |

A custom archetype can publish today when it compiles to the existing allowlisted
operations. A genuinely new control primitive or lifecycle is a platform
extension; a new business capability composed from existing primitives is not.

## Commands

Validate without changing the catalog:

```bash
member-assistant-skills validate skills/available/online_id/SKILL.md
```

Publish and activate atomically:

```bash
member-assistant-skills publish skills/available/online_id/SKILL.md
```

Stage an artifact without routing new work to it:

```bash
member-assistant-skills publish skills/available/online_id/SKILL.md --staged
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
