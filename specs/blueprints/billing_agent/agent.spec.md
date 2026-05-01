# Blueprint: Billing Agent

## Purpose
The Billing Agent provides member self-service for billing inquiries, retrieving payment details, scheduling payments, and answering standard FAQs. It leverages a mock billing service to simulate real-time API integrations and relies on static prompt instructions for FAQ answering.

## Implements Features
- F-009: Billing Agent

## Interface Contract

### `MockBillingService`
A new service located at `services/billing.py` to simulate a backend system.
- **Data Structure**: Hardcoded mock data for multiple users. `member_id` "12345" will have multiple accounts (e.g., Auto Loan, Personal Loan, Mortgage).
- **Methods**:
  - `get_billing_summary(member_id: str) -> dict`: Returns a list of active accounts, current balances, and next payment due dates/amounts.
  - `schedule_payment(member_id: str, account_id: str, amount: float, date: str) -> dict`: Simulates scheduling a payment, returning a confirmation number and updated status.

### FAQ Strategy
The FAQ answers will be directly injected into the `agents/billing_agent/instruction.md`.
Example instructions to add:
- "If the user asks about supported payment methods, tell them we accept ACH, Debit Cards, and internal account transfers."
- "If the user asks about late fees, explain that a 5% fee applies after a 10-day grace period."

## Data Models

```python
@dataclass
class AccountBillingInfo:
    account_id: str
    account_type: str  # e.g., "Auto Loan", "Mortgage"
    balance: float
    next_payment_amount: float
    next_payment_date: str

@dataclass
class BillingSummary:
    member_id: str
    accounts: List[AccountBillingInfo]
```

## Acceptance Criteria
- [ ] `BillingAgent` is created using `scripts/create_agent.py` and correctly registered.
- [ ] `MockBillingService` returns multiple accounts for member disambiguation testing.
- [ ] FAQ responses perfectly align with `instruction.md` without tool calls.

## Dependencies
- `MainAgent` routing (Requires ensuring the `BillingAgent` is discoverable via `agent.md`).
- `services/billing.py` (New mock service).
