---
apiVersion: nexus.skills/v1
kind: Skill
metadata:
  name: guided_balance
  version: 2.1.0
  owner: Deposit Servicing
intent:
  description: Retrieves authorized mock account balances using account type and account-number selection when needed.
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
      account_type:
        type: string
        enum: [checking, savings]
      account_number:
        type: string
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
      goal: check_account_balance
      outcome: retrieved
---

# Guided balance

Retrieve only accounts eligible for the authenticated mock member. Display all
eligible balances when the member has two or fewer accounts. For a larger
portfolio, collect account type first, then collect the account number only
when there are multiple eligible accounts of that type. A member can correct a
selected account type at any time before the balance is returned.