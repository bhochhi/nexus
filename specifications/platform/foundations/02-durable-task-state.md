---
apiVersion: nexus.platform/v1
kind: PlatformFoundation
metadata: {id: PFND-DURABLE-TASK-STATE, name: durable-task-state, status: approved, version: 1.0.0, owner: Agentic Conversation Platform}
decisions: [ADR-0003, ADR-0004]
interfaces: [ConversationState, TaskState, WorkflowState]
---
# Durable task state
## Purpose
Preserve official progress across turns, interruptions, restarts, and catalog changes.
## Responsibilities
- Persist active, queued, paused, and completed work with inputs, progress, status, and exact artifact identity.
- Apply corrections by invalidating dependent validation and confirmation state.
## Invariants
- **INV-STATE-001:** In-flight work remains pinned to its original artifact version and hash.
- **INV-STATE-002:** A new objective cannot silently discard resumable work.
## Interfaces
- State store transaction boundary and workflow-state contract.
## Failure behavior
- On persistence failure, do not claim progress or execute a consequential operation.
## Verification
- `tests/test_state_store.py`, `tests/test_interruption_and_catalog.py`.
