"""
Auto-Insurance Agent — Graph nodes.
"""
from .state import AutoInsuranceAgentState


def process_node(state: AutoInsuranceAgentState) -> dict:
    """Process member input.
    
    (Note: Logic is handled directly in invoke for this agent)
    """
    return {"response": "", "reasoning": ""}
