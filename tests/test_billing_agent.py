"""
Tests for Billing Agent.

Tests the tools and the agent's basic initialization.
"""
import json
import unittest
from unittest.mock import MagicMock

from agents.billing_agent.tools import get_billing_summary, schedule_payment
from agents.billing_agent.agent import BillingAgent
from agents.billing_agent.mock_db import billing_service
from core.session import SessionState


class TestBillingTools(unittest.TestCase):
    """Test the tools directly."""

    def test_get_billing_summary_success(self):
        result = get_billing_summary.invoke({"member_id": "12345"})
        data = json.loads(result)
        self.assertEqual(data["member_id"], "12345")
        self.assertEqual(len(data["accounts"]), 3)
        self.assertEqual(data["accounts"][0]["account_type"], "Auto Loan")

    def test_get_billing_summary_not_found(self):
        result = get_billing_summary.invoke({"member_id": "UNKNOWN"})
        data = json.loads(result)
        self.assertIn("error", data)

    def test_schedule_payment_success(self):
        result = schedule_payment.invoke({
            "member_id": "12345", 
            "account_id": "AL-9876", 
            "amount": 350.00, 
            "date": "2026-05-15"
        })
        data = json.loads(result)
        self.assertEqual(data["status"], "success")
        self.assertIn("CONF-", data["confirmation_number"])

    def test_schedule_payment_account_not_found(self):
        result = schedule_payment.invoke({
            "member_id": "12345", 
            "account_id": "UNKNOWN-999", 
            "amount": 100.00, 
            "date": "2026-05-15"
        })
        data = json.loads(result)
        self.assertIn("error", data)


class TestBillingAgentInit(unittest.TestCase):
    """Test the agent initialization and structure."""

    def test_initialization(self):
        llm_mock = MagicMock()
        session_mock = MagicMock(spec=SessionState)
        agent = BillingAgent(llm_client=llm_mock, session=session_mock)

        self.assertEqual(agent.agent_name, "billing_agent")
        self.assertIsNone(agent.build_graph())
        self.assertEqual(len(agent.tools), 3) # 2 original tools + yield_control


if __name__ == "__main__":
    unittest.main()
