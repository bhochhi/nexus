"""
Main Agent — Graph node helper functions.

Pure utility functions used by the MainAgent's graph nodes.

Implements: blueprints/main_agent/nodes.spec.md
"""
import re
from typing import Tuple


def extract_reasoning(text: str) -> Tuple[str, str]:
    """Extract <reasoning>...</reasoning> content and clean the response text.

    Returns:
        (reasoning_text, cleaned_response)
    """
    match = re.search(r"<reasoning>(.*?)</reasoning>", text, re.DOTALL)
    if match:
        reasoning = match.group(1).strip()
        clean = re.sub(r"<reasoning>.*?</reasoning>\s*", "", text, flags=re.DOTALL).strip()
        return reasoning, clean
    return "", text
