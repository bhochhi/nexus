---
name: nexus-independent-verification
description: Independently verify a Nexus change against its constitution, specifications, acceptance criteria, contracts, tests, and risk controls. Use for review after implementation, especially for consequential capabilities and platform primitives.
---

# Nexus independent verification

Announce `Workflow stage: independent_verification`.

Begin from the source specifications and acceptance IDs, not from the author's
summary. Inspect the implementation diff, candidate artifact, contracts, tests,
and runtime evidence. Reproduce validation and relevant tests in a clean or
isolated environment where practical.

Check:

- behavior satisfies each acceptance criterion and stated edge case;
- impact classification did not omit a connector or platform extension;
- consequential confirmation, authorization, idempotency, privacy, and status
  handling remain deterministic;
- existing capability behavior and durable state remain compatible;
- candidate skill dependencies match the deployed capability surface;
- failures retain controlled and last-known-good behavior;
- evidence identifies the exact source and artifact content.

An author may run these checks diagnostically but cannot be the sole independent
approver of their own consequential change. Report concrete failures and do not
approve based only on an LLM judge or prose review.
