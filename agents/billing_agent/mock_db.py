from dataclasses import dataclass
from typing import List, Dict
import datetime

@dataclass
class AccountBillingInfo:
    account_id: str
    account_type: str  # e.g., "Auto Loan", "Mortgage", "Personal Loan"
    balance: float
    next_payment_amount: float
    next_payment_date: str

@dataclass
class BillingSummary:
    member_id: str
    accounts: List[AccountBillingInfo]

class MockBillingService:
    def __init__(self):
        # In-memory mock data
        self._members_data: Dict[str, BillingSummary] = {
            "12345": BillingSummary(
                member_id="12345",
                accounts=[
                    AccountBillingInfo(
                        account_id="AL-9876",
                        account_type="Auto Loan",
                        balance=15000.00,
                        next_payment_amount=350.00,
                        next_payment_date=(datetime.date.today() + datetime.timedelta(days=10)).isoformat()
                    ),
                    AccountBillingInfo(
                        account_id="PL-5432",
                        account_type="Personal Loan",
                        balance=5000.00,
                        next_payment_amount=150.00,
                        next_payment_date=(datetime.date.today() + datetime.timedelta(days=2)).isoformat()
                    ),
                    AccountBillingInfo(
                        account_id="MTG-1122",
                        account_type="Mortgage",
                        balance=350000.00,
                        next_payment_amount=2100.00,
                        next_payment_date=(datetime.date.today() + datetime.timedelta(days=20)).isoformat()
                    )
                ]
            )
        }

    def get_billing_summary(self, member_id: str) -> dict:
        """Retrieves the billing summary for a given member."""
        if member_id not in self._members_data:
            return {"error": "Member not found. Please provide a valid member ID (e.g., '12345')."}
        
        summary = self._members_data[member_id]
        return {
            "member_id": summary.member_id,
            "accounts": [
                {
                    "account_id": acc.account_id,
                    "account_type": acc.account_type,
                    "balance": acc.balance,
                    "next_payment_amount": acc.next_payment_amount,
                    "next_payment_date": acc.next_payment_date
                }
                for acc in summary.accounts
            ]
        }

    def schedule_payment(self, member_id: str, account_id: str, amount: float, date: str) -> dict:
        """Simulates scheduling a payment."""
        if member_id not in self._members_data:
            return {"error": "Member not found."}
        
        summary = self._members_data[member_id]
        account = next((acc for acc in summary.accounts if acc.account_id == account_id), None)
        
        if not account:
            return {"error": f"Account {account_id} not found for member {member_id}."}
        
        # In a real system, we'd validate the date format and create a transaction record.
        # Here we just mock a success response.
        return {
            "status": "success",
            "message": f"Payment of ${amount:.2f} scheduled for {date} on account {account_id}.",
            "confirmation_number": f"CONF-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

# Global singleton instance for the mock service
billing_service = MockBillingService()
