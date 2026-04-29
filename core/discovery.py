"""
Nexus — Agent discovery.

Scans agents/ directory at startup, reads agent.md from each module,
parses YAML frontmatter, and builds a registry of AgentCapability objects.

Implements: blueprints/core/discovery.spec.md
Features: F-002 (Agent Discovery & Capability Awareness)
"""
import logging
import os
import re
from typing import List, Optional

from core.types import AgentCapability, Skill

logger = logging.getLogger(__name__)


def discover_agents(agents_dir: str) -> List[AgentCapability]:
    """Scan agents/*/agent.md, parse YAML frontmatter, return capabilities.

    - Skips directories starting with '_' (e.g., _template/)
    - Only includes agents with status 'active'
    - Never crashes — logs warnings on errors
    """
    capabilities = []

    if not os.path.isdir(agents_dir):
        logger.warning(f"Agents directory not found: {agents_dir}")
        return capabilities

    for entry in sorted(os.listdir(agents_dir)):
        # Skip hidden dirs, template dirs, and files
        if entry.startswith("_") or entry.startswith("."):
            continue

        agent_dir = os.path.join(agents_dir, entry)
        if not os.path.isdir(agent_dir):
            continue

        agent_md_path = os.path.join(agent_dir, "agent.md")
        if not os.path.isfile(agent_md_path):
            logger.warning(f"No agent.md found in {agent_dir}, skipping")
            continue

        capability = parse_agent_md(agent_md_path)
        if capability is None:
            continue

        if capability.status != "active":
            logger.info(f"Agent '{capability.name}' has status '{capability.status}', skipping")
            continue

        capabilities.append(capability)
        logger.info(f"Discovered agent: {capability.name} ({len(capability.skills)} skills)")

    return capabilities


def parse_agent_md(filepath: str) -> Optional[AgentCapability]:
    """Parse agent.md YAML frontmatter into AgentCapability.

    Uses regex-based parsing to avoid pyyaml dependency.
    Frontmatter is content between first two '---' lines.
    """
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except (IOError, OSError) as e:
        logger.warning(f"Could not read {filepath}: {e}")
        return None

    # Extract YAML frontmatter
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        logger.warning(f"No YAML frontmatter found in {filepath}")
        return None

    frontmatter = match.group(1)

    try:
        name = _extract_field(frontmatter, "name")
        display_name = _extract_field(frontmatter, "display_name")
        description = _extract_field(frontmatter, "description")
        version = _extract_field(frontmatter, "version", default="1.0.0")
        status = _extract_field(frontmatter, "status", default="active")
        skills = _extract_skills(frontmatter)

        if not name:
            logger.warning(f"Missing 'name' in {filepath}")
            return None
        if not display_name:
            logger.warning(f"Missing 'display_name' in {filepath}")
            return None

        module_path = os.path.dirname(filepath)

        return AgentCapability(
            name=name,
            display_name=display_name,
            description=description or "",
            skills=skills,
            version=version,
            status=status,
            module_path=module_path,
        )
    except Exception as e:
        logger.warning(f"Error parsing {filepath}: {e}")
        return None


def _extract_field(frontmatter: str, field_name: str, default: str = "") -> str:
    """Extract a simple key: value field from YAML frontmatter."""
    # Match field_name: "value" or field_name: value (not a list item)
    pattern = rf'^{field_name}:\s*["\']?(.*?)["\']?\s*$'
    match = re.search(pattern, frontmatter, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return default


def _extract_skills(frontmatter: str) -> List[Skill]:
    """Extract skills list from YAML frontmatter.

    Expected format:
    skills:
      - name: skill_name
        description: "Skill description"
    """
    skills = []

    # Find the skills section
    skills_match = re.search(r'^skills:\s*$', frontmatter, re.MULTILINE)
    if not skills_match:
        return skills

    # Get everything after 'skills:'
    remaining = frontmatter[skills_match.end():]

    # Parse each skill item (starts with '  - name:')
    skill_blocks = re.finditer(
        r'-\s*name:\s*["\']?(.*?)["\']?\s*\n\s*description:\s*["\']?(.*?)["\']?\s*$',
        remaining,
        re.MULTILINE,
    )

    for match in skill_blocks:
        skill_name = match.group(1).strip()
        skill_desc = match.group(2).strip()
        if skill_name:
            skills.append(Skill(name=skill_name, description=skill_desc))

    return skills


def format_capabilities(capabilities: List[AgentCapability]) -> str:
    """Format capabilities into a human-readable string for the member."""
    if not capabilities:
        return "I'm still setting up. No services are available yet."

    lines = ["Here's what I can help with today:"]
    for cap in capabilities:
        if cap.name == "main_agent":
            continue  # Don't list the orchestrator as a capability
        for skill in cap.skills:
            lines.append(f"  • {cap.display_name} — {skill.description}")

    if len(lines) == 1:
        return "I'm still setting up. No services are available yet."

    return "\n".join(lines)
