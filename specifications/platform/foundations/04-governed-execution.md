---
apiVersion: nexus.platform/v1
kind: PlatformFoundation
metadata: {id: PFND-GOVERNED-EXECUTION, name: governed-execution, status: approved, version: 1.0.0, owner: Agentic Conversation Platform}
decisions: [ADR-0004]
interfaces: [ExecutionPlan, ToolContract, PolicyDecision]
---
# Governed execution
## Purpose
Execute flexible conversational plans through deterministic, allowlisted operations.
## Responsibilities
- Validate inputs, authorize operations, obtain required confirmation, invoke declared tools, and return authoritative outcomes.
- Enforce operation ordering and idempotency for consequential work.
## Invariants
- **INV-EXEC-001:** A plan invokes only declared tools, actions, and platform operations.
- **INV-EXEC-002:** A consequential call immediately follows fresh confirmation of the material inputs.
## Interfaces
- Capability runtime surface, tool contracts, and policy engine.
## Failure behavior
- Fail closed, avoid unsupported success claims, and retain enough state for governed recovery.
## Verification
- `tests/test_declarative_skills.py`, `tests/test_scenarios.py`.
