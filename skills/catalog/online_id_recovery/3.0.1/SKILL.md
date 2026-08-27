---
apiVersion: nexus.skills/v1
kind: Skill
metadata:
  name: online_id_recovery
  version: 3.0.1
  owner: Digital Identity
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
  - id: routes-recovery-request
    utterance: I forgot my online ID
    expect:
      skill: online_id_recovery
      goal: recover_online_id
      outcome: navigated
---

# Online ID recovery

Help a member who has forgotten their online ID reach the approved recovery
experience. Never display, infer, or collect the member's online ID in chat.

This is a direct navigation capability, so its small `implementation.navigation`
contract compiles into the standard governed tool-and-response workflow. It does
not need a separate workflow file or a Python executor.
