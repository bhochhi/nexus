---
apiVersion: nexus.skills/v1
kind: Skill
metadata:
  name: internal_transfer
  version: 2.1.0
  owner: Money Movement
  capability:
    id: CAP-INTERNAL-TRANSFER
    specification: specifications/capabilities/internal-transfer/CAPABILITY.md
    acceptance: [AC-TRANSFER-001, AC-TRANSFER-002, AC-TRANSFER-003, AC-TRANSFER-004, AC-TRANSFER-005, AC-TRANSFER-006, AC-TRANSFER-007]
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
      destination_account:
        type: string
      amount:
        type: string
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
  workflow:
    version: 1
    steps:
      - op: collect
        fields:
          - name: source_account
            prompt: Which account should the money come from?
          - name: destination_account
            prompt: Which account should receive the money?
          - name: amount
            prompt: How much would you like to transfer?
        completed_step: collected transfer details
      - op: call_tool
        tool: mock_accounts
        action: resolve_account
        arguments:
          reference: $inputs.source_account
        save_as: source
        on_empty:
          status: awaiting_input
          field: source_account
          response: I couldn't match the source account. Which account should the money come from?
      - op: call_tool
        tool: mock_accounts
        action: resolve_account
        arguments:
          reference: $inputs.destination_account
        save_as: destination
        on_empty:
          status: awaiting_input
          field: destination_account
          response: I couldn't match the destination account. Which account should receive the money?
      - op: validate
        rule: not_equal
        left: $vars.source.account_id
        right: $vars.destination.account_id
        on_fail:
          status: awaiting_input
          field: destination_account
          retry_step: 2
          response: The destination must be different from the source. Which account should receive the money?
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
acceptance:
  - id: AC-TRANSFER-001
    utterance: Transfer $50 from checking to savings
    expect:
      skill: internal_transfer
      goal: make_internal_transfer
      confirmation_required: true
---

# Internal-transfer runtime skill

Implements `CAP-INTERNAL-TRANSFER`. Collect and validate the accounts and amount,
present the exact review, obtain fresh confirmation, and immediately perform one
idempotent consequential submission.

This candidate preserves the published `2.0.0` execution behavior while moving
the workflow into structured frontmatter and adding explicit capability and
acceptance traceability for its next release.
