---
apiVersion: nexus.capabilities/v1
kind: Capability
metadata:
  id: CAP-DOMAIN-NNN
  name: capability-name
  status: draft
  owner: Business owner
archetype: declarative
risk: informational
---

# Capability name

## Purpose and member value

Explain what approved information or controlled response this capability gives.

## Scope

- Included questions and outcomes.
- Explicit exclusions.

## Member scenarios

> Representative member language.

- Expected grounded or controlled response behavior.

## Required behavior

- Identify the approved source, response recipe, and disclosure behavior.
- Never fill knowledge gaps from model memory.

## Acceptance criteria

- **AC-CAP-NNN — Grounded response:** Given ..., when ..., then ...

## Examples

Include positive, paraphrased, ambiguous, and unsupported requests.

## Edge cases and failures

- Missing, stale, contradictory, or unavailable approved content.

## Governance and integrations

- Knowledge sources, tools, disclosures, owner, and freshness requirements.

## Verification

- Deterministic scenarios and optional LLM-judge clarity rubric.
