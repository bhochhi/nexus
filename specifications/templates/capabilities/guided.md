---
apiVersion: nexus.capabilities/v1
kind: Capability
metadata:
  id: CAP-DOMAIN-NNN
  name: capability-name
  status: draft
  owner: Business owner
archetype: guided
risk: read_only
---

# Capability name

## Purpose and member value

Explain the outcome and why progressive information gathering is appropriate.

## Scope

- Supported goals, outcomes, and exclusions.

## Member scenarios

Describe complete, incomplete, out-of-order, corrected, and interrupted input.

## Required behavior

- Required and optional fields, prompts, validation, and completion behavior.
- Ask only for information still needed.

## Acceptance criteria

- **AC-CAP-NNN — Progressive collection:** Given ..., when ..., then ...

## Examples

Include multi-turn conversations and corrections.

## Edge cases and failures

- Ambiguous selections, invalid values, interruption, timeout, and tool failure.

## Governance and integrations

- Authentication, authorization, data minimization, tools, and handoff rules.

## Verification

- Deterministic state/slot tests and optional conversational-quality rubric.
