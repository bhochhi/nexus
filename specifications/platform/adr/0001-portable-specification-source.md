---
apiVersion: nexus.platform/v1
kind: ArchitectureDecision
metadata:
  id: ADR-0001
  title: Portable specifications are the engineering source of truth
  status: accepted
  owners: [Agentic Conversation Platform]
  decisionDate: 2026-08-30
  supersedes: []
enforcement:
  invariants:
    - id: INV-PORTABLE-SOURCE-001
      statement: Vendor adapters must not redefine platform or capability behavior.
  features: [PF-CONVERSATION-LIFECYCLE]
  tests: [tests/test_spec_workflow.py]
---

# Portable specifications are the engineering source of truth

## Context

Several development agents must implement the same platform and business
behavior without creating vendor-specific sources of truth.

## Decision

Use repository-owned, portable specifications for platform behavior, tool and
event contracts, and the development lifecycle. Codex, GitHub Copilot, and
Claude Code consume thin instructions that point to this material; none owns a
parallel workflow or behavioral specification.

Business capabilities continue to use immutable, versioned `SKILL.md`
artifacts and their existing publication controls. The member-assistant runtime
continues to select a skill and execute its governed plan; this workflow does
not alter that path.

## Consequences

Every consequential change requires independent verification and recorded
release evidence before promotion. An author may prepare a specification,
implementation, or evidence, but may not approve their own consequential
change. Vendor adapters contain only navigation and stage-announcement guidance.

## Alternatives considered

- Maintain a complete workflow for each agent vendor. Rejected because the
  implementations would drift.
- Keep all requirements in runtime skill artifacts. Rejected because platform
  behavior and architectural decisions have a wider scope than one skill.

## Enforcement

`INV-PORTABLE-SOURCE-001` is enforced structurally by the portable specification
validator and behaviorally by the linked platform feature acceptance criteria.

## Supersession

Clarifications may edit this file through Git. A new ADR is required only when
the architectural decision changes; that ADR will list `ADR-0001` in
`metadata.supersedes`.
