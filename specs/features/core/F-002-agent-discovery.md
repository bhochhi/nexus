# F-002: Agent Discovery & Capability Awareness

## Description
The system automatically discovers what capabilities (skills) are available by scanning all agent modules at startup. Each agent publishes a manifest file (`agent.md`) describing its skills. The orchestrator reads these manifests and becomes aware of what services it can offer — without any hardcoded knowledge of sub-agents.

## Business Value
New capabilities can be added by simply dropping a new agent module into the system — no changes to the orchestrator needed. This makes the platform extensible and reduces time-to-market for new features. Business teams can define capabilities in plain-language agent.md files.

## User Story
As a **platform operator**, I want the system to automatically discover new agent capabilities at startup, so that I can add new services without modifying the orchestrator code.

## Acceptance Criteria
- [ ] System scans the `agents/` directory at startup for agent modules
- [ ] Each agent module contains an `agent.md` file with a standardized format
- [ ] `agent.md` includes: agent name, display name, description, list of skills, version, status
- [ ] Each skill has a name and human-readable description
- [ ] Only agents with `status: active` are loaded
- [ ] Agents with `status: disabled` or `status: beta` are skipped
- [ ] Template directories (prefixed with `_`) are skipped
- [ ] Missing or malformed `agent.md` files are skipped with a warning (no crash)
- [ ] The orchestrator can list all discovered capabilities in a member-friendly format
- [ ] Discovery happens once at startup (v1); hot-reload is a future enhancement

## Scenarios

### Happy Path
1. `agents/` contains `main_agent/agent.md` and `live_agent/agent.md`
2. On startup, system reads both manifests
3. Orchestrator knows it can offer: greeting, skill-based routing, live agent connection
4. Member asks "What can you do?" → system lists discovered skills

### Adding a New Agent
1. Developer creates `agents/billing_agent/` with `agent.md`
2. On next app restart, system discovers the new billing agent
3. Orchestrator now includes billing skills in its capability list
4. No code changes to orchestrator required

### Edge Cases
- What if `agents/` directory is empty? → System starts with no sub-agent capabilities, orchestrator still functions (greeting only)
- What if `agent.md` has invalid YAML? → Skip that agent, log warning, continue
- What if two agents declare the same skill name? → Both are loaded, orchestrator includes both (LLM decides based on context)

## Dependencies
- None

## Notes
- The `agent.md` format uses YAML frontmatter (simple key-value pairs between `---` delimiters) followed by free-form markdown documentation.
- v1: startup-only discovery. Future: file watcher or registry service for hot-reload.
