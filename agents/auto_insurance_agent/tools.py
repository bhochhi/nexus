"""
Auto-Insurance Agent — Tool definitions.

Implements: blueprints/auto_insurance_agent/tools.spec.md
"""
import json
from langchain_core.tools import tool
from .mock_db import MOCK_POLICIES


@tool
def get_policy_details(member_id: str) -> str:
    """Retrieve the active auto insurance policy details for a given member.
    
    Args:
        member_id: The unique identifier of the member.
    """
    policies = MOCK_POLICIES.get(member_id)
    if not policies:
        return f"No auto insurance policies found for member {member_id}."
    
    # Return the first/active policy
    return json.dumps(policies[0], indent=2)


@tool
def add_driver(member_id: str, driver_name: str) -> str:
    """Add a new driver to the active auto insurance policy.
    
    Args:
        member_id: The unique identifier of the member.
        driver_name: The full name of the driver to be added.
    """
    policies = MOCK_POLICIES.get(member_id)
    if not policies:
        return f"No auto insurance policies found for member {member_id}."
    
    policy = policies[0]
    if driver_name in policy["drivers"]:
        return f"Driver '{driver_name}' is already on the policy."
    
    policy["drivers"].append(driver_name)
    return f"Successfully added driver '{driver_name}' to policy {policy['policy_id']}."


@tool
def remove_driver(member_id: str, driver_name: str) -> str:
    """Remove an existing driver from the active auto insurance policy.
    
    Args:
        member_id: The unique identifier of the member.
        driver_name: The full name of the driver to be removed.
    """
    policies = MOCK_POLICIES.get(member_id)
    if not policies:
        return f"No auto insurance policies found for member {member_id}."
    
    policy = policies[0]
    if driver_name not in policy["drivers"]:
        return f"Driver '{driver_name}' is not currently on the policy."
        
    if len(policy["drivers"]) <= 1:
        return f"Cannot remove driver '{driver_name}'. The policy must have at least one active driver."
        
    policy["drivers"].remove(driver_name)
    return f"Successfully removed driver '{driver_name}' from policy {policy['policy_id']}."

# Export the tools list
TOOLS = [get_policy_details, add_driver, remove_driver]
