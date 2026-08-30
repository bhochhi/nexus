---
name: nexus-implementation
description: Implement an approved Nexus specification and plan across platform code, connectors, capability packages, candidate skills, tests, and documentation while preserving unrelated runtime behavior. Use when validated intent and impact are already understood.
---

# Nexus implementation

Announce `Workflow stage: implementation`.

Implement against stable acceptance IDs. Change source specifications and their
implementations together when a discovered requirement is clarified; return to
analysis when the requirement materially changes.

For capability work:

- keep `CAPABILITY.md` business-readable;
- use the closest archetype template;
- trace every capability acceptance ID in candidate `SKILL.md` metadata;
- keep executable acceptance scenarios deterministic;
- use only declared tools and supported workflow operations;
- create a new candidate version rather than editing a published catalog copy;
- preserve the active runtime unless publication and activation are explicitly
  in scope.

For connector or platform work, update the relevant machine contract and
feature specification, then add tests that keep them synchronized with code.
Run focused tests during implementation and the proportionate regression suite
before handoff. Do not mark implementation as independently approved.
