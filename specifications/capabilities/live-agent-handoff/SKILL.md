---
apiVersion: nexus.skills/v1
kind: Skill
metadata:
  name: live_agent_handoff
  version: 3.3.0
  owner: Contact Center Operations
  capability:
    id: CAP-LIVE-AGENT-HANDOFF
    specification: specifications/capabilities/live-agent-handoff/CAPABILITY.md
    acceptance: [AC-HANDOFF-001, AC-HANDOFF-002, AC-HANDOFF-003, AC-HANDOFF-004, AC-HANDOFF-005, AC-HANDOFF-006, AC-HANDOFF-007, AC-HANDOFF-008]
intent:
  description: Collects a live-support reason, derives the right queue, and creates a minimized handoff.
  goals:
    - name: request_live_agent
      display_name: speak with a live agent
      keywords: [live agent, human, person, representative, talk to someone]
      examples:
        - Get me a person.
        - I want a live agent about my auto policy.
  input_schema:
    type: object
    required: [reason, queue]
    properties:
      reason:
        type: string
        description: The member's concise reason for requesting live support.
      queue:
        type: string
        enum: [insurance, banking, advice]
        description: Derive insurance for policies, coverage, premiums, or claims; banking for accounts, cards, balances, or transactions; and advice for planning or financial guidance.
      active_goal:
        type: string
      completed_steps:
        type: array
        items:
          type: string
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
    summary_message_limit: 24
    summary_paragraph_character_limit: 800
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
          active_goal: $inputs.active_goal
          completed_steps: $inputs.completed_steps
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
  - id: AC-HANDOFF-001
    utterance: I want a live agent about my credit card balance
    expect:
      skill: live_agent_handoff
      goal: request_live_agent
---

# Live-agent handoff runtime skill

Implements `CAP-LIVE-AGENT-HANDOFF`. After shared conversation policy enters the
handoff flow, collect a concise reason, use only an approved queue, and transfer
minimized context rather than the full transcript.

The representative-facing summary retains deterministic `Goal`, `Reason`, and
`Completed` fields. It may add one concise paragraph grounded only in the
bounded transcript and structured task context. Greetings, confirmation and
queue-selection logistics, invented causes or outcomes, and the full transcript
are excluded. Summary-generation failure uses deterministic minimized copy and
does not change the authoritative handoff result.

This `3.3.0` candidate carries forward the published `3.2.0` behavior while
adding explicit capability and acceptance traceability for a future release; it
does not modify the immutable published artifact.
