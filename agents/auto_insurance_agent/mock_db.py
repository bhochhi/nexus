"""
Mock Database for Auto-Insurance Agent.
Implements: blueprints/auto_insurance_agent/tools.spec.md
"""

MOCK_POLICIES = {
    "MEMBER-123": [
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
}
