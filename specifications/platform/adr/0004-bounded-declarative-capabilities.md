---
apiVersion: nexus.platform/v1
kind: ArchitectureDecision
metadata: {id: ADR-0004, title: Capabilities execute through a bounded declarative runtime surface, status: accepted, owners: [Agentic Conversation Platform], decisionDate: 2026-09-02, supersedes: []}
enforcement:
  invariants: [{id: INV-BOUNDED-CAPABILITY-001, statement: A capability cannot introduce an undeclared platform operation, tool action, policy, or lifecycle.}]
  features: [PF-CAPABILITY-AUTHORING-DELIVERY]
  tests: [tests/test_declarative_skills.py, tests/test_skill_authoring.py]
---
# Capabilities execute through a bounded declarative runtime surface
## Context
Business capabilities must evolve without accumulating capability-name branches or arbitrary executable code in the shared orchestrator.
## Decision
Publish immutable capability artifacts that declare discovery, inputs, governance, tools, and plans using a versioned platform surface. Unsupported primitives require a connector or platform extension before activation.
## Alternatives considered
- Add a Python executor for each capability. Rejected because it couples catalog growth to runtime deployment.
- Treat skill prose as unrestricted executable instruction. Rejected because policy, compatibility, and failure behavior would be implicit.
## Consequences
The runtime surface and compiler become governed contracts; some new capabilities must wait for an explicit platform extension.
## Enforcement
`PFND-CAPABILITY-REGISTRY`, `PFND-GOVERNED-EXECUTION`, and the capability-runtime contract validate the boundary.
## Supersession
Changes to the declarative boundary require a new ADR and compatibility plan.
