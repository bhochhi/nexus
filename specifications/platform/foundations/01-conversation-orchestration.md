---
apiVersion: nexus.platform/v1
kind: PlatformFoundation
metadata: {id: PFND-CONVERSATION-ORCHESTRATION, name: conversation-orchestration, status: approved, version: 1.0.0, owner: Agentic Conversation Platform}
decisions: [ADR-0003]
interfaces: [TurnAnalysis, ConversationDecision, ConversationState]
---
# Conversation orchestration
## Purpose
Coordinate each turn without embedding business-capability branches in the orchestrator.
## Responsibilities
- Interpret a turn, reconcile it with durable work, choose an allowed decision, and persist the result before responding.
- Order concurrent work by policy and preserve resumable interruptions.
## Invariants
- **INV-ORCH-001:** Model output is advisory; only validated platform decisions change durable state.
- **INV-ORCH-002:** Orchestration depends on capability metadata and contracts, never a concrete skill name.
## Interfaces
- Consumes `TurnAnalysis`; emits `ConversationDecision`, events, and a response request.
## Failure behavior
- Reject invalid decisions, retain prior durable state, and use controlled reception or handoff behavior.
## Verification
- `tests/test_scenarios.py`, `tests/test_streaming.py`.
