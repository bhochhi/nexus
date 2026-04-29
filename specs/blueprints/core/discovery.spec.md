# Spec: Agent Discovery

## Purpose
Scans the `agents/` directory at startup, reads `agent.md` from each agent module, parses the YAML frontmatter, and builds a registry of `AgentCapability` objects. This registry is what the orchestrator uses to know what skills are available across the platform.

## Interface Contract

### `discover_agents(agents_dir: str) -> List[AgentCapability]`
- Scan all immediate subdirectories under `agents_dir`
- Skip directories starting with `_` (e.g., `_template/`)
- For each subdirectory, look for `agent.md`
- Parse YAML frontmatter from `agent.md` (between `---` delimiters)
- Build an `AgentCapability` from the parsed YAML
- Only include agents with `status: active` (skip `disabled` and `beta` for v1)
- Return the list of discovered capabilities
- If `agent.md` is missing or malformed, log a warning and skip that agent
- Never crash — discovery failures are non-fatal

### `parse_agent_md(filepath: str) -> Optional[AgentCapability]`
- Read the file at `filepath`
- Extract YAML frontmatter (content between first two `---` lines)
- Parse required fields: `name`, `display_name`, `description`, `skills`, `version`, `status`
- Parse `skills` as a list of objects with `name` and `description`
- Set `module_path` to the directory containing the agent.md
- Return `AgentCapability` or `None` if parsing fails

### `format_capabilities(capabilities: List[AgentCapability]) -> str`
- Format the list of capabilities into a human-readable string
- Used by the orchestrator to tell the member what's available
- Example output:
  ```
  Here's what I can help with today:
  • Live Agent Support — Connect to a human representative in Banking, Insurance, or Advice queue
  ```

## agent.md YAML Schema

```yaml
---
name: string              # Required. Snake_case identifier.
display_name: string      # Required. Human-readable name.
description: string       # Required. What this agent does.
skills:                   # Required. List of skills.
  - name: string          # Required. Snake_case skill identifier.
    description: string   # Required. Human-readable description.
version: string           # Required. Semver string.
status: string            # Required. "active" | "beta" | "disabled"
---

# Markdown body (optional — free-form documentation)
```

## Acceptance Criteria

- [ ] Discovers all agent directories under `agents/`
- [ ] Skips directories starting with `_`
- [ ] Parses YAML frontmatter correctly from agent.md
- [ ] Builds `AgentCapability` with all fields populated
- [ ] `skills` field contains list of `Skill` objects with name + description
- [ ] `module_path` points to the agent's directory
- [ ] Only returns agents with `status: active`
- [ ] Missing `agent.md` logs warning, doesn't crash
- [ ] Malformed YAML logs warning, doesn't crash
- [ ] Missing required fields logs warning, skips agent
- [ ] `format_capabilities` produces readable output
- [ ] Returns empty list if no agents found (doesn't crash)

## Examples

```python
# Given agents/ contains main_agent/ and live_agent/ with valid agent.md files:
capabilities = discover_agents("agents/")
assert len(capabilities) == 2
assert capabilities[0].name == "main_agent"
assert capabilities[1].name == "live_agent"
assert len(capabilities[1].skills) == 1
assert capabilities[1].skills[0].name == "connect_to_live_agent"

# Given agents/_template/ exists:
# It is skipped (starts with _)

# Given agents/broken_agent/ has no agent.md:
# Warning logged, agent skipped, no crash
```

## Dependencies
- `core.types` (AgentCapability, Skill)
- `pyyaml` or stdlib-only YAML parsing (frontmatter is simple enough for regex)

## Notes
- v1 uses startup-only discovery. Hot-reload is a future enhancement.
- We should avoid adding `pyyaml` as a dependency if possible. The YAML frontmatter is simple key-value pairs and lists — consider a lightweight parser or regex-based extraction.
