---
# Target authoring schema. Complete the platform migration documented in
# docs/skill-schema-migration-plan.md before publishing v3 artifacts.
schema_version: nexus.skills/v3
name: replace_with_lower_snake_case_name
version: 1.0.0

display_name: member-facing capability phrase
description: Describe what the skill does, when to use it, and its important boundaries in no more than 1024 characters.
examples:
  - A short, realistic way a member may request this capability.
  - A meaningfully different paraphrase without requiring exact wording.

# Omit `goals`; the platform derives one goal named `name`. The current v3
# compiler rejects multi-goal artifacts.

metadata:
  # Accountable team identity, not a business category.
  owner: accountable-team-name
  domain: replace_with_business_domain
  category: replace_with_catalog_category
  tags: []

input_schema:
  type: object
  required: [required_input]
  properties:
    required_input:
      type: string
      description: Explain the business meaning, valid evidence, and important ambiguity rules for this input.

# Optional conservative offline behavior. Do not use this as the semantic
# definition of the skill; description and examples own discovery meaning.
fallback:
  routing_hints: []
  input_extraction: {}

behavior:
  # Built-in presets: knowledge, guided_resolution, deterministic_workflow,
  # navigation, human_handoff. A custom archetype must still compile to the
  # platform's allowlisted workflow operations.
  archetype: guided_resolution
  interaction: guided
  execution: workflow
  lifecycle: synchronous
governance:
  risk_tier: read_only
  auth_required: true
  required_authorization: replace:with_scope
  confirmation_required: false
  failure_behavior: offer_handoff
implementation:
  # Tier 3 runtime dependencies. These are not automatically exposed as LLM
  # function calls. Every workflow call must name a tool from this allowlist.
  tools: [approved_tool]
  response_template: "Completed with {grounded_value}."
  telemetry_events: [skill_started, skill_completed]
  config: {}
  workflow:
    version: 1
    steps:
      # Optional preflight: a safe read-only lookup may run before collect.
      # Current Nexus can stop safely on failure; automatic rejection of this
      # candidate and selection of the next ranked goal is not yet implemented.
      - op: call_tool
        tool: approved_tool
        action: read_only_preflight
        arguments:
          member_ref: $context.member_ref
        save_as: eligibility
      - op: validate
        rule: truthy
        left: $vars.eligibility
        on_fail:
          status: failed
          response: This capability is not currently available for the member.
          outcome:
            status: ineligible
      - op: collect
        fields:
          - name: required_input
            prompt: Ask one concise question for the unresolved input.
      - op: call_tool
        tool: approved_tool
        action: perform_read_only_action
        arguments:
          value: $inputs.required_input
        save_as: result
      - op: respond
        values:
          grounded_value: $vars.result.value
        outcome:
          status: completed
acceptance:
  - id: routes-a-representative-request
    utterance: A short, realistic way a member may request this capability.
    expect:
      skill: replace_with_lower_snake_case_name
      outcome: completed
---

# Member-facing skill title

## When to use

Explain the positive boundary and the nearby requests that are outside this
skill. Do not duplicate the executable workflow.

## Inputs and interpretation

Explain what each input means in member language, how several inputs may appear
in one turn, how corrections work, and which ambiguities require a question.

## Conversation behavior

Explain how to acknowledge the objective, what context may be reused, and how
to ask concise questions. These instructions guide language understanding and
wording; they do not override runtime controls.

## Safety and boundaries

State what must remain deterministic, grounded, policy-controlled, confirmed,
or tool-validated. Identify claims the model must not make on its own.
