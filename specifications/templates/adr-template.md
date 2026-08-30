---
apiVersion: nexus.platform/v1
kind: ArchitectureDecision
metadata:
  id: ADR-NNNN
  title: Decision title
  status: proposed
  owners: [Owning group]
  decisionDate: YYYY-MM-DD
  supersedes: []
enforcement:
  invariants:
    - id: INV-DOMAIN-NNN
      statement: A testable architectural invariant.
  features: []
  tests: []
---

# Decision title

## Context

What forces or constraints require a decision?

## Decision

What was decided?

## Alternatives considered

- Alternative and why it was not selected.

## Consequences

- Positive, negative, and operational consequences.

## Enforcement

How do features, contracts, tests, and promotion gates enforce the invariants?

## Supersession

Clarifications use normal Git edits. Create a new ADR only when the decision
changes, and link the replaced ADR through `metadata.supersedes`.
