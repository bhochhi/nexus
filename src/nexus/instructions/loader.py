from pathlib import Path

import yaml


def load_instructions(domain: str) -> list[str]:
    """Load behavioral rules for a given domain."""
    path = Path(__file__).parent / f"{domain}.yaml"
    data = yaml.safe_load(path.read_text())
    return data.get("rules", [])


def load_all_instructions() -> dict[str, list[str]]:
    """Load instructions for all domains."""
    domains = ["global", "banking", "insurance", "escalation"]
    return {domain: load_instructions(domain) for domain in domains}
