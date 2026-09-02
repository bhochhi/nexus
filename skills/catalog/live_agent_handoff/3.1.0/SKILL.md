---
schema_version: nexus.skills/v3
name: live_agent_handoff
version: 3.1.0
display_name: speak with a live agent
description: Connects a member with a live support representative by collecting a concise reason, deriving the appropriate banking, insurance, or advice queue, and sending minimized context. Use when the member explicitly asks for a person or accepts an offered handoff.
examples:
  - Get me a person.
  - I want to speak with a representative.
  - Connect me to someone about my auto policy.
  - Yes, please transfer me to live support.
metadata:
  owner: Contact Center Operations
  domain: servicing
  category: assisted-support
  tags: [handoff]
input_schema:
  type: object
  required: [reason, queue]
  properties:
    reason:
      type: string
      description: The member's concise reason for requesting live support; preserve the business topic while excluding unnecessary sensitive detail.
    queue:
      type: string
      enum: [insurance, banking, advice]
      description: Derive insurance for policies, coverage, premiums, or claims; banking for accounts, cards, balances, or transactions; and advice for planning or financial guidance.
fallback:
  routing_hints: [live agent, human, person, representative, talk to someone]
  input_extraction:
    reason:
      strategy: full_message
    queue:
      strategy: alias
      aliases:
        insurance: insurance
        policy: insurance
        coverage: insurance
        claim: insurance
        premium: insurance
        auto: insurance
        banking: banking
        bank: banking
        account: banking
        balance: banking
        credit card: banking
        debit card: banking
        transaction: banking
        advice: advice
        advisor: advice
        planning: advice
        retirement: advice
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
  response_template: "You're in the {queue} live-support queue. Case {case_id}. I'll connect you automatically when an MSR is available."
  telemetry_events: [handoff_requested, handoff_queued]
  config:
    queues: [insurance, banking, advice]
  workflow:
    version: 1
    steps:
      - op: collect
        fields:
          - name: reason
            prompt: Briefly, what would you like the live specialist to help with?
          - name: queue
            prompt: Is this about insurance, banking, or financial advice?
        completed_step: collected live-support reason and queue
      - op: call_tool
        tool: mock_live_agent
        action: create
        arguments:
          reason: $inputs.reason
          queue: $inputs.queue
          active_goal: $context.prior_task.goal
          completed_steps: $context.prior_task.completed_steps
        save_as: handoff
        completed_step: queued live-agent case
      - op: respond
        values:
          queue: $vars.handoff.queue
          case_id: $vars.handoff.case_id
        outcome:
          status: $vars.handoff.status
          case_id: $vars.handoff.case_id
          queue: $vars.handoff.queue
          reason: $inputs.reason
          summary: $vars.handoff.summary
        completed_step: returned minimized handoff context
acceptance:
  - id: recognizes-live-agent-request
    utterance: I want a live agent about my credit card balance
    expect:
      skill: live_agent_handoff
---

# Live-agent handoff

## When to use

Use this skill when the member explicitly requests a human representative or
accepts a handoff offered by conversation policy. Do not treat ordinary
frustration as consent to transfer the conversation.

## Inputs and interpretation

`reason` is a concise description of what the live specialist should handle.
`queue` is derived from that reason when the topic is clear. Ask the member to
choose banking, insurance, or advice only when the queue remains ambiguous.

## Conversation behavior

Acknowledge the request directly. Avoid making the member repeat information
already available from the active task. Keep the handoff summary concise and
relevant.

## Safety and boundaries

The runtime owns queue validation, context minimization, case creation, and the
returned case status. Do not send the full transcript or claim that a person is
connected before the handoff tool reports it.
