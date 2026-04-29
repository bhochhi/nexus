#!/usr/bin/env python3
"""
Agent Scaffolding Script — Creates a new agent module from templates.

Creates a fully-structured agent directory with all required files,
ready for development and auto-discoverable by the orchestrator.

Implements: blueprints/scripts/create_agent.spec.md

Usage:
    python scripts/create_agent.py <agent_name> [--display-name "..."] [--description "..."]

Example:
    python scripts/create_agent.py billing_agent \\
        --display-name "Billing Agent" \\
        --description "Handles billing inquiries and payment setup"
"""
import argparse
import os
import re
import sys


# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(PROJECT_ROOT, "agents")
TEMPLATE_DIR = os.path.join(AGENTS_DIR, "_template")

# Template files to process (template filename → output filename)
TEMPLATE_FILES = [
    ("agent.md.template", "agent.md"),
    ("persona.md.template", "persona.md"),
    ("instruction.md.template", "instruction.md"),
    ("agent.py.template", "agent.py"),
    ("graph.py.template", "graph.py"),
    ("nodes.py.template", "nodes.py"),
    ("tools.py.template", "tools.py"),
    ("state.py.template", "state.py"),
    ("__init__.py.template", "__init__.py"),
]


def to_class_name(agent_name: str) -> str:
    """Convert snake_case agent_name to PascalCase class name.

    If name ends with '_agent', produce e.g. 'LiveAgent' (not 'LiveAgentAgent').
    If name doesn't end with '_agent', append 'Agent': 'billing' → 'BillingAgent'.

    Examples:
        live_agent → LiveAgent
        billing_agent → BillingAgent
        balance_inquiry → BalanceInquiryAgent
        faq → FaqAgent
    """
    # Split on underscores and capitalize each part
    parts = agent_name.split("_")

    # Check if name already ends with 'agent'
    if parts[-1].lower() == "agent" and len(parts) > 1:
        # Already has 'agent' suffix — just PascalCase it
        return "".join(part.capitalize() for part in parts)
    else:
        # Add 'Agent' suffix
        return "".join(part.capitalize() for part in parts) + "Agent"


def to_display_name(agent_name: str) -> str:
    """Convert snake_case agent_name to a human-readable display name.

    Examples:
        billing_agent → Billing Agent
        balance_inquiry → Balance Inquiry
    """
    return " ".join(part.capitalize() for part in agent_name.split("_"))


def validate_agent_name(name: str) -> bool:
    """Check that agent_name is a valid Python identifier in snake_case."""
    if not name.isidentifier():
        return False
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        return False
    return True


def substitute_variables(template_content: str, variables: dict) -> str:
    """Replace {{variable}} placeholders in template content."""
    result = template_content
    for key, value in variables.items():
        result = result.replace("{{" + key + "}}", value)
    return result


def create_agent(agent_name: str, display_name: str, description: str) -> None:
    """Create a new agent module from templates."""
    target_dir = os.path.join(AGENTS_DIR, agent_name)

    # Check if agent already exists
    if os.path.exists(target_dir):
        print(f"❌ Error: Agent '{agent_name}' already exists at {target_dir}/")
        sys.exit(1)

    # Check templates directory exists
    if not os.path.isdir(TEMPLATE_DIR):
        print(f"❌ Error: Template directory not found at {TEMPLATE_DIR}/")
        sys.exit(1)

    # Build variable map
    class_name = to_class_name(agent_name)
    variables = {
        "agent_name": agent_name,
        "display_name": display_name,
        "description": description,
        "class_name": class_name,
        "version": "1.0.0",
    }

    # Create agent directory
    os.makedirs(target_dir)

    # Process each template
    created_files = []
    for template_filename, output_filename in TEMPLATE_FILES:
        template_path = os.path.join(TEMPLATE_DIR, template_filename)

        if not os.path.exists(template_path):
            print(f"⚠️  Warning: Template not found: {template_filename}")
            continue

        # Read template
        with open(template_path, "r") as f:
            template_content = f.read()

        # Substitute variables
        output_content = substitute_variables(template_content, variables)

        # Write output
        output_path = os.path.join(target_dir, output_filename)
        with open(output_path, "w") as f:
            f.write(output_content)

        created_files.append(os.path.join("agents", agent_name, output_filename))

    # Print success summary
    print(f"\n✅ Agent '{agent_name}' created at agents/{agent_name}/\n")
    print("Files created:")
    for filepath in created_files:
        print(f"  {filepath}")
    print()
    print("Next steps:")
    print("  1. Edit agent.md to define your agent's skills")
    print("  2. Implement your graph in graph.py")
    print("  3. Add tools in tools.py")
    print("  4. Run the app — your agent will be auto-discovered")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Nexus agent from the standard template.",
        epilog="Example: python scripts/create_agent.py billing_agent "
               '--display-name "Billing Agent" '
               '--description "Handles billing inquiries"',
    )
    parser.add_argument(
        "agent_name",
        help="Snake_case name for the agent (e.g., billing_agent)",
    )
    parser.add_argument(
        "--display-name",
        default=None,
        help='Human-readable name (default: derived from agent_name)',
    )
    parser.add_argument(
        "--description",
        default=None,
        help='Agent description (default: auto-generated)',
    )

    args = parser.parse_args()

    # Validate agent name
    if not validate_agent_name(args.agent_name):
        print(
            f"❌ Error: Agent name '{args.agent_name}' is not a valid Python identifier. "
            "Use snake_case (e.g., 'my_agent')."
        )
        sys.exit(1)

    # Derive defaults
    display_name = args.display_name or to_display_name(args.agent_name)
    description = args.description or f"A specialized agent for {display_name} tasks."

    create_agent(args.agent_name, display_name, description)


if __name__ == "__main__":
    main()
