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
  publishedSkill: skills/catalog/live_agent_handoff/3.2.0/SKILL.md
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
- Provide deterministic goal, reason, and completed-step fields plus one
  bounded, grounded summary paragraph for the representative.
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
5. Transfer only allowed deterministic fields and a bounded transcript window.
6. Generate at most one concise summary paragraph grounded only in that
   transcript and structured task context; exclude greetings and handoff
   logistics and never invent causes, facts, decisions, or outcomes.
7. Preserve deterministic goal, reason, and completed-step fields and use a
   deterministic minimized paragraph if generation is unavailable.
8. Return the case identifier, queue, and authoritative waiting status.
9. Once assigned, prevent automated replies from competing with the human chat.

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
- **AC-HANDOFF-007 — Grounded summary:** The optional generated paragraph uses
  only the bounded transcript and structured task context, stays within its
  configured limit, and contains no invented cause, fact, decision, or outcome.
- **AC-HANDOFF-008 — Deterministic fallback:** If summary generation is
  unavailable or invalid, the representative still receives deterministic
  goal, reason, completed-step, and minimized fallback fields.

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
- The summary provider fails, returns unsupported claims, or exceeds its limit.

## Governance and integrations

- Risk tier: handoff.
- Shared platform policy owns the confirmation or offer preceding the skill.
- Approved integration: live-support queue and case service.
- Transfer only minimized context; do not send a full transcript by default.
- Summary generation is presentation support, not execution authority, and its
  failure cannot block or falsify a successfully queued case.

## Verification

- Deterministic tests cover queue derivation, clarification, waiting,
  assignment, cancellation, reconnect, and return to automation.
- Privacy tests assert summary minimization.
- Grounding and fallback tests assert bounded input, deterministic fields,
  unsupported-claim rejection, and provider-unavailable behavior.
- Concurrency tests assert a single active responder.
