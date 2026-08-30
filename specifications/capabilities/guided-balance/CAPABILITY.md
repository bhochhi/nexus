---
apiVersion: nexus.capabilities/v1
kind: Capability
metadata:
  id: CAP-GUIDED-BALANCE
  name: guided-balance
  status: approved
  owner: Deposit Servicing
archetype: guided
risk: read_only
implementation:
  skill: specifications/capabilities/guided-balance/SKILL.md
  publishedSkill: skills/catalog/guided_balance/2.1.0/SKILL.md
---

# Guided account balance

## Purpose and member value

Let an authenticated member retrieve authorized mock balances while asking only
for account distinctions needed to identify the desired eligible account.

## Scope

- Retrieve balances only for accounts eligible for the current member.
- Support checking and savings references, aliases, and masked account numbers.
- Guide account-type and account-number selection when the request is ambiguous.
- Exclude transaction history, external accounts, and unauthorized balances.

## Member scenarios

### Single unambiguous account

> What is my savings balance?

When only one eligible savings account exists, the capability may return it
without asking for redundant information.

### Several accounts of one type

> What is my checking balance?

When several checking accounts are eligible, the capability asks the member to
select the masked account.

### Correction

> I meant savings.

The capability invalidates the earlier dependent account selection and resolves
the corrected type.

## Required behavior

1. Require authenticated balance-read authorization.
2. Retrieve the eligible account set from the approved account tool.
3. Use an explicit account reference when it uniquely identifies an account.
4. Ask for account type or masked number only when needed for disambiguation.
5. Restart dependent selection when the member changes account type.
6. Return only labels, masked identifiers, and authorized available balances.

## Acceptance criteria

- **AC-BALANCE-001 — Authorization:** No account-specific balance is returned
  without the required authenticated authorization.
- **AC-BALANCE-002 — Eligible accounts only:** Selection and response are limited
  to accounts returned by the approved eligibility tool.
- **AC-BALANCE-003 — Minimal clarification:** The capability does not ask for a
  field when the eligible set and supplied reference already resolve uniquely.
- **AC-BALANCE-004 — Ambiguous selection:** Multiple eligible matches produce a
  controlled choice using masked member-facing labels.
- **AC-BALANCE-005 — Correction continuity:** Changing account type invalidates
  dependent account-number selection and resolves the corrected request.
- **AC-BALANCE-006 — Data minimization:** Responses contain no full account number
  or balance for an account outside the resolved eligible set.

## Examples

> Which account would you like: Checking ending in 1001; Checking ending in
> 1002?

The choice exposes enough information to distinguish eligible accounts without
revealing a complete identifier.

## Edge cases and failures

- No eligible accounts are returned.
- Several accounts share the same type and similar aliases.
- The member supplies an invalid or unauthorized account number.
- Eligibility changes between selection and response.
- The member interrupts selection and later resumes.

## Governance and integrations

- Risk tier: read-only account data.
- Authentication and `balances:read` authorization are required.
- Approved tool: account eligibility and balance retrieval.
- Failure behavior: offer governed assistance or handoff without leaking data.

## Verification

- Deterministic tests cover zero, one, two, and several eligible accounts.
- Tests cover aliases, invalid selection, correction, interruption, and masking.
- LLM judging may assess prompt clarity but not authorization or eligibility.
