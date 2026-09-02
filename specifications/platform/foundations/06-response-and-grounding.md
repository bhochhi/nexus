---
apiVersion: nexus.platform/v1
kind: PlatformFoundation
metadata: {id: PFND-RESPONSE-GROUNDING, name: response-and-grounding, status: approved, version: 1.0.0, owner: Agentic Conversation Platform}
decisions: [ADR-0003]
interfaces: [SkillResult, ResponseDraft, AssistantEvent]
---
# Response composition and grounding
## Purpose
Create a consistent member experience from authoritative results and controlled conversation context.
## Responsibilities
- Compose acknowledgements, clarifications, results, resumptions, gaps, and failures without changing execution truth.
- Retain required sources, disclosures, and minimized context.
## Invariants
- **INV-RESPONSE-001:** Generated language cannot invent a tool outcome, approval, source, or completed action.
- **INV-RESPONSE-002:** Informational claims require approved grounding or controlled copy.
## Interfaces
- Business result, source metadata, policy annotations, and streaming event contracts.
## Failure behavior
- Fall back to controlled copy while preserving the authoritative outcome.
## Verification
- `tests/test_scenarios.py`, `tests/test_streaming.py`.
