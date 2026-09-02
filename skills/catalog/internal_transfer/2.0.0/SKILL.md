---
apiVersion: nexus.skills/v1
kind: Skill
metadata:
  name: internal_transfer
  version: 2.0.0
  owner: Money Movement
intent:
  description: Collects, validates, reviews, confirms, and submits one mock internal transfer.
  goals:
    - name: make_internal_transfer
      display_name: make an internal transfer
      keywords: [transfer, move money, send money between]
      examples:
        - Transfer $50 from checking to savings.
  input_schema:
    type: object
    required: [source_account, destination_account, amount]
    properties:
      source_account:
        type: string
        description: The eligible member account the money should come from; use the member's stated account type, identifier, or last four digits.
      destination_account:
        type: string
        description: The eligible member account that should receive the money; use the member's stated account type, identifier, or last four digits.
      amount:
        type: string
        description: The monetary amount to transfer; an account identifier or last-four value is not an amount unless the member describes it as money.
        pattern: '^[0-9]+(\.[0-9]{1,2})?$'
  input_extraction:
    amount:
      strategy: regex
      pattern: '(?:\$\s*|\b)(\d+(?:\.\d{1,2})?)\b'
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
acceptance:
  - id: requires-confirmation-for-transfer
    utterance: Transfer $50 from checking to savings
    expect:
      skill: internal_transfer
      goal: make_internal_transfer
      confirmation_required: true
---

# Internal transfer

Collect and validate the source account, destination account, and amount. The
member must see a review and explicitly confirm immediately before the one
consequential, idempotent submission step.

## Workflow

```yaml
version: 1
steps:
  - op: collect
    fields:
      - name: source_account
        prompt: Which account should the money come from?
    completed_step: collected source account
  - op: call_tool
    tool: mock_accounts
    action: resolve_account
    arguments:
      reference: $inputs.source_account
    save_as: source
    on_empty:
      status: awaiting_input
      field: source_account
      response: I couldn't match the source account. Please provide its account type and last four digits.
      ambiguous_choice_template: "I found multiple {account_type} accounts. Which account would you like: {choices}?"
  - op: collect
    fields:
      - name: destination_account
        prompt: Which account should receive the money?
    completed_step: collected destination account
  - op: call_tool
    tool: mock_accounts
    action: resolve_account
    arguments:
      reference: $inputs.destination_account
    save_as: destination
    on_empty:
      status: awaiting_input
      field: destination_account
      response: I couldn't match the destination account. Please provide its account type and last four digits.
      ambiguous_choice_template: "I found multiple {account_type} accounts. Which account would you like: {choices}?"
  - op: validate
    rule: not_equal
    left: $vars.source.account_id
    right: $vars.destination.account_id
    on_fail:
      status: awaiting_input
      field: destination_account
      retry_step: 2
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
      source_label: $vars.source.label
      destination_label: $vars.destination.label
    retry_response: Please answer yes to submit the reviewed transfer or no to cancel it.
    decline_response: Transfer cancelled; no money was moved.
    completed_step: presented transfer review
    confirmed_step: captured explicit confirmation
  - op: call_tool
    tool: mock_internal_transfer
    action: submit
    consequential: true
    arguments:
      source_account_id: $vars.source.account_id
      destination_account_id: $vars.destination.account_id
      amount: $vars.amount
      idempotency_key: $vars.idempotency_key
    save_as: receipt
    completed_step: submitted idempotent mock transfer
  - op: respond
    values:
      amount: $vars.amount
      source_label: $vars.source.label
      destination_label: $vars.destination.label
      transaction_id: $vars.receipt.transaction_id
    outcome:
      status: $vars.receipt.status
      transaction_id: $vars.receipt.transaction_id
      amount: $vars.receipt.amount
      duplicate: $vars.receipt.duplicate
```
