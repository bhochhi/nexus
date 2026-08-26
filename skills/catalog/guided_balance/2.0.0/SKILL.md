---
apiVersion: nexus.skills/v1
kind: Skill
metadata:
  name: guided_balance
  version: 2.0.0
  owner: Deposit Servicing
intent:
  description: Retrieves authorized mock account balances with guided account selection.
  goals:
    - name: check_account_balance
      display_name: check an account balance
      keywords: [balance, how much money, available funds]
      examples:
        - What is my balance?
        - How much is in checking?
  input_schema:
    type: object
    properties:
      account:
        type: string
  input_extraction:
    account:
      strategy: alias
      aliases:
        checking: checking
        savings: savings
        chk-001: chk-001
        sav-001: sav-001
        "1001": "1001"
        "2002": "2002"
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
  config:
    display_all_threshold: 1
  guided_selection:
    source:
      tool: mock_accounts
      action: list_eligible_balances
      arguments:
        member_ref: $context.member_ref
      save_as: eligible_accounts
      completed_step: retrieved eligible account choices
    selection:
      collection: $vars.eligible_accounts
      input: account
      auto_select_threshold: $config.display_all_threshold
      match_fields: [account_id, account_type, masked_number, label, aliases]
      choice_template: "{label}"
      prompt_template: "Which account would you like: {choices}?"
      invalid_prefix: "I couldn't match that account. "
      separator: "; "
      save_as: selected_accounts
    response:
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
      goal: check_account_balance
      outcome: retrieved
---

# Guided balance

Retrieve only accounts eligible for the authenticated mock member. If the
configured threshold does not permit showing all accounts, ask neutrally which
account the member wants and validate their answer against eligible accounts.
The `guided_selection` recipe compiles this configuration into the shared
retrieve, select, and respond operations.
