# Flattened skill schema migration plan

## Outcome

Move Nexus from the nested v1/v2 skill envelope to the flattened
`nexus.skills/v3` contract while preserving immutable published artifacts and
in-flight tasks. The standard authoring model is one skill to one derived goal.
Multi-goal authoring is reserved for a future schema and is explicitly rejected
by the current v3 compiler.

The platform must remain skill-agnostic. Adding a business capability composed
from existing platform primitives must require a new skill artifact and tools,
not changes to the conversation runtime, provider adapters, policy engine, or
declarative executor.

## Architectural invariants

1. The model may interpret language, rank skills, extract several inputs, and
   correct prior inputs. It never validates business data or authorizes a side
   effect.
2. The catalog supplies discovery and execution contracts. Platform code must
   not branch on a skill name, business input name, account type, product, or
   sample value.
3. Platform code may understand stable platform primitives such as workflow
   operations, schema constraints, lifecycle states, risk tiers, confirmation,
   and tool contracts.
4. A selected single-goal skill produces one runtime goal whose stable name is
   the skill name. The provider does not return a duplicate goal identifier.
5. A member objective may select several skills. The planner creates and orders
   one durable goal/task for each accepted skill match.
6. Durable tasks continue to pin skill name, skill version, and artifact hash.
   Schema migration never changes the definition used by in-flight work.
7. The optional multi-goal form must not reuse the old shallow goal-label list.
   Each goal requires an independently auditable input, governance, and
   implementation contract.

## Phase 1: author the v3 skill artifacts

Draft new immutable versions of the four active example skills without
activating them:

- `approved_knowledge`: keep one query input; overdraft, deposit insurance, and
  coverage remain RAG topics represented by examples, not goals.
- `guided_balance`: keep one account-balance outcome and schema-driven account
  selection semantics.
- `internal_transfer`: keep one transfer outcome; preserve source,
  destination, amount, resolution, review, and confirmation behavior entirely
  in the artifact and tool contracts.
- `live_agent_handoff`: keep one handoff outcome; declare how current task
  context maps into handoff inputs rather than having runtime know its field
  names.

For each artifact:

- move `name` and `version` to the root;
- replace `apiVersion` with `schema_version` and remove `kind`;
- move `description`, `display_name`, `examples`, and `input_schema` to the root;
- convert examples to plain strings;
- remove the single-item `goals` declaration and deterministic goal keywords;
- separate `metadata.owner` from domain/category classification;
- move conservative offline hints under `fallback`;
- remove the duplicate expected goal from single-goal acceptance scenarios;
- retain Tier 2 Markdown instructions and Tier 3 governed execution behavior.

Do not update `active.yaml` until the compiler, catalog, and tests accept v3.

## Phase 2: compiler, validation, and publication

Update `src/member_assistant/skill_authoring.py` and
`src/member_assistant/catalog.py` to:

1. Recognize `schema_version: nexus.skills/v3`.
2. Parse root identity and discovery fields.
3. Validate two to eight unique string examples and the 1,024-character
   description boundary.
4. Normalize a single-goal v3 artifact into one internal goal contract whose
   name is the skill name and whose display name is the skill display name.
5. Reject a single-goal artifact that also declares `goals`.
6. Either reject the optional multi-goal form as not yet enabled or compile
   every goal as a complete contract. Never accept labels that silently share
   one workflow.
7. Preserve v1/v2 readers so immutable artifacts and pinned tasks remain
   loadable.
8. Validate owner separately from domain, category, and optional COSA metadata.
9. Keep publication identity and immutability based on skill name, skill
   version, and artifact hash.
10. Update acceptance validation so `expect.skill` is sufficient for the
    single-goal form; require `expect.goal` only for a multi-goal artifact.

The compiler may use a normalized internal representation, but that structure
is generated from `SKILL.md`; it is not a second author-maintained contract.

## Phase 3: semantic discovery contract

Replace the duplicate skill-plus-goal provider contract with a skill match:

```json
{
  "skill_name": "internal_transfer",
  "confidence": 0.97,
  "inputs": {
    "source_account": "checking 1001",
    "destination_account": "savings",
    "amount": "200.00"
  }
}
```

Required changes:

- replace or evolve `GoalMatch` into `SkillMatch` for Tier 1 discovery;
- send `name`, `display_name`, `description`, `examples`, and the bounded input
  schema for each active skill;
- remove the instruction requiring the model to return a declared goal name;
- allow several skill matches only when the member independently requests
  several outcomes or the request is genuinely ambiguous;
- update OpenAI, Bedrock, fallback, and deterministic adapters to return the
  same provider-neutral structure;
- make deterministic routing consume declared `fallback.routing_hints`, not
  goal keywords;
- keep active-task slot updates separate from new skill matches so a slot answer
  is not mistaken for a new objective.

Shared provider instructions must be schema-driven. The current prompt's
special treatment of an input named `amount` should become a declared schema
format or normalization rule, such as `format: currency-amount`. Provider code
must not know the fields used by internal transfer.

## Phase 4: planning and durable runtime state

Update the runtime without adding skill-specific branches:

1. Rank accepted `SkillMatch` values.
2. Derive a runtime goal from each selected single-goal skill.
3. Create a durable task pinned to name, version, and artifact hash.
4. Preserve multi-skill objective planning, queuing, interruption, resume, and
   clarification using skill identity plus task identity.
5. Use `display_name` for member-facing transitions and capability lists.
6. Keep a natural-language `objective_summary` when useful for planning or
   handoff; do not treat that summary as an authored routing identifier.
7. Remove the assumption that every route exposes `supported_goals[0]`.
8. Rename internal helpers when it improves clarity—for example,
   `_normalize_skill_matches` and `_task_from_skill_match`—while allowing the
   runtime `GoalState` concept to remain.

For future multi-goal support, discovery first selects the capability package;
activation then selects one or more complete goal contracts inside that pinned
artifact. This is an extension of the same task model, not a reason to keep a
duplicate single-goal field today.

## Phase 5: remove business semantics from platform primitives

The following current behavior must move out of shared platform code:

- `src/member_assistant/skills/declarative.py` contains checking/savings token
  recognition and invokes `mock_accounts` while constructing an ambiguity
  response. Replace it with declarative candidate filtering, match fields,
  choice rendering, and workflow-supplied collections. A generic executor must
  not know account types or tool names.
- `src/member_assistant/providers/turn_contract.py` contains money-specific
  number normalization. Express normalization through schema annotations or a
  registered platform data format whose behavior is selected by the artifact.
- `src/member_assistant/providers/deterministic.py` contains account-number and
  archetype-specific slot assumptions. Limit offline behavior to declared
  fallback rules and the pending field contract.
- `src/member_assistant/runtime.py` supplies handoff fields such as
  `active_goal` and `completed_steps` by name. Expose safe task context through
  generic `$context` values and let the handoff workflow map those values into
  its own inputs.

This does not mean the platform is unaware of all semantics. Confirmation,
authorization, risk ordering, workflow operations, schemas, and tool contracts
are deliberate platform control primitives. The boundary is that platform code
understands *how to control work*, not *which business skill is running*.

## Phase 6: tests and compatibility gates

Add or update tests for:

- canonical flattened v3 compilation and validation;
- v1/v2 immutable compatibility and exact-version task resume;
- derived single-goal identity without provider-supplied goal names;
- several selected skills from one member objective;
- semantic extraction of several inputs and correction of any declared input;
- examples as positive semantic demonstrations rather than exact phrases;
- generic candidate ambiguity and selection with non-account field names;
- schema-selected normalization with non-transfer field names;
- declarative handoff context mapping without runtime field knowledge;
- publication, activation, rollback, and deactivation of v3 artifacts;
- rejection of a shallow or partially defined multi-goal artifact.

Add one deliberately unrelated test skill—for example, a read-only appointment
lookup using arbitrary field and tool names. It must route, collect, validate,
execute, resume, and report telemetry without any platform-code change. This is
the strongest regression test for skill agnosticism.

## Phase 7: rollout

1. Publish the four v3 skill versions as staged artifacts.
2. Run catalog, provider, conversation, declarative workflow, restart, and
   observability suites.
3. Exercise the known transcripts: compound balance/transfer objectives,
   complete first-turn transfer inputs, ambiguous same-type accounts, account
   suffix versus amount, correction, greeting, and capability discovery.
4. Activate v3 versions together in the demo catalog.
5. Verify that an in-flight v1/v2 task resumes its pinned artifact while new
   conversations route to v3.
6. Retain the previous active index values for immediate rollback.
7. Refresh Graphify after each implementation phase so architectural queries
   reflect the new contracts.

## Definition of done

- Every active example uses the flattened v3 schema and omits `goals`.
- Provider discovery returns skills, not duplicate skill/goal pairs.
- The runtime derives one goal/task per selected single-goal skill.
- No shared platform module references an active skill name, its business slot
  names, account types, or mock tool names.
- An unrelated declarative skill works without modifying shared platform code.
- Multiple skills can still be planned from one member objective.
- Optional multi-goal artifacts are either fully supported with per-goal
  contracts or explicitly rejected; shallow shared-workflow goals are never
  accepted.
- Legacy immutable artifacts and pinned tasks remain loadable and resumable.
