"""
Tests for Auto-Insurance Agent.

Tests the tools and the agent's basic initialization.
"""
import json
import unittest
from unittest.mock import MagicMock

from agents.auto_insurance_agent.tools import get_policy_details, add_driver, remove_driver
from agents.auto_insurance_agent.mock_db import MOCK_POLICIES
from agents.auto_insurance_agent.agent import AutoInsuranceAgent
from core.session import SessionState


class TestAutoInsuranceTools(unittest.TestCase):
    """Test the tools directly."""

    def setUp(self):
        # Reset mock db for each test
        MOCK_POLICIES["MEMBER-123"] = [
            {
                "policy_id": "AUTO-999888",
                "start_date": "2026-01-15",
                "expiry_date": "2027-01-15",
                "premium": 1250.00,
                "deductibles": {
                    "comprehensive": 500.00,
                    "liability": 0.00
                },
                "drivers": ["Alice Smith"]
            }
        ]

    def test_get_policy_details_success(self):
        result = get_policy_details.invoke({"member_id": "MEMBER-123"})
        data = json.loads(result)
        self.assertEqual(data["policy_id"], "AUTO-999888")
        self.assertIn("Alice Smith", data["drivers"])

    def test_get_policy_details_not_found(self):
        result = get_policy_details.invoke({"member_id": "UNKNOWN"})
        self.assertIn("No auto insurance policies found", result)

    def test_add_driver_success(self):
        result = add_driver.invoke({"member_id": "MEMBER-123", "driver_name": "Bob Jones"})
        self.assertIn("Successfully added driver", result)
        self.assertIn("Bob Jones", MOCK_POLICIES["MEMBER-123"][0]["drivers"])

    def test_add_driver_already_exists(self):
        result = add_driver.invoke({"member_id": "MEMBER-123", "driver_name": "Alice Smith"})
        self.assertIn("already on the policy", result)
        self.assertEqual(len(MOCK_POLICIES["MEMBER-123"][0]["drivers"]), 1)

    def test_remove_driver_success(self):
        # Add a second driver first so we don't violate the >1 rule
        MOCK_POLICIES["MEMBER-123"][0]["drivers"].append("Bob Jones")
        
        result = remove_driver.invoke({"member_id": "MEMBER-123", "driver_name": "Alice Smith"})
        self.assertIn("Successfully removed driver", result)
        self.assertNotIn("Alice Smith", MOCK_POLICIES["MEMBER-123"][0]["drivers"])

    def test_remove_driver_only_driver(self):
        result = remove_driver.invoke({"member_id": "MEMBER-123", "driver_name": "Alice Smith"})
        self.assertIn("must have at least one active driver", result)
        self.assertIn("Alice Smith", MOCK_POLICIES["MEMBER-123"][0]["drivers"])

    def test_remove_driver_not_found(self):
        result = remove_driver.invoke({"member_id": "MEMBER-123", "driver_name": "Ghost Driver"})
        self.assertIn("not currently on the policy", result)


class TestAutoInsuranceAgentInit(unittest.TestCase):
    """Test the agent initialization and structure."""

    def test_initialization(self):
        llm_mock = MagicMock()
        session_mock = MagicMock(spec=SessionState)
        agent = AutoInsuranceAgent(llm_client=llm_mock, session=session_mock)

        self.assertEqual(agent.agent_name, "auto_insurance_agent")
        self.assertIsNone(agent.build_graph())
        self.assertEqual(len(agent.get_tools()), 3)
        self.assertIn("get_policy_details", agent.tool_map)
        self.assertIn("add_driver", agent.tool_map)
        self.assertIn("remove_driver", agent.tool_map)


if __name__ == "__main__":
    unittest.main()
