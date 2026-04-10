from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Intent:
    name: str
    description: str
    sample_utterances: list[str]


def load_intents(domain: str) -> list[Intent]:
    """Load intents for a given domain (banking, insurance, faq)."""
    path = Path(__file__).parent / f"{domain}.yaml"
    data = yaml.safe_load(path.read_text())
    return [
        Intent(
            name=i["name"],
            description=i["description"],
            sample_utterances=i["sample_utterances"],
        )
        for i in data["intents"]
    ]


def load_all_intents() -> dict[str, list[Intent]]:
    """Load intents for all domains."""
    domains = ["banking", "insurance", "faq"]
    return {domain: load_intents(domain) for domain in domains}


def format_intents_for_prompt(intents: dict[str, list[Intent]]) -> str:
    """Format all intents into a string suitable for prompt injection."""
    lines = []
    for domain, domain_intents in intents.items():
        lines.append(f"\n[{domain.upper()}]")
        for intent in domain_intents:
            utterances = ", ".join(f'"{u}"' for u in intent.sample_utterances[:2])
            lines.append(f"  - {intent.name}: {intent.description} (e.g. {utterances})")
    return "\n".join(lines)
