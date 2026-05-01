# Blueprint: Billing Agent Tools

## Purpose
Defines the tool definitions for the Billing Agent, allowing it to interface with the `MockBillingService`.

## Tools

### 1. `get_billing_summary`
- **Input**: `member_id: str`
- **Output**: JSON string of billing summary for all accounts.
- **Behavior**: Calls `MockBillingService.get_billing_summary()`.
- **Error Handling**: Gracefully returns error messages if the service call fails or the member ID is not found.

### 2. `schedule_payment`
- **Input**: `member_id: str`, `account_id: str`, `amount: float`, `date: str`
- **Output**: JSON string with confirmation details.
- **Behavior**: Calls `MockBillingService.schedule_payment()`.
- **Validation**: Requires all fields to be populated. Fails if date format is invalid.

## Acceptance Criteria
- [ ] Agent correctly routes to `get_billing_summary` when asked about payments.
- [ ] Agent correctly routes to `schedule_payment` and returns a confirmation.
- [ ] Tools cleanly handle missing accounts or missing member IDs without crashing the agent.
