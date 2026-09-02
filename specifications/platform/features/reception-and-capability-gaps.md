---
apiVersion: nexus.platform/v1
kind: PlatformFeature
metadata: {id: PF-RECEPTION-CAPABILITY-GAPS, name: reception-and-capability-gaps, status: approved, version: 1.0.0, owner: Agentic Conversation Platform}
enforces: [INV-ORCH-002, INV-RESPONSE-002]
---
# Reception and capability gaps
## Purpose
Explain the currently available capability surface and handle unsupported or ambiguous objectives without disrupting active work.
## Required behavior
- Greetings and capability questions use only current catalog metadata.
- Ambiguity is clarified before a goal is created.
- Unsupported objectives emit a structured gap and offer only governed next steps.
- A gap detected during active input collection preserves the active task.
## Acceptance criteria
- **AC-PF-RECEPTION-001 — Catalog accuracy:** Reception advertises only active catalog capabilities.
- **AC-PF-RECEPTION-002 — Durable ambiguity:** A clarification prompt and its choices survive restart.
- **AC-PF-RECEPTION-003 — Controlled gap:** Unsupported work is acknowledged without invented execution and is observable as a structured gap.
## Examples
A request outside the active catalog receives a concise limitation and, when appropriate, an offer of assisted support.
## Edge cases
- A greeting occurs during active work; several candidates tie; the provider reports a gap for an installed capability.
## Verification
- `tests/test_scenarios.py`, `tests/test_observability.py`.
