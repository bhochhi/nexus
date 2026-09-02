---
apiVersion: nexus.capabilities/v1
kind: Capability
metadata:
  id: CAP-LIVE-AGENT-HANDOFF
  name: live-agent-handoff
  status: approved
  owner: Contact Center Operations
archetype: human_handoff
risk: handoff
implementation:
  skill: specifications/capabilities/live-agent-handoff/SKILL.md
  publishedSkill: skills/catalog/live_agent_handoff/3.1.0/SKILL.md
---

# Live-agent handoff

## Purpose and member value

Move responsibility to an appropriate member-service representative when the
member requests a person or platform policy requires human support, without
making the member repeat unnecessary context.

## Scope

- Collect a concise support reason after shared policy establishes handoff intent.
- Derive or ask for one of the approved insurance, banking, or advice queues.
- Create a minimized case and place it in the approved queue.
- Exclude unrestricted transcript transfer and unsupported queue invention.

## Member scenarios

### Clear queue

> I need a person about my credit card balance.

The capability records the concise reason, selects banking, and queues the case.

### Ambiguous queue

> Please get me someone who can help.

The capability asks whether the request concerns insurance, banking, or advice.

### Interrupted work

The current goal and completed safe steps may be included in minimized context;
sensitive values and the full transcript are not transferred automatically.

## Required behavior

1. Enter only after shared conversation policy authorizes the handoff flow.
2. Collect a concise reason and approved queue.
3. Derive a queue only when the reason clearly maps to an approved value.
4. Create the case through the approved live-support tool.
5. Transfer only allowed summary fields, active goal, and completed steps.
6. Return the case identifier, queue, and authoritative waiting status.
7. Once assigned, prevent automated replies from competing with the human chat.

## Acceptance criteria

- **AC-HANDOFF-001 — Approved queue:** Every created case uses insurance,
  banking, or advice; ambiguity produces clarification.
- **AC-HANDOFF-002 — Context minimization:** The handoff summary contains only
  allowed goal, reason, completed-step, and session context.
- **AC-HANDOFF-003 — Authoritative status:** The member is told only the queue
  and assignment status returned by the live-support system.
- **AC-HANDOFF-004 — State continuity:** Paused work and relevant completed steps
  remain available for governed return or representative context.
- **AC-HANDOFF-005 — Single responder:** Assigned live-support conversations do
  not also route member messages through the virtual-assistant graph.
- **AC-HANDOFF-006 — Failure behavior:** Unavailable or failed handoff follows an
  approved alternate-support response without inventing an assignment.

## Examples

> You're in the banking live-support queue. Case CASE-123. I'll connect you when
> a representative is available.

The wording reflects an actual queued case and does not claim that a
representative is already connected.

## Edge cases and failures

- The reason maps to several queues.
- No representative is online.
- The member cancels while waiting.
- Assignment occurs after a reconnect.
- A representative ends the conversation and returns the member to automation.
- Case creation succeeds but the response is delayed or duplicated.

## Governance and integrations

- Risk tier: handoff.
- Shared platform policy owns the confirmation or offer preceding the skill.
- Approved integration: live-support queue and case service.
- Transfer only minimized context; do not send a full transcript by default.

## Verification

- Deterministic tests cover queue derivation, clarification, waiting,
  assignment, cancellation, reconnect, and return to automation.
- Privacy tests assert summary minimization.
- Concurrency tests assert a single active responder.
