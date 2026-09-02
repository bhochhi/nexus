---
schema_version: nexus.skills/v3
name: internal_transfer
version: 2.1.0
display_name: make an internal transfer
description: Moves money between eligible checking and savings accounts owned by the authenticated member. Use for requests to transfer, move, send, or put funds from one member-owned account into another; do not use for person-to-person payments, bill pay, wires, or transfers involving an external bank.
examples:
  - Transfer $50 from checking to savings.
  - Move two hundred dollars from savings 2003 to checking 1002.
  - Send $200 from my checking account 1001 to savings.
  - Put $75 in my other checking account from savings.
  - I want to move money between my accounts.
metadata:
  owner: Money Movement
  domain: banking
  category: money-movement
  tags: [authenticated, consequential]
input_schema:
  type: object
  required: [source_account, destination_account, amount]
  properties:
    source_account:
      type: string
      description: The eligible member account the money leaves. Use the account type, identifier, or last four digits stated as the source; if direction is unclear, ask instead of guessing.
    destination_account:
      type: string
      description: The eligible member account receiving the money. Use the account type, identifier, or last four digits stated as the destination; if direction is unclear, ask instead of guessing.
    amount:
      type: string
      format: currency-amount
      description: The monetary amount to transfer. A number used as an account identifier or last four digits is not an amount unless the member describes it as money.
      pattern: '^[0-9]+(\.[0-9]{1,2})?$'
fallback:
  routing_hints: [transfer, move money, send money, move funds, between my accounts]
  input_extraction:
    amount:
      strategy: regex
      pattern: '\$\s*(\d+(?:\.\d{1,2})?)\b'
      group: 1
    source_account:
      strategy: regex
      pattern: '\bfrom\s+([a-z0-9-]+)(?:\s+account)?\s+to\s+([a-z0-9-]+)'
      group: 1
    destination_account:
      strategy: regex
      pattern: '\bfrom\s+([a-z0-9-]+)(?:\s+account)?\s+to\s+([a-z0-9-]+)'
      group: 2
behavior:
  archetype: deterministic_workflow
  interaction: guided
  execution: workflow
  lifecycle: synchronous
governance:
  risk_tier: consequential
  auth_required: true
  required_authorization: transfers:internal
  confirmation_required: true
  disclosure: This POC performs only a mock transfer.
  failure_behavior: no_action_and_offer_handoff
implementation:
  tools: [mock_accounts, mock_internal_transfer]
  response_template: "Mock transfer completed: ${amount} from {source_label} to {destination_label}. Reference {transaction_id}."
  telemetry_events: [transfer_validated, confirmation_requested, transfer_submitted]
  config:
    maximum_amount: "5000.00"
    currency: USD
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
      - op: collect
        fields:
          - name: source_account
            prompt: Which account should the money come from?
        completed_step: collected source account
      - op: select
        collection: $vars.eligible_accounts
        input: source_account
        auto_select_threshold: 1
        require_single: true
        match_fields: [account_id, account_type, masked_number, label, aliases]
        choice_template: "{label}"
        prompt_template: "Which source account would you like: {choices}?"
        ambiguous_prompt_template: "I found multiple {selection} accounts. Which account would you like: {choices}?"
        invalid_prefix: "I couldn't match that source account. "
        separator: "; "
        save_as: source
      - op: collect
        fields:
          - name: destination_account
            prompt: Which account should receive the money?
        completed_step: collected destination account
      - op: select
        collection: $vars.eligible_accounts
        input: destination_account
        auto_select_threshold: 1
        require_single: true
        match_fields: [account_id, account_type, masked_number, label, aliases]
        choice_template: "{label}"
        prompt_template: "Which destination account would you like: {choices}?"
        ambiguous_prompt_template: "I found multiple {selection} accounts. Which account would you like: {choices}?"
        invalid_prefix: "I couldn't match that destination account. "
        separator: "; "
        save_as: destination
      - op: validate
        rule: not_equal
        left: $vars.source.0.account_id
        right: $vars.destination.0.account_id
        on_fail:
          status: awaiting_input
          field: destination_account
          retry_step: 3
          response: The destination must be different from the source. Which account should receive the money?
      - op: collect
        fields:
          - name: amount
            prompt: How much would you like to transfer?
        completed_step: collected transfer amount
      - op: validate_decimal
        value: $inputs.amount
        minimum: "0.01"
        maximum: $config.maximum_amount
        save_as: amount
        on_fail:
          status: awaiting_input
          field: amount
          response: Enter an amount greater than $0 and within the configured transfer limit.
        completed_step: validated transfer details
      - op: set
        value: $task.id
        save_as: idempotency_key
      - op: confirm
        template: "Review mock transfer: ${amount} from {source_label} to {destination_label}. Confirm this transfer now? Please answer yes or no."
        values:
          amount: $vars.amount
          source_label: $vars.source.0.label
          destination_label: $vars.destination.0.label
        retry_response: Please answer yes to submit the reviewed transfer or no to cancel it.
        decline_response: Transfer cancelled; no money was moved.
        completed_step: presented transfer review
        confirmed_step: captured explicit confirmation
      - op: call_tool
        tool: mock_internal_transfer
        action: submit
        consequential: true
        arguments:
          source_account_id: $vars.source.0.account_id
          destination_account_id: $vars.destination.0.account_id
          amount: $vars.amount
          idempotency_key: $vars.idempotency_key
        save_as: receipt
        completed_step: submitted idempotent mock transfer
      - op: respond
        values:
          amount: $vars.receipt.amount
          source_label: $vars.source.0.label
          destination_label: $vars.destination.0.label
          transaction_id: $vars.receipt.transaction_id
        outcome:
          status: submitted
          transaction_id: $vars.receipt.transaction_id
          amount: $vars.receipt.amount
          source_account: $vars.source.0.account_id
          destination_account: $vars.destination.0.account_id
        completed_step: returned mock transfer receipt
acceptance:
  - id: requires-confirmation-for-transfer
    utterance: Transfer $50 from checking to savings
    expect:
      skill: internal_transfer
      confirmation_required: true
---

# Internal transfer

## When to use

Use this skill to move money between eligible accounts owned by the same
authenticated member. Words such as “move,” “send,” and “put” can express an
internal transfer even when the member does not say “transfer.”

Do not use it for another person's account, an external bank, bill payment, or
a wire.

## Inputs and interpretation

- `source_account` is the account the money leaves.
- `destination_account` is the account receiving the money.
- `amount` is the monetary value to move.

Extract all unambiguous inputs supplied in one turn. Account type alone is not a
unique account when the runtime returns multiple matches. A four-digit suffix
next to an account type is an account reference, not an amount. If “to” and
“from” direction is unclear, summarize the likely interpretation and ask the
member to confirm or correct it.

## Conversation behavior

Ask only for missing or ambiguous information. Accept explicit corrections to
any unconfirmed input. Never claim that a transfer is complete before the
runtime returns a receipt.

## Safety and boundaries

The runtime owns account eligibility and resolution, source/destination
inequality, amount limits, the exact review, explicit confirmation,
authorization, idempotency, and submission. Model instructions cannot bypass
those controls.
