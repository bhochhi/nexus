---
apiVersion: nexus.platform/v1
kind: ArchitectureDecision
metadata: {id: ADR-0003, title: Model output is advisory and platform decisions are authoritative, status: accepted, owners: [Agentic Conversation Platform], decisionDate: 2026-09-02, supersedes: []}
enforcement:
  invariants: [{id: INV-ADVISORY-MODEL-001, statement: Only validated platform decisions may mutate durable conversation or task state.}]
  features: [PF-CONVERSATION-LIFECYCLE]
  tests: [tests/test_scenarios.py, tests/test_providers.py]
---
# Model output is advisory and platform decisions are authoritative
## Context
Natural-language understanding benefits from probabilistic models, while authorization, execution, and durable continuity require deterministic control.
## Decision
Providers return typed analysis and optional response drafts. The platform validates them against state, catalog, schemas, policy, and allowed decisions before persisting or executing anything.
## Alternatives considered
- Let a model directly mutate state or call tools. Rejected because behavior would be provider-dependent and difficult to audit.
- Use only deterministic intent rules. Rejected because they do not provide the required conversational flexibility.
## Consequences
Provider contracts stay replaceable; the platform owns more explicit reconciliation, decision, and failure logic.
## Enforcement
Foundations `PFND-CONVERSATION-ORCHESTRATION`, `PFND-MODEL-PROVIDER-BOUNDARY`, and `PFND-RESPONSE-GROUNDING` define the invariant boundaries.
## Supersession
A future decision may supersede this ADR only with an equally auditable authority and state model.
