---
apiVersion: nexus.platform/v1
kind: PlatformFeature
metadata:
  id: PF-CONVERSATION-LIFECYCLE
  name: governed-conversation-lifecycle
  status: approved
  version: 1.0.0
  owner: Agentic Conversation Platform
enforces:
  - INV-PORTABLE-SOURCE-001
---

# Governed conversation lifecycle

## Purpose

Provide consistent goal selection, skill execution, interruption, confirmation,
and resumption behavior across every business capability.

## Required behavior

- A member objective may produce one or more platform goals.
- Each active goal selects one governed business skill.
- A selected skill supplies an execution plan containing ordered steps.
- A new goal pauses rather than silently discards resumable work.
- Consequential work is never inferred as approved from the original request.

## Acceptance criteria

- **AC-PF-001 — Safe multi-goal ordering:** Given a member asks for a balance
  and a transfer, the read-only goal may complete first and the transfer must
  request confirmation before submission.
- **AC-PF-002 — Interruption preserves the plan:** Given a plan needs input and
  the member changes topic, the original plan remains resumable after the new
  goal completes.

## Examples

> Check my checking balance and then transfer $25 to savings.

The balance result is returned first. The transfer remains a separate goal and
reaches an explicit review and confirmation step before execution.

## Edge cases

- The member abandons the paused goal.
- The skill version changes while a plan is paused.
- The member corrects a material value after confirming.

## Verification

- `tests/test_scenarios.py`
- `tests/test_interruption_and_catalog.py`
- `tests/test_skill_authoring.py`
