# Nexus

**Multi-Agent Conversational AI Platform for Financial Services**

Nexus is a fully agentic, orchestrator-based chatbot platform for financial institutions (banking, insurance, investment). It uses a hierarchical delegation pattern where a Main Agent discovers and routes to specialized sub-agents.

## Key Concepts

- **Orchestrator Pattern** — Main Agent discovers skills from sub-agents, uses LLM tool-calling to route
- **Spec-Driven Development** — Every component has a spec written and approved before implementation
- **Self-Describing Agents** — Each agent publishes `agent.md` with its skills, discovered at startup
- **Isolated Histories** — Each agent owns its conversation history; delegation produces summary handoffs
- **LangGraph Standard** — Every agent uses a LangGraph StateGraph for consistency

## Tech Stack

- **Python 3.11+**
- **LangGraph** — Agent state machines
- **AWS Bedrock / Amazon Nova Pro** — LLM provider
- **websockets** — LiveAgent contact center bridge

## Quick Start

### Using Make (recommended)

```bash
make setup           # Create .venv and install dependencies (run once)
make run             # Run the member CLI (default: MEMBER_ID=M12345)
make run-debug       # Run with debug panel enabled
make contact-center  # Start the contact center WebSocket server
make msr-cli         # Start the MSR console (MSR_QUEUE=banking MSR_NAME=Alice)
make test            # Run the test suite
make help            # Show all available targets
```

Override variables on the fly:
```bash
make run MEMBER_ID=M99999
make msr-cli MSR_QUEUE=insurance MSR_NAME="Bob"
```

### Manual Setup

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the member CLI
python app.py --member-id M12345

# Run the contact center (separate terminals)
python scripts/run_contact_center.py
python contact_center/msr_console.py --queue banking --name "Alice"
```

> **Note:** Always activate the virtual environment (`source .venv/bin/activate`) before running any commands in a new terminal session. The Makefile handles this automatically via `.venv/bin/python`.

## Project Structure

```
nexus/
├── specs/              # Source of truth — spec documents
├── core/               # Core infrastructure (session, discovery, LLM, base agent)
├── agents/             # Agent modules (main_agent, live_agent, _template)
├── contact_center/     # Mock contact center (WebSocket server + MSR console)
├── scripts/            # Scaffolding and utility scripts
└── tests/              # Test suite
```

## Development Workflow

1. **Write Spec** → `specs/<component>.spec.md`
2. **Review & Approve** → Confirm acceptance criteria
3. **Implement** → Code follows the spec exactly
4. **Test** → Tests derived from acceptance criteria
5. **Verify** → Run tests, confirm spec is satisfied

See `specs/README.md` for the spec format guide.
