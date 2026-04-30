"""
Auto-Insurance Agent — State definition.
"""
from typing import TypedDict


class AutoInsuranceAgentState(TypedDict):
    """LangGraph state for Auto-Insurance Agent."""
    response: str
    reasoning: str
