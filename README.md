# Nexus

Agentic conversational AI chatbot for banking and insurance domains. Built with Python, LangGraph, and AWS Bedrock Nova Pro.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [System Diagram](#system-diagram)
- [Conversation Flow](#conversation-flow)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)
- [Configuration](#configuration)
- [Extending Nexus](#extending-nexus)

---

## Overview

Nexus is a two-layer platform:

1. **Build-time agents** — AI coding assistants (Product Owner, Spec Writer, Architect, Dev, QA) that follow spec-driven development to build and maintain the chatbot
2. **Runtime agent** — a Python/LangGraph conversational chatbot that uses AWS Bedrock Nova Pro to classify intent, call domain tools, and respond in natural language

The runtime agent handles 30 intents across three domains:

| Domain | Intents | Examples |
|--------|---------|----------|
| **Banking** (10) | check_balance, transfer_money, view_transactions, report_fraud, freeze_card, activate_card, update_contact_info, open_account, close_account, dispute_transaction | "What is my balance?" |
| **Insurance** (10) | file_claim, check_claim_status, update_policy, get_policy_details, add_vehicle, remove_vehicle, request_quote, renew_policy, cancel_policy, roadside_assistance | "I need to file a claim" |
| **FAQ** (10) | hours_of_operation, contact_support, reset_password, app_help, website_help, fees_info, eligibility, locations, security_info, general_info | "What are your hours?" |

---

## Architecture

Nexus uses a **LangGraph StateGraph** — a directed graph where each node is a Python function that reads and writes to a shared state dictionary. Edges define the transitions between nodes, with conditional routing based on state values.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Nexus Platform                           │
│                                                                 │
│  ┌───────────────────┐          ┌────────────────────────────┐  │
│  │  Build-Time Layer │          │     Runtime Layer           │  │
│  │                   │          │                            │  │
│  │  .claude/agents/  │  builds  │  src/nexus/                │  │
│  │  ┌─────────────┐  │ ──────► │  ┌──────────────────────┐  │  │
│  │  │Product Owner│  │          │  │  LangGraph StateGraph │  │  │
│  │  │Spec Writer  │  │          │  │                      │  │  │
│  │  │Architect    │  │          │  │  entry → router →    │  │  │
│  │  │Dev          │  │          │  │  domain → tools →    │  │  │
│  │  │QA           │  │          │  │  respond → END       │  │  │
│  │  └─────────────┘  │          │  └──────────┬───────────┘  │  │
│  │                   │          │             │              │  │
│  │  specs/features/  │          │  ┌──────────▼───────────┐  │  │
│  │  (source of truth)│          │  │  AWS Bedrock          │  │  │
│  │                   │          │  │  Nova Pro LLM         │  │  │
│  └───────────────────┘          │  └──────────────────────┘  │  │
│                                 └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| **LLM Abstraction** | `src/nexus/llm/` | Factory pattern for swappable LLM backends. `BaseLLM` ABC with `BedrockLLM` implementation using the Converse API |
| **Graph Engine** | `src/nexus/graph/` | LangGraph StateGraph with 7 nodes and conditional edges |
| **Tool Registry** | `src/nexus/tools/` | Registry pattern mapping tool names to callable implementations. Mock tools return realistic data |
| **Session Memory** | `src/nexus/memory/` | Session store abstraction with in-memory implementation. Persists conversation history across turns |
| **Intent Definitions** | `src/nexus/intents/` | YAML files defining 30 intents with sample utterances |
| **Instructions** | `src/nexus/instructions/` | YAML domain-specific behavioral rules (e.g., "mask account numbers", "confirm high-value transfers") |
| **Prompts** | `src/nexus/prompts/` | Text template files with `{variable}` placeholders for LLM calls |

---

## System Diagram

### Runtime Data Flow

```
                    User Input
                        │
                        ▼
              ┌─────────────────┐
              │   CLI / API     │  (app.py)
              └────────┬────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │     LangGraph Engine     │
         │                         │
         │  ┌───────────────────┐  │     ┌──────────────────────┐
         │  │   entry node      │  │     │  Session Store        │
         │  │ (load session)    │◄─┼────►│  (InMemoryStore)      │
         │  └────────┬──────────┘  │     └──────────────────────┘
         │           │             │
         │  ┌────────▼──────────┐  │     ┌──────────────────────┐
         │  │   router node     │  │     │  AWS Bedrock          │
         │  │ (classify intent) │◄─┼────►│  Nova Pro LLM         │
         │  └────────┬──────────┘  │     │  (Converse API)       │
         │           │             │     └──────────────────────┘
         │    ┌──────┼──────┬──────┤
         │    ▼      ▼      ▼     ▼│
         │ banking insur.  faq  escal.│   ┌──────────────────────┐
         │ handler handler handler hand│   │  Intent Definitions   │
         │    │      │      │      │  │   │  (YAML)               │
         │    └──┬───┘──────┘      │  │◄──│  30 intents           │
         │       │                 │  │   └──────────────────────┘
         │  ┌────▼──────────┐     │  │
         │  │ tool_execute  │     │  │   ┌──────────────────────┐
         │  │ (call tools)  │◄────┼──┼──►│  Tool Registry        │
         │  └────────┬──────┘     │  │   │  banking/ insurance/  │
         │           │            │  │   │  faq/ tools           │
         │  ┌────────▼──────────┐ │  │   └──────────────────────┘
         │  │   respond node   │  │  │
         │  │ (format answer)  │◄─┼──┤   ┌──────────────────────┐
         │  └────────┬─────────┘  │  │   │  Instructions (YAML)  │
         │           │            │  └──►│  Domain rules          │
         └───────────┼────────────┘      └──────────────────────┘
                     │
                     ▼
              Agent Response
```

### LLM Integration Pattern

```
┌──────────────────┐     ┌────────────────┐     ┌───────────────────┐
│   BaseLLM (ABC)  │     │  LLMFactory    │     │  Config           │
│                  │     │                │     │                   │
│  invoke()        │◄────│  create() ─────┼────►│  LLM_PROVIDER     │
│  invoke_with_    │     │  returns the   │     │  BEDROCK_MODEL_ID │
│    tools()       │     │  right impl    │     │  AWS_REGION       │
└───────┬──────────┘     └────────────────┘     └───────────────────┘
        │
        ▼
┌──────────────────┐
│  BedrockLLM      │
│                  │
│  boto3.client    │───────► AWS Bedrock Runtime
│  ("bedrock-      │         Converse API
│   runtime")      │         model: amazon.nova-pro-v1:0
│  .converse()     │
└──────────────────┘
```

---

## Conversation Flow

### Detailed Node-by-Node Flow

```
Step 1: ENTRY
  ┌──────────────────────────────────────────────┐
  │ Load session from store (user_id + session_id)│
  │ Populate conversation_history into state      │
  │ Append user message to history                │
  └──────────────┬───────────────────────────────┘
                 │
Step 2: ROUTER   ▼
  ┌──────────────────────────────────────────────┐
  │ Build routing prompt with:                    │
  │   - All 30 intent definitions + utterances    │
  │   - Conversation history for context          │
  │ Send to LLM → parse JSON response:            │
  │   { intent, domain, confidence, missing_slots }│
  │ If confidence < 0.7 → set should_escalate     │
  └──────────────┬───────────────────────────────┘
                 │
Step 3: DOMAIN   ▼  (conditional edge: route_by_intent)
  ┌──────────┬──────────┬──────────┬─────────────┐
  │ banking  │insurance │   faq    │ escalation   │
  │          │          │          │              │
  │ Map      │ Map      │ Direct   │ Format       │
  │ intent   │ intent   │ FAQ      │ handoff      │
  │ to tool  │ to tool  │ lookup   │ message      │
  │ + args   │ + args   │          │              │
  └────┬─────┴────┬─────┴────┬─────┴──────┬──────┘
       │          │          │            │
Step 4: TOOL EXECUTE  ▼  (conditional edge: needs_tool_execution)
  ┌──────────────────────────────────────────────┐
  │ Look up tool_name in ToolRegistry             │
  │ Call tool.execute(tool_args)                  │
  │ Store result in tool_result (or tool_error)   │
  └──────────────┬───────────────────────────────┘
                 │
Step 5: RESPOND  ▼
  ┌──────────────────────────────────────────────┐
  │ Build response prompt with:                   │
  │   - Tool result data                          │
  │   - User message + conversation history       │
  │ Send to LLM → get natural language response   │
  │ Save session (append to history, update intent)│
  │ Return response_text                          │
  └──────────────┬───────────────────────────────┘
                 │
                 ▼
                END
```

### Example Conversation Trace

```
User: "What is my account balance?"

  entry    → loads session for user-001, appends message to history
  router   → LLM classifies: { intent: "check_balance", domain: "banking", confidence: 0.95 }
  banking  → maps check_balance → tool: get_account_balance, args: { user_id: "user-001" }
  tool_exec→ calls GetAccountBalance.execute() → { balance: 4250.75, account: "****4521" }
  respond  → LLM generates: "Your checking account (****4521) has a balance of $4,250.75."

User: "I want to file a claim"

  entry    → loads session (now has 1 turn of history)
  router   → LLM classifies: { intent: "file_claim", domain: "insurance", confidence: 0.92 }
  insurance→ maps file_claim → tool: file_claim, args: { user_id: "user-001" }
  tool_exec→ calls FileClaim.execute() → { claim_id: "CLM-2026-08234", status: "submitted" }
  respond  → LLM generates: "Your claim CLM-2026-08234 has been submitted successfully."
```

### State Schema

The `AgentState` TypedDict flows through every node:

```
AgentState
├── Input
│   ├── user_message: str
│   ├── user_id: str
│   └── session_id: str
├── Session Context
│   ├── conversation_history: list[dict]
│   ├── preferences: dict
│   └── last_intent: str
├── Routing
│   ├── current_intent: str           # e.g. "check_balance"
│   ├── intent_domain: str            # "banking" | "insurance" | "faq" | "escalation"
│   └── routing_confidence: float     # 0.0 - 1.0
├── Tool Execution
│   ├── tool_name: str                # e.g. "get_account_balance"
│   ├── tool_args: dict
│   ├── tool_result: dict
│   └── tool_error: str
├── Response
│   ├── response_text: str
│   ├── needs_clarification: bool
│   └── missing_slots: list[str]
└── Control
    ├── error_count: int
    └── should_escalate: bool
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.11+ | Runtime and tooling |
| Orchestration | LangGraph | StateGraph for conversation flow |
| LLM | AWS Bedrock Nova Pro (`amazon.nova-pro-v1:0`) | Intent classification and response generation |
| LLM Integration | langchain-aws, boto3 | Bedrock Converse API |
| Config | pydantic-settings | Type-safe settings from `.env` |
| Data | PyYAML | Intent and instruction definitions |
| Testing | pytest | Unit and integration tests |
| Linting | ruff | Code quality and formatting |

---

## Project Structure

```
nexus/
├── CLAUDE.md                              # AI dev workflow instructions
├── README.md                              # This file
├── PRD.md                                 # Product Requirements Document
├── Makefile                               # Build commands
├── pyproject.toml                         # Python project config + deps
├── requirements.txt                       # Pinned dependency versions
├── .env.example                           # Environment variable template
├── .gitignore
│
├── .claude/agents/                        # Build-time AI agent instructions
│   ├── product-owner.md                   # Generates Acceptance Criteria
│   ├── spec-writer.md                     # Writes Gherkin specs
│   ├── architect.md                       # Designs system components
│   ├── dev.md                             # Implements Python code
│   └── qa.md                              # Validates against specs
│
├── specs/features/                        # Gherkin specs (source of truth)
│   ├── intent_routing.feature
│   ├── banking_balance.feature
│   └── insurance_claim.feature
│
├── src/nexus/
│   ├── app.py                             # CLI entry point
│   ├── config.py                          # pydantic-settings config
│   │
│   ├── llm/                               # LLM abstraction layer
│   │   ├── base.py                        # BaseLLM abstract class
│   │   ├── bedrock.py                     # BedrockLLM (Converse API)
│   │   └── factory.py                     # LLMFactory
│   │
│   ├── graph/                             # LangGraph state machine
│   │   ├── state.py                       # AgentState TypedDict
│   │   ├── agent.py                       # build_graph() — wires nodes + edges
│   │   ├── edges.py                       # route_by_intent, needs_tool_execution
│   │   └── nodes/
│   │       ├── entry.py                   # Load session
│   │       ├── router.py                  # LLM intent classification
│   │       ├── banking.py                 # Banking domain handler
│   │       ├── insurance.py               # Insurance domain handler
│   │       ├── faq.py                     # FAQ handler
│   │       ├── escalation.py              # Human escalation
│   │       └── respond.py                 # Format + save response
│   │
│   ├── tools/                             # Tool implementations
│   │   ├── base.py                        # Tool protocol
│   │   ├── registry.py                    # ToolRegistry
│   │   ├── banking/                       # 5 banking tools (mock)
│   │   ├── insurance/                     # 4 insurance tools (mock)
│   │   └── faq/                           # 1 FAQ tool
│   │
│   ├── memory/                            # Session management
│   │   ├── session.py                     # Session dataclass
│   │   └── store.py                       # InMemoryStore
│   │
│   ├── prompts/                           # LLM prompt templates
│   │   ├── system_prompt.txt
│   │   ├── routing_prompt.txt
│   │   └── response_prompt.txt
│   │
│   ├── intents/                           # YAML intent definitions
│   │   ├── banking.yaml                   # 10 banking intents
│   │   ├── insurance.yaml                 # 10 insurance intents
│   │   └── faq.yaml                       # 10 FAQ intents
│   │
│   └── instructions/                      # Domain behavioral rules
│       ├── global.yaml
│       ├── banking.yaml
│       ├── insurance.yaml
│       └── escalation.yaml
│
└── tests/
    ├── conftest.py                        # MockLLM + shared fixtures
    ├── unit/                              # 14 unit tests
    └── integration/                       # 5 integration tests
```

---

## Development Workflow

Nexus uses **spec-driven development** with AI coding assistants:

```
 ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
 │Product Owner  │     │ Spec Writer  │     │  Architect   │
 │              │────►│              │────►│              │
 │ Writes ACs   │     │ Given/When/  │     │ Designs      │
 │ from feature │     │ Then specs   │     │ graph nodes, │
 │ requests     │     │ in specs/    │     │ state, tools │
 └──────────────┘     └──────────────┘     └──────┬───────┘
                                                   │
                      ┌──────────────┐     ┌───────▼──────┐
                      │     QA       │     │    Dev       │
                      │              │◄────│              │
                      │ Validates    │     │ Implements   │
                      │ code against │     │ Python code  │
                      │ specs        │     │ per design   │
                      └──────────────┘     └──────────────┘
```

Agent instructions live in `.claude/agents/`. Gherkin specs in `specs/features/` are the **source of truth** — if a code change breaks a spec, the code must be fixed.

---

## Getting Started

### Prerequisites

- Python 3.11+ (tested with 3.12)
- AWS account with Bedrock access enabled for `amazon.nova-pro-v1:0`
- AWS credentials configured (`~/.aws/credentials` or environment variables)

### Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd nexus

# 2. Set up virtualenv and install all dependencies
make setup

# 3. Configure environment
cp .env.example .env
# Edit .env with your AWS region and any overrides

# 4. Run the tests (no AWS credentials needed — uses mock LLM)
make test

# 5. Start the chatbot CLI (requires AWS credentials)
make run
```

### Manual Setup (without Make)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install project + dev dependencies
pip install -e ".[dev]"

# Or use pinned requirements
pip install -r requirements.txt
pip install -e .

# Run
python -m nexus.app
```

### Available Commands

| Command          | Description                              |
|------------------|------------------------------------------|
| `make setup`     | Create venv and install all dependencies |
| `make test`      | Run pytest (unit + integration)          |
| `make lint`      | Check code with ruff                     |
| `make format`    | Auto-format code with ruff               |
| `make typecheck` | Run mypy type checker                    |
| `make run`       | Start the CLI chat loop                  |
| `make clean`     | Remove venv, caches, build artifacts     |

---

## Running Tests

All tests use a `MockLLM` — **no AWS credentials needed**.

```bash
# All tests (19 total: 14 unit + 5 integration)
make test

# Specific test file
venv/bin/pytest tests/unit/test_router_node.py -v

# With coverage
venv/bin/pytest tests/ --cov=nexus --cov-report=term-missing
```

---

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable            | Default                  | Description                          |
|---------------------|--------------------------|--------------------------------------|
| `AWS_REGION`        | `us-east-1`             | AWS region for Bedrock               |
| `BEDROCK_MODEL_ID`  | `amazon.nova-pro-v1:0`  | Bedrock model to use                 |
| `LLM_PROVIDER`      | `bedrock`               | LLM backend (`bedrock`)             |
| `SESSION_STORE_TYPE` | `memory`                | Session storage (`memory`)           |
| `LOG_LEVEL`         | `INFO`                  | Logging level                        |

### AWS Bedrock Setup

1. Enable Bedrock model access for `amazon.nova-pro-v1:0` in your AWS region
2. Configure credentials via one of:
   - `aws configure` (sets `~/.aws/credentials`)
   - Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - IAM role (EC2/ECS/Lambda)
3. Required IAM permission: `bedrock:InvokeModel`

---

## Extending Nexus

### Adding a New Intent

1. Add the intent to the appropriate YAML file in `src/nexus/intents/`:
   ```yaml
   - name: my_new_intent
     description: What this intent does
     sample_utterances:
       - "Example phrase 1"
       - "Example phrase 2"
   ```
2. Create a tool in the matching domain directory (`src/nexus/tools/<domain>/`)
3. Register it in the domain's `register_*_tools()` function
4. Add a Gherkin spec in `specs/features/`
5. Add tests

### Adding a New Domain

1. Create `src/nexus/intents/<domain>.yaml`
2. Create `src/nexus/instructions/<domain>.yaml`
3. Create `src/nexus/tools/<domain>/` with tool implementations
4. Create `src/nexus/graph/nodes/<domain>.py` handler node
5. Register the node and edge in `src/nexus/graph/agent.py`
6. Update `route_by_intent` in `src/nexus/graph/edges.py`

### Swapping the LLM Provider

The factory pattern in `src/nexus/llm/factory.py` allows swapping backends by changing `LLM_PROVIDER` in `.env`. To add a new provider:

1. Create a class extending `BaseLLM` in `src/nexus/llm/`
2. Implement `invoke()` and `invoke_with_tools()`
3. Register it in `LLMFactory.create()`
