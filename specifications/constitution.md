---
apiVersion: nexus.platform/v1
kind: PlatformConstitution
metadata:
  id: NEXUS-CONSTITUTION
  title: Nexus platform constitution
  status: ratified
  owners: [Agentic Conversation Platform]
  ratifiedDate: 2026-08-30
---

# Nexus platform constitution

## Purpose

Nexus provides conversationally adaptive, operationally governed member
assistance. Portable specifications express intent and required behavior; the
runtime enforces state, policy, authorization, validation, execution, audit,
and response boundaries.

## Principles

1. **Member objectives, platform goals:** A member expresses an objective. The
   platform may create one or more goals. A goal selects a skill, and a skill
   supplies an execution plan containing ordered steps.
2. **Model advises; platform decides:** Model output used for control flow is a
   typed recommendation. The platform validates and persists official state.
3. **Conversation is flexible; execution is governed:** Language understanding
   may adapt to context. Consequential execution remains deterministic,
   authorized, confirmed, idempotent, and auditable.
4. **Skills are bounded capabilities:** A skill can use only published platform
   operations, contracts, tools, and policy controls. A skill cannot introduce
   a hidden platform primitive.
5. **Grounded responses:** Informational answers come from approved sources or
   controlled templates, never unsupported model memory.
6. **Durable continuity:** Interruptions, corrections, restarts, catalog
   changes, and handoffs do not silently lose or replace active work.
7. **Least necessary data:** Prompts, state, tools, traces, and handoffs minimize
   sensitive member information.
8. **Evidence before promotion:** Acceptance behavior is traceable to tests or
   evaluations. Consequential changes require independent verification.

## Specification authority

When artifacts conflict, use this precedence:

1. This constitution.
2. Accepted ADRs.
3. Approved platform feature specifications and machine contracts.
4. Approved capability specifications.
5. Implementation plans.
6. Candidate skills and code.
7. Generated evidence and explanatory documentation.

Published runtime artifacts remain immutable evidence of what executed, but do
not override a newer approved source specification. Vendor-specific agent files
are adapters and cannot redefine this hierarchy.

Every material change updates the highest applicable source artifact. Agents do
not repair a mismatch only in generated code when the specification is wrong or
incomplete.

## Safety and governance

- Authentication is not blanket authorization; authorize each operation.
- Obtain fresh explicit confirmation immediately before a consequential action.
- A material correction invalidates earlier confirmation.
- Use idempotency and authoritative status checks for consequential retries.
- Keep unsupported work in a controlled lane and offer governed handoff where
  appropriate.
- Preserve last-known-good runtime behavior when new artifacts fail validation.
- Do not let the author of a consequential change be its sole approver.
- Browser and agent identities cannot bypass environment release controls.

## Quality gates

A change cannot be promoted unless:

- its specification is structurally valid and owned;
- impact analysis classifies platform and connector dependencies;
- acceptance IDs map to deterministic tests or approved evaluation rubrics;
- required platform, contract, connector, and tool versions are available;
- regression tests protect existing member behavior;
- release evidence identifies exact source and artifact digests;
- required independent and business approvals are recorded.

LLM judging may assess semantic quality such as clarity and conversational
naturalness. It is not the sole verifier for authorization, confirmation,
privacy, monetary execution, idempotency, or other safety invariants.

## Terminology

- **Member objective:** What the member is trying to accomplish.
- **Platform goal:** A durable outcome the platform advances for an objective.
- **Capability:** A business-owned behavior defined by `CAPABILITY.md`.
- **Skill:** A versioned executable implementation selected for a goal.
- **Execution plan:** The ordered steps supplied by the selected skill.
- **Tool:** A typed platform operation used by a plan step.
- **Contract:** A machine-readable boundary for tools, events, state, or runtime
  compatibility.

Do not introduce “job” as an additional business term unless a future ADR
defines a genuinely distinct independently scheduled, owned, and audited
runtime entity.
