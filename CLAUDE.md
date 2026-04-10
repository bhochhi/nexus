# Nexus — Development Guide

## Project Overview

Nexus is an agentic conversational AI chatbot for banking and insurance domains. It uses a two-layer architecture:

- **Build-time agents**: AI coding assistants (in `.claude/agents/`) that follow spec-driven development
- **Runtime agent**: Python/LangGraph chatbot using AWS Bedrock Nova Pro LLM

## Architecture

The runtime agent is a LangGraph `StateGraph` with this topology:

```
entry → router → [banking | insurance | faq | escalation] → tool_execute → respond → END
```

- **Router**: LLM-based intent classification across 30 intents (10 banking, 10 insurance, 10 FAQ)
- **Domain handlers**: Map intents to tools, enforce domain-specific rules
- **Tool execution**: Registry-based dispatch to mock (later real) API tools
- **Response**: LLM generates natural language from tool results

## Tech Stack

- Python 3.11+, LangGraph, langchain-aws, boto3
- AWS Bedrock with Nova Pro (`amazon.nova-pro-v1:0`) as runtime LLM
- pydantic-settings for config, PyYAML for intent/instruction loading
- pytest for testing, ruff for linting

## Slash Commands (Skills)

These are user-triggered workflows in `.claude/commands/`. Use them to drive the spec-driven development pipeline:

| Command | Purpose | Example |
|---------|---------|---------|
| `/project:plan` | Generate Acceptance Criteria from a feature request | `/project:plan add dispute resolution flow` |
| `/project:spec-write` | Convert ACs into Gherkin specs (Given/When/Then) | `/project:spec-write <paste ACs>` |
| `/project:architect` | Design system components for a feature | `/project:architect design dispute tool and graph node` |
| `/project:dev` | Implement code that satisfies specs | `/project:dev implement dispute_transaction tool` |
| `/project:qa` | Validate implementation against specs | `/project:qa banking domain` |

### Typical Workflow

```
/project:plan "users should be able to dispute a transaction"
  → Produces ACs (AC-1, AC-2, ...)

/project:spec-write <ACs from above>
  → Produces specs/features/banking_dispute.feature

/project:architect "design dispute transaction flow"
  → Produces architecture: new tool, node changes, state fields

/project:dev "implement dispute transaction per architect design"
  → Produces src/nexus/tools/banking/dispute_transaction.py + tests

/project:qa
  → Validates: tests pass, lint clean, specs satisfied
```

## Agents (Sub-Agents)

These are specialized AI workers in `.claude/agents/` with distinct personas. Each has a `title`, `description`, responsibilities, and project context in YAML frontmatter:

| Agent | File | Triggered By | Produces |
|-------|------|-------------|----------|
| **Product Owner** | `.claude/agents/product-owner.md` | `/project:plan` | Acceptance Criteria |
| **Spec Writer** | `.claude/agents/spec-writer.md` | `/project:spec-write` | Gherkin `.feature` files |
| **Architect** | `.claude/agents/architect.md` | `/project:architect` | Architecture designs |
| **Developer** | `.claude/agents/dev.md` | `/project:dev` | Python code + tests |
| **QA Engineer** | `.claude/agents/qa.md` | `/project:qa` | Validation reports |

### How Commands and Agents Relate

**Commands** are user-facing skills — they define *what* to do (the prompt template with `$ARGUMENTS`).
**Agents** are specialized workers — they define *who* does it (persona, rules, context).

When you run `/project:plan "add balance transfer"`:
1. The command template in `.claude/commands/plan.md` is loaded
2. `$ARGUMENTS` is replaced with "add balance transfer"
3. Claude operates with the Product Owner agent's persona and context
4. Output: structured ACs ready for the next step

## Development Workflow (Spec-Driven)

```
Product Owner → Spec Writer → Architect → Dev → QA
    (ACs)      (Given/When/Then) (Design)  (Code) (Validate)
```

Agent instructions live in `.claude/agents/`. Specs in `specs/features/` are the source of truth.

## Key Commands

```
make setup      # Create venv, install deps
make test       # Run pytest
make lint       # Run ruff linter
make format     # Auto-format with ruff
make run        # Start CLI chat loop
make clean      # Remove build artifacts
```

## Key Directories

- `src/nexus/graph/` — LangGraph state machine (nodes, edges, state schema)
- `src/nexus/llm/` — LLM abstraction (base, bedrock, factory)
- `src/nexus/tools/` — Tool implementations by domain (banking, insurance, faq)
- `src/nexus/intents/` — Intent YAML definitions
- `src/nexus/instructions/` — Domain behavioral rules (YAML)
- `src/nexus/prompts/` — LLM prompt templates
- `src/nexus/memory/` — Session management
- `specs/features/` — Gherkin specs (source of truth)
- `tests/` — Unit and integration tests

## Conventions

- Factory pattern for LLM providers (swappable backends)
- Registry pattern for tool dispatch
- YAML for intent and instruction definitions
- Prompt templates in `.txt` files with `{variable}` placeholders
- All mock tools return realistic data structures
- Specs (Given/When/Then) are the contract; code must satisfy them
