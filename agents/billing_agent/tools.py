"""
Billing Agent — Tools.

Implements: blueprints/billing_agent/tools.spec.md
"""
import json
from langchain_core.tools import tool
from .mock_db import billing_service

@tool
def get_billing_summary(member_id: str) -> str:
    """Retrieves the billing summary for a given member. Returns a JSON string of all active accounts, balances, and next payment due dates."""
    result = billing_service.get_billing_summary(member_id)
    return json.dumps(result)

@tool
def schedule_payment(member_id: str, account_id: str, amount: float, date: str) -> str:
    """Schedules a payment for a specific account. Date should be in ISO format (YYYY-MM-DD)."""
    result = billing_service.schedule_payment(member_id, account_id, amount, date)
    return json.dumps(result)

TOOLS = [get_billing_summary, schedule_payment]
