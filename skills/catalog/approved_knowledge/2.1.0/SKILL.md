---
schema_version: nexus.skills/v3
name: approved_knowledge
version: 2.1.0
display_name: ask an account-policy question
description: Answers member questions about supported banking and insurance policies using only approved local knowledge. Use for informational questions about overdraft, deposit insurance, and coverage; do not use for account-specific balances, transactions, money movement, or personalized advice.
examples:
  - How does overdraft protection work?
  - Are my deposits insured?
  - What coverage applies to this account?
  - Can you explain the deposit insurance policy?
metadata:
  owner: Member Knowledge Product
  domain: banking
  category: member-knowledge
  tags: [informational, grounded]
input_schema:
  type: object
  required: [query]
  properties:
    query:
      type: string
      minLength: 2
      description: The member's complete informational policy question; preserve the subject and qualifiers needed for approved retrieval.
fallback:
  routing_hints: [overdraft, coverage, deposit insurance, insured, insurance]
  input_extraction:
    query:
      strategy: full_message
behavior:
  archetype: knowledge
  interaction: direct
  execution: knowledge_retrieval
  lifecycle: synchronous
governance:
  risk_tier: informational
  auth_required: false
  confirmation_required: false
  failure_behavior: offer_handoff
implementation:
  tools: [local_knowledge]
  response_template: "{answer} Source: {source_title} ({source_id}). {disclosure}"
  telemetry_events: [knowledge_search, grounded_answer]
  config:
    maximum_sources: 1
  tool_response:
    call:
      tool: local_knowledge
      action: search
      arguments:
        query: $inputs.query
        limit: $config.maximum_sources
      save_as: matches
      completed_step: retrieved approved knowledge
      on_empty:
        status: failed
        response: I couldn't find an approved answer for that question. I can connect you with a live agent instead.
        outcome:
          status: no_approved_source
    response:
      values:
        answer: $vars.matches.0.answer
        source_title: $vars.matches.0.title
        source_id: $vars.matches.0.source_id
        disclosure: $vars.matches.0.disclosure
      outcome:
        status: answered
        source_id: $vars.matches.0.source_id
        source_title: $vars.matches.0.title
        grounded: true
      completed_step: returned grounded answer
acceptance:
  - id: answers-approved-overdraft-question
    utterance: How does overdraft protection work?
    expect:
      skill: approved_knowledge
      outcome: answered
---

# Approved knowledge

## When to use

Use this skill for informational banking or insurance policy questions covered
by the approved knowledge collection. Do not use it for member-specific account
data, transactions, money movement, or personalized recommendations.

## Inputs and interpretation

Treat `query` as the member's complete question. Preserve meaningful qualifiers
instead of reducing it to a keyword.

## Conversation behavior

Answer only from the grounded retrieval result. Keep the source identifier,
source title, and required disclosure. If no approved source is returned, say
that an approved answer was not found and offer the governed fallback; do not
fill the gap from model memory.

## Safety and boundaries

The runtime owns retrieval, source limits, grounding, and fallback behavior.
The model may phrase the grounded result naturally but must not invent policy.
