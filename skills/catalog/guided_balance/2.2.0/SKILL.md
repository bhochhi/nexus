---
schema_version: nexus.skills/v3
name: guided_balance
version: 2.2.0
display_name: check an account balance
description: Retrieves available balances for eligible checking or savings accounts owned by the authenticated member. Use when the member asks how much money is available or requests an account balance; do not use to transfer money, explain policy, or discuss an unsupported external account.
examples:
  - What is my balance?
  - How much do I have in checking?
  - Show me the balance for savings 2003.
  - How much money is available in account 1002?
metadata:
  owner: Deposit Servicing
  domain: banking
  category: deposit-servicing
  tags: [authenticated, read-only]
input_schema:
  type: object
  properties:
    account_type:
      type: string
      enum: [checking, savings]
      description: The member-stated account type. It narrows eligible accounts but does not uniquely identify one when several accounts share that type.
    account_number:
      type: string
      description: The account identifier or last four digits the member selected; do not infer it merely from account type.
fallback:
  routing_hints: [balance, how much money, how much I have, available funds]
  input_extraction:
    account_type:
      strategy: alias
      aliases:
        checking: checking
        checkings: checking
        savings: savings
        saving: savings
        chk-001: checking
        chk-002: checking
        chk-003: checking
        sav-001: savings
        sav-002: savings
        "1001": checking
        "1002": checking
        "1003": checking
        "2002": savings
        "2003": savings
    account_number:
      strategy: alias
      aliases:
        chk-001: "1001"
        chk-002: "1002"
        chk-003: "1003"
        sav-001: "2002"
        sav-002: "2003"
        "1001": "1001"
        "1002": "1002"
        "1003": "1003"
        "2002": "2002"
        "2003": "2003"
behavior:
  archetype: guided_resolution
  interaction: guided
  execution: tool_query
  lifecycle: synchronous
governance:
  risk_tier: read_only
  auth_required: true
  required_authorization: balances:read
  confirmation_required: false
  failure_behavior: offer_handoff
implementation:
  tools: [mock_accounts]
  response_template: "Mock balance: {items}."
  telemetry_events: [balance_started, balance_retrieved]
  workflow:
    version: 1
    steps:
      - op: call_tool
        tool: mock_accounts
        action: list_eligible_balances
        arguments:
          member_ref: $context.member_ref
        save_as: eligible_accounts
        completed_step: retrieved eligible account choices
      - op: select
        collection: $vars.eligible_accounts
        input: account_type
        auto_select_threshold: 2
        match_fields: [account_type]
        choice_distinct_by: account_type
        choice_template: "{account_type}"
        prompt_template: "Which account type would you like: {choices}?"
        invalid_prefix: "I couldn't match that account type. "
        separator: "; "
        save_as: accounts_for_type
      - op: select
        collection: $vars.accounts_for_type
        input: account_number
        auto_select_threshold: 2
        restart_on_input_change: [account_type]
        restart_step: 1
        match_fields: [account_id, masked_number, aliases]
        choice_template: "{label}"
        prompt_template: "Which account would you like: {choices}?"
        invalid_prefix: "I couldn't match that account. "
        separator: "; "
        save_as: selected_accounts
      - op: respond
        values: {}
        items: $vars.selected_accounts
        item_template: "{label}: ${available_balance} available"
        separator: "; "
        outcome:
          status: retrieved
          accounts: $vars.selected_accounts
        completed_step: returned authorized mock balance
acceptance:
  - id: asks-for-or-retrieves-account-balance
    utterance: What is my balance?
    expect:
      skill: guided_balance
      outcome: retrieved
---

# Guided balance

## When to use

Use this skill when the member wants an available balance for an eligible
checking or savings account. A request to move money is a separate objective.

## Inputs and interpretation

`account_type` narrows the eligible account collection. `account_number`
identifies a particular account by identifier or last four digits. If several
eligible accounts have the stated type, the type alone is not a complete
selection and the member must choose from the runtime-provided account labels.

## Conversation behavior

Accept an account type, an account number, or both in one turn. Apply explicit
corrections before returning a balance. Ask only for information that remains
ambiguous after the eligible-account lookup.

## Safety and boundaries

The runtime performs the authorization check, eligible-account lookup, account
resolution, and response grounding. Never invent an account or balance.
