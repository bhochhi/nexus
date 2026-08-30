---
apiVersion: nexus.workflow/v1
kind: ImpactAnalysis
metadata:
  changeId: CHANGE-NNN
  title: Change title
  status: draft
classification:
  primary: capability-only
  rationale: Why existing platform behavior is or is not sufficient.
---

# Change title

## Requested outcome

Describe the business or platform outcome without prescribing implementation.

## Relevant specifications

- Constitution principles:
- ADRs:
- Platform features:
- Capability specifications:
- Tool, event, state, and runtime contracts:

## Platform capability-surface comparison

- Required interaction mode:
- Required execution mode:
- Required lifecycle:
- Required workflow operations:
- Required validation and policy controls:
- Required tools and connector operations:
- Required state and events:
- Minimum runtime API version:

## Classification

Choose one primary classification:

- **Capability-only:** existing platform operations and contracts are sufficient.
- **Connector extension:** a new integration binding or tool operation is needed.
- **Platform extension:** a new cross-cutting behavior or primitive is needed.

Explain why the other classifications do not apply.

## Affected artifacts

- Specifications:
- Contracts:
- Capability packages:
- Platform code:
- Connector code:
- Tests and evaluations:
- Documentation:

## Dependency and release order

List platform, connector, and capability releases in the order they must become
available. Identify compatibility gates and rollback boundaries.

## Acceptance and verification impact

Map new or changed acceptance IDs to deterministic tests, evaluation rubrics,
and the required independent verifier.

## Risks and open questions

- Security, privacy, policy, compatibility, operational, and migration risks.
