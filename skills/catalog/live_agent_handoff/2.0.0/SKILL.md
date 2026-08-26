---
apiVersion: nexus.skills/v1
kind: Skill
metadata:
  name: live_agent_handoff
  version: 2.0.0
  owner: Contact Center Operations
intent:
  description: Creates a mock live-agent case with minimized context.
  goals:
    - name: request_live_agent
      display_name: speak with a live agent
      keywords: [live agent, human, person, representative, talk to someone]
      examples:
        - Get me a person.
        - I want a live agent.
  input_schema:
    type: object
    properties:
      reason:
        type: string
      active_goal:
        type: string
      completed_steps:
        type: array
        items:
          type: string
behavior:
  archetype: human_handoff
  interaction: guided
  execution: handoff
  lifecycle: synchronous
governance:
  risk_tier: handoff
  auth_required: false
  confirmation_required: false
  failure_behavior: show_alternate_support_channel
implementation:
  tools: [mock_live_agent]
  response_template: "I've queued a mock live agent in {queue}. Case {case_id}; they will receive a concise summary."
  telemetry_events: [handoff_requested, handoff_queued]
  config:
    queue: member-support
  tool_response:
    call:
      tool: mock_live_agent
      action: create
      arguments:
        reason: $inputs.reason
        active_goal: $inputs.active_goal
        completed_steps: $inputs.completed_steps
      save_as: handoff
      completed_step: queued mock live-agent case
    response:
      values:
        queue: $vars.handoff.queue
        case_id: $vars.handoff.case_id
      outcome:
        status: $vars.handoff.status
        case_id: $vars.handoff.case_id
        queue: $vars.handoff.queue
        summary: $vars.handoff.summary
      completed_step: returned minimized handoff context
acceptance:
  - id: recognizes-live-agent-request
    utterance: I want a live agent
    expect:
      skill: live_agent_handoff
      goal: request_live_agent
---

# Live-agent handoff

Create a support case only after the shared conversation policy has confirmed
that the member wants a handoff. Transfer a concise reason, active goal, and
completed-step summary rather than the full conversation. The `tool_response`
recipe compiles to the common governed executor.
