---
apiVersion: nexus.capabilities/v1
kind: Capability
metadata:
  id: CAP-INTERNAL-TRANSFER
  name: internal-transfer
  status: approved
  owner: Money Movement
archetype: deterministic
risk: consequential
implementation:
  skill: specifications/capabilities/internal-transfer/SKILL.md
  publishedSkill: skills/catalog/internal_transfer/2.0.0/SKILL.md
---

# Internal account transfer

## Purpose and member value

Allow an authenticated member to move money between eligible accounts through
a conversational experience while retaining deterministic money-movement
controls.

## Scope

- Transfer US dollars between two eligible internal accounts.
- Collect missing source, destination, or amount information conversationally.
- Resolve member-facing account references through the approved account tool.
- Exclude external transfers, scheduled transfers, recurring transfers, and
  amounts above the configured limit.

## Member scenarios

### Complete request

> Transfer $50 from checking to savings.

The assistant resolves both accounts, validates the amount, presents a review,
asks for confirmation, and submits once only after the member confirms.

### Incomplete request

> Move some money to savings.

The assistant asks only for the missing source account and amount.

### Material correction

> Actually, make it $200.

The assistant replaces the amount, invalidates any prior confirmation, and
presents a new review.

## Required behavior

1. Collect the source account, destination account, and amount.
2. Resolve both accounts through the approved account integration.
3. Reject identical source and destination accounts.
4. Validate the amount against currency and configured limits.
5. Present the exact amount and account labels for review.
6. Obtain fresh explicit confirmation immediately before submission.
7. Submit with an idempotency key owned by the durable plan.
8. Return the authoritative tool outcome and transaction reference.
9. Audit validation, confirmation, submission, and failure outcomes.

## Acceptance criteria

- **AC-TRANSFER-001 — Fresh confirmation:** No transfer is submitted until the
  member explicitly confirms the current review.
- **AC-TRANSFER-002 — Material changes invalidate confirmation:** Changing the
  amount or either account requires a new review and confirmation.
- **AC-TRANSFER-003 — Distinct accounts:** Source and destination must resolve
  to different account identifiers.
- **AC-TRANSFER-004 — Amount limits:** The amount must be at least $0.01 and no
  greater than the configured transfer limit.
- **AC-TRANSFER-005 — Idempotent submission:** Retrying the same durable plan
  cannot create a second transfer.
- **AC-TRANSFER-006 — Version continuity:** A paused or restarted plan continues
  with the exact published skill version and hash with which it began.
- **AC-TRANSFER-007 — Controlled failure:** A failed or indeterminate submission
  must not be described as successful and must follow approved recovery or
  handoff behavior.

## Examples

### Review

> Review transfer: $50.00 from Checking to Savings. Confirm this transfer now?

### Decline

> Transfer cancelled; no money was moved.

## Edge cases and failures

- The member uses an ambiguous account nickname.
- An account becomes ineligible between collection and submission.
- The member interrupts before confirmation and later resumes.
- The member says “yes” after changing a material value.
- The submission times out after the backend may have accepted it.
- The channel retries the same confirmed request.
- The active catalog version changes while the plan is paused.

## Governance and integrations

- Risk tier: consequential.
- Authentication is required.
- Required authorization: `transfers:internal`.
- Approved tools: account resolution and idempotent internal-transfer submission.
- The current POC performs only mock transfers and must disclose that fact.
- Failure behavior: take no new action and offer governed handoff when needed.

## Verification

- Deterministic tests must cover every `AC-TRANSFER-*` criterion before
  promotion.
- LLM judging may assess review clarity and conversational quality, but it may
  not approve confirmation, authorization, limits, or idempotency controls.
- Independent verification is required before promoting a consequential skill.
