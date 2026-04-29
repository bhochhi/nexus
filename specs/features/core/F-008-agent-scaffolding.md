# F-008: Agent Scaffolding

## Description
A CLI script that creates a new agent module from a standardized template. Running the script generates all required files (agent.md, persona.md, instruction.md, agent.py, graph.py, nodes.py, tools.py, state.py) with sensible defaults, ready for the developer to customize.

## Business Value
Consistency across agents reduces onboarding time for new developers and ensures every agent follows the same pattern. A 30-second scaffold replaces 15 minutes of copy-pasting and remembering file structures.

## User Story
As a **developer**, I want to create a new agent with a single command, so that I get the correct file structure with all required files and can focus on writing the agent's logic.

## Acceptance Criteria
- [ ] Script creates a new directory under `agents/<agent_name>/`
- [ ] All required files are generated: agent.md, persona.md, instruction.md, agent.py, graph.py, nodes.py, tools.py, state.py, __init__.py
- [ ] `agent.md` is populated with the provided name, display_name, and description
- [ ] `agent.py` extends BaseAgent with the correct class name
- [ ] `graph.py` contains a minimal LangGraph (START → process → END)
- [ ] `tools.py` contains an empty tools list
- [ ] Script accepts agent_name as required argument
- [ ] Script accepts optional --display-name and --description flags
- [ ] Script refuses to overwrite an existing agent directory
- [ ] Newly created agent is automatically discovered on next app startup (no code changes)

## Scenarios

### Happy Path
```bash
python scripts/create_agent.py billing_agent \
  --display-name "Billing Agent" \
  --description "Handles billing inquiries, payment setup, and payment updates"
```
Creates `agents/billing_agent/` with all 9 files.

### Agent Already Exists
```bash
python scripts/create_agent.py live_agent
# Error: Agent 'live_agent' already exists at agents/live_agent/
```

### Verify Discovery
1. Run scaffolding script to create `billing_agent`
2. Restart app
3. Ask "What can you do?" → response includes Billing Agent skills

## Dependencies
- F-002: Agent Discovery & Capability Awareness (the created agent must be discoverable)

## Notes
- Templates live in `agents/_template/` with `.template` extension
- The script reads templates, substitutes variables (name, display_name, description), and writes the output files
