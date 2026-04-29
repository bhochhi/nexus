"""
Tests for core/discovery.py

Acceptance criteria from blueprints/core/discovery.spec.md
Feature: F-002 (Agent Discovery & Capability Awareness)
"""
import os
import tempfile

from core.discovery import (
    discover_agents,
    format_capabilities,
    parse_agent_md,
)
from core.types import AgentCapability, Skill


def _create_agent_md(tmpdir, agent_name, content):
    """Helper to create an agent directory with agent.md."""
    agent_dir = os.path.join(tmpdir, agent_name)
    os.makedirs(agent_dir, exist_ok=True)
    with open(os.path.join(agent_dir, "agent.md"), "w") as f:
        f.write(content)
    return agent_dir


VALID_AGENT_MD = """---
name: test_agent
display_name: "Test Agent"
description: "A test agent for unit testing"
skills:
  - name: do_something
    description: "Does something useful"
  - name: do_other
    description: "Does something else"
version: "1.0.0"
status: active
---

# Test Agent

This is a test agent.
"""

DISABLED_AGENT_MD = """---
name: disabled_agent
display_name: "Disabled Agent"
description: "Should be skipped"
skills:
  - name: noop
    description: "Does nothing"
version: "1.0.0"
status: disabled
---
"""

MINIMAL_AGENT_MD = """---
name: minimal
display_name: "Minimal Agent"
description: "Minimal"
skills:
  - name: single_skill
    description: "One skill"
version: "1.0.0"
status: active
---
"""


class TestParseAgentMd:
    def test_parse_valid_agent_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = _create_agent_md(tmpdir, "test_agent", VALID_AGENT_MD)
            cap = parse_agent_md(os.path.join(agent_dir, "agent.md"))

            assert cap is not None
            assert cap.name == "test_agent"
            assert cap.display_name == "Test Agent"
            assert cap.description == "A test agent for unit testing"
            assert cap.version == "1.0.0"
            assert cap.status == "active"
            assert len(cap.skills) == 2
            assert cap.skills[0].name == "do_something"
            assert cap.skills[1].name == "do_other"

    def test_parse_missing_file(self):
        cap = parse_agent_md("/nonexistent/path/agent.md")
        assert cap is None

    def test_parse_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = _create_agent_md(tmpdir, "bad", "No frontmatter here")
            cap = parse_agent_md(os.path.join(agent_dir, "agent.md"))
            assert cap is None

    def test_parse_missing_name(self):
        content = """---
display_name: "No Name"
description: "Missing name field"
version: "1.0.0"
status: active
---
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = _create_agent_md(tmpdir, "noname", content)
            cap = parse_agent_md(os.path.join(agent_dir, "agent.md"))
            assert cap is None


class TestDiscoverAgents:
    def test_discovers_active_agents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _create_agent_md(tmpdir, "agent_a", VALID_AGENT_MD)
            _create_agent_md(tmpdir, "agent_b", MINIMAL_AGENT_MD)

            caps = discover_agents(tmpdir)
            assert len(caps) == 2

    def test_skips_disabled_agents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _create_agent_md(tmpdir, "active", VALID_AGENT_MD)
            _create_agent_md(tmpdir, "disabled", DISABLED_AGENT_MD)

            caps = discover_agents(tmpdir)
            assert len(caps) == 1
            assert caps[0].name == "test_agent"

    def test_skips_template_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _create_agent_md(tmpdir, "_template", VALID_AGENT_MD)
            _create_agent_md(tmpdir, "real_agent", MINIMAL_AGENT_MD)

            caps = discover_agents(tmpdir)
            assert len(caps) == 1
            assert caps[0].name == "minimal"

    def test_skips_agents_without_agent_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _create_agent_md(tmpdir, "good", VALID_AGENT_MD)
            # Create dir without agent.md
            os.makedirs(os.path.join(tmpdir, "empty_agent"))

            caps = discover_agents(tmpdir)
            assert len(caps) == 1

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            caps = discover_agents(tmpdir)
            assert caps == []

    def test_nonexistent_directory(self):
        caps = discover_agents("/nonexistent/path")
        assert caps == []


class TestFormatCapabilities:
    def test_format_with_capabilities(self):
        caps = [
            AgentCapability(
                name="live_agent",
                display_name="Live Agent Support",
                description="Connects to live agents",
                skills=[Skill(name="connect", description="Connect to a human representative")],
            )
        ]
        result = format_capabilities(caps)
        assert "Live Agent Support" in result
        assert "Connect to a human representative" in result

    def test_format_empty(self):
        result = format_capabilities([])
        assert "still setting up" in result.lower() or "no services" in result.lower()

    def test_skips_main_agent(self):
        caps = [
            AgentCapability(name="main_agent", display_name="Nexus", description="Orchestrator", skills=[Skill(name="greet", description="Greet")]),
            AgentCapability(name="live_agent", display_name="Live Agent", description="Live", skills=[Skill(name="connect", description="Connect")]),
        ]
        result = format_capabilities(caps)
        assert "Live Agent" in result
        # main_agent should not appear as a listed capability
        assert "Nexus" not in result or "Live Agent" in result
