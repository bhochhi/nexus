---
apiVersion: nexus.skills/v1
kind: Skill
metadata:
  name: approved_knowledge
  version: 2.0.0
  owner: Member Knowledge Product
intent:
  description: Answers banking and insurance FAQs from approved local knowledge.
  goals:
    - name: answer_approved_faq
      display_name: ask an account-policy question
      keywords: [overdraft, coverage, deposit insurance, insured, insurance]
      examples:
        - How does overdraft protection work?
        - Are my deposits insured?
  input_schema:
    type: object
    required: [query]
    properties:
      query:
        type: string
        minLength: 2
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
      goal: answer_approved_faq
      outcome: answered
---

# Approved knowledge

Answer only from approved local knowledge. A response must retain its source
identifier, source title, and any required disclosure. When retrieval returns no
approved source, do not answer from model memory. The `tool_response` recipe is
compiled into the standard governed lookup-and-response workflow.
