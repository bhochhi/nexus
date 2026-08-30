---
apiVersion: nexus.capabilities/v1
kind: Capability
metadata:
  id: CAP-DOMAIN-NNN
  name: capability-name
  status: draft
  owner: Business owner
archetype: deterministic
risk: consequential
---

# Capability name

## Purpose and member value

Explain the consequential outcome and why a fixed governed sequence is needed.

## Scope

- Supported action, limits, eligibility, and explicit exclusions.

## Member scenarios

Describe complete, incomplete, corrected, declined, duplicated, and interrupted
requests.

## Required behavior

- Ordered collection, authorization, validation, review, fresh confirmation,
  idempotent execution, status resolution, audit, and response steps.

## Acceptance criteria

- **AC-CAP-NNN — Fresh confirmation:** Given ..., when ..., then ...
- **AC-CAP-NNN — Idempotency:** Given ..., when ..., then ...

## Examples

Include the review presented immediately before execution.

## Edge cases and failures

- Material correction, duplicate retry, timeout after submission, partial
  failure, policy denial, and handoff.

## Governance and integrations

- Risk owner, authorization, confirmation, limits, tools, audit, and retention.

## Verification

- Deterministic safety tests are mandatory; LLM judging may assess wording only.
