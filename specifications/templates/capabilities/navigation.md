---
apiVersion: nexus.capabilities/v1
kind: Capability
metadata:
  id: CAP-DOMAIN-NNN
  name: capability-name
  status: draft
  owner: Business owner
archetype: navigation
risk: navigation
---

# Capability name

## Purpose and member value

Explain the trusted destination or journey offered to the member.

## Scope

- Supported navigation goals and prohibited destinations.

## Member scenarios

Describe direct, ambiguous, unavailable, and interrupted navigation requests.

## Required behavior

- Resolve only an allowlisted destination through a platform-owned adapter.
- Do not expose sensitive identifiers or business-authored arbitrary URLs.

## Acceptance criteria

- **AC-CAP-NNN — Approved destination:** Given ..., when ..., then ...

## Examples

Include representative member language and expected member-visible copy.

## Edge cases and failures

- Destination unavailable, session ineligible, or member changes goals.

## Governance and integrations

- Destination owner, authentication needs, disclosures, and analytics events.

## Verification

- Allowlist, response, and failure-path tests.
