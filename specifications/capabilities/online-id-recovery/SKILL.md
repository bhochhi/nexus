---
apiVersion: nexus.skills/v1
kind: Skill
metadata:
  name: online_id_recovery
  version: 3.1.0
  owner: Digital Identity
  capability:
    id: CAP-ONLINE-ID-RECOVERY
    specification: specifications/capabilities/online-id-recovery/CAPABILITY.md
    acceptance: [AC-ONLINE-ID-001, AC-ONLINE-ID-002, AC-ONLINE-ID-003, AC-ONLINE-ID-004, AC-ONLINE-ID-005]
intent:
  description: Navigates a member to the approved online-ID recovery experience.
  goals:
    - name: recover_online_id
      display_name: recover your online ID
      keywords: [online id, username, forgot my id, forgot id]
      examples:
        - I forgot my online ID.
        - Help me recover my username.
  input_schema:
    type: object
    properties: {}
behavior:
  archetype: navigation
  interaction: direct
  execution: navigation
  lifecycle: synchronous
governance:
  risk_tier: navigation
  auth_required: false
  confirmation_required: false
  disclosure: Identity information is handled only by the approved recovery journey.
  failure_behavior: offer_handoff
implementation:
  tools: [mock_approved_navigation]
  response_template: "Use the approved online-ID recovery page: {url}. I won't display or infer your ID here."
  telemetry_events: [online_id_recovery_link_provided]
  config:
    destination: online_id_recovery
  navigation:
    tool: mock_approved_navigation
    action: open_destination
    arguments:
      destination: $config.destination
    save_as: navigation
    completed_step: provided approved recovery link
    response_values:
      url: $vars.navigation.url
    outcome:
      status: navigated
      destination: $vars.navigation.destination
      url: $vars.navigation.url
acceptance:
  - id: AC-ONLINE-ID-001
    utterance: I forgot my online ID
    expect:
      skill: online_id_recovery
      goal: recover_online_id
      outcome: navigated
---

# Online-ID recovery runtime skill

Implements `CAP-ONLINE-ID-RECOVERY`. Resolve only the platform-owned recovery
destination. Never display, infer, or collect the member's online ID in chat.

This candidate preserves the published `3.0.0` execution behavior while adding
explicit capability and acceptance traceability for its next release.
