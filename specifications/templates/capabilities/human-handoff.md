---
apiVersion: nexus.capabilities/v1
kind: Capability
metadata:
  id: CAP-DOMAIN-NNN
  name: capability-name
  status: draft
  owner: Business owner
archetype: human_handoff
risk: handoff
---

# Capability name

## Purpose and member value

Explain when and how responsibility moves from automation to a person.

## Scope

- Supported triggers, queues, channels, and exclusions.

## Member scenarios

Describe explicit request, safety escalation, frustration, unavailable queue,
cancel, assignment, and return to automation.

## Required behavior

- Obtain required confirmation, minimize transferred context, preserve state,
  expose ownership, and prevent dual automated/human replies.

## Acceptance criteria

- **AC-CAP-NNN — Context minimization:** Given ..., when ..., then ...

## Examples

Include member, system, and representative messages.

## Edge cases and failures

- No representative online, disconnect, cancellation, reassignment, and timeout.

## Governance and integrations

- Queue ownership, consent, context fields, retention, audit, and service levels.

## Verification

- Routing, privacy, state-continuity, and concurrency tests.
