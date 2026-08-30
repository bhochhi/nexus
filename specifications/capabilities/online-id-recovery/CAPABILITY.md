---
apiVersion: nexus.capabilities/v1
kind: Capability
metadata:
  id: CAP-ONLINE-ID-RECOVERY
  name: online-id-recovery
  status: approved
  owner: Digital Identity
archetype: navigation
risk: navigation
implementation:
  skill: specifications/capabilities/online-id-recovery/SKILL.md
  publishedSkill: skills/catalog/online_id_recovery/3.0.0/SKILL.md
---

# Online-ID recovery navigation

## Purpose and member value

Help a member who forgot their online ID reach the approved identity-recovery
journey without collecting, displaying, or inferring identity information in
the conversation.

## Scope

- Recognize requests to recover an online ID or username.
- Resolve the platform-owned approved recovery destination.
- Return controlled navigation copy and destination metadata.
- Exclude identity lookup, identity disclosure, and business-authored arbitrary
  URLs.

## Member scenarios

### Direct request

> I forgot my online ID.

The capability provides the approved recovery destination and privacy reminder.

### Unsupported disclosure request

> Tell me what my username is.

The capability does not retrieve or infer the username and directs the member to
the approved recovery journey.

## Required behavior

1. Use a platform-owned destination identifier rather than an authored URL.
2. Resolve the identifier through the approved navigation adapter.
3. Return only the adapter-provided URL and destination metadata.
4. State that the assistant will not display or infer the member's online ID.
5. Follow configured handoff behavior if the approved destination is unavailable.

## Acceptance criteria

- **AC-ONLINE-ID-001 — Approved destination:** Navigation resolves only the
  allowlisted `online_id_recovery` destination.
- **AC-ONLINE-ID-002 — No identity disclosure:** The conversation never displays,
  infers, or collects the member's online ID.
- **AC-ONLINE-ID-003 — Platform-owned URL:** Business-authored skill content
  cannot substitute an arbitrary URL for the navigation adapter result.
- **AC-ONLINE-ID-004 — Controlled failure:** An unavailable destination produces
  approved failure or handoff behavior rather than an invented link.
- **AC-ONLINE-ID-005 — Dynamic availability:** Once a compatible version is
  activated, new goals can route to it without graph recompilation or restart.

## Examples

> Use the approved online-ID recovery page: [approved destination]. I won't
> display or infer your ID here.

## Edge cases and failures

- The destination configuration is missing or not allowlisted.
- The member asks for both recovery and an unrelated goal.
- The skill activates while another plan is in progress.
- A newer version changes response wording but retains the same destination.

## Governance and integrations

- Risk tier: navigation.
- Authentication is not required to provide the recovery entry point.
- Approved integration: platform-owned navigation adapter.
- Identity information remains within the approved recovery journey.

## Verification

- Tests cover routing before and after activation, destination allowlisting,
  failure behavior, version upgrade, rollback, and interruption/resumption.
- Security tests assert no identity value enters response, state, or trace.
