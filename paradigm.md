You are an AI engineering assistant tasked with generating the initial project structure and baseline implementation for an agentic chatbot platform named Nexus.

The architecture and code implementation should follow spec-driven development. So, First, we need to build AI workflow that would have Custome Agents with specialize skills. like Architect, Dev, QA, Spec writer in Given when Then format, along with Product owner the gives high help ACs as requirements. Dev need to write the code in python to build the Agentic ChatBot. this conversational chat bot may use langgraph to orchrestrate the conversation dialog so that it can communicate with users and conversational agent. THis conversational Agent should use bedrock to integrate with nova llm. 
the start with simple one conversation Agent has skills or intents for answering question in banking or insurance domain. we can later explain our runtime agents into domain specific agents. one for banking and another for insurance. for now one agentic bot conversationalAgent which will orchrastrate the dialog between user and LLM and will have ability to call the tools/api call to get user specific data 

let's start with planning how will the project structure looks like. how will these coding or development agent looks like that will help build the conversational Agent. remember, we can use claude models or openai model during build time to make a chatbot but chatbot itself need to use nova pro llm through bedrock. and use pythong if you need langGraph framework to build such convoAgent. 

Now let me write the final plan file synthesizing everything from the exploration and design phases.The plan is ready. Here's a quick summary of what it covers:

**Two layers:**
- **Build-time agents** (`.claude/agents/`) — Product Owner, Spec Writer, Architect, Dev, QA as markdown instruction files driving spec-driven development
- **Runtime chatbot** (`src/nexus/`) — Python/LangGraph StateGraph with nodes for entry, routing, banking/insurance/faq handlers, tool execution, and response formatting, all powered by Bedrock Nova Pro

**Key decisions:**
- Bedrock Converse API (not `invoke_model`) for native tool-calling
- Single graph with conditional edges (simple start, extractable later)
- Python tools in-process (not Go Lambdas from copilot branch)
- Factory pattern for LLM swapping during dev/test
- Carries forward the 30 intent YAMLs, prompts, and instructions from the existing copilot branch

**7 implementation phases** from scaffolding through API layer, with verification steps at each stage.

Here is Claude's plan:

# Nexus: Project Structure & Baseline Implementation Plan

## Context

Nexus is an agentic conversational AI chatbot platform for banking and insurance domains. The project has two layers:

1. **Build-time AI agents** — instruction files that guide AI coding assistants (Claude Code) through spec-driven development: Product Owner, Spec Writer, Architect, Dev, QA
2. **Runtime conversational agent** — a Python/LangGraph chatbot that uses AWS Bedrock Nova Pro LLM, with tool-calling for user-specific data

The repo is currently a blank slate on the `claude/create-structure` branch (only `README.md` exists). A parallel `copilot/create-nexus-project-structure` branch has a Go-based scaffold with useful YAML definitions (30 intents, prompts, instructions) that we'll carry forward and adapt to Python/LangGraph.

**Key constraint:** Build-time agents can use Claude/OpenAI. The runtime chatbot MUST use Nova Pro via Bedrock.

---

## Project Structure

```
nexus/
├── CLAUDE.md                              # Top-level AI dev workflow instructions
├── README.md                              # Project overview, setup, usage
├── PRD.md                                 # Product Requirements Document
├── Makefile                               # setup, test, lint, format, run, clean
├── pyproject.toml                         # Python project config + dependencies
├── .env.example                           # Environment variable template
├── .gitignore                             # Python/venv/cache ignores
│
├── .claude/
│   └── agents/                            # Build-time AI agent instructions
│       ├── product-owner.md               # Generates Acceptance Criteria
│       ├── spec-writer.md                 # Writes Given/When/Then specs
│       ├── architect.md                   # Designs components & graph topology
│       ├── dev.md                         # Implements Python code
│       └── qa.md                          # Validates against specs
│
├── specs/
│   └── features/                          # Gherkin specs (source of truth)
│       ├── intent_routing.feature
│       ├── banking_balance.feature
│       └── insurance_claim.feature
│
├── src/
│   └── nexus/
│       ├── __init__.py
│       ├── app.py                         # Entry point: CLI chat loop
│       ├── config.py                      # pydantic-settings + .env loading
│       │
│       ├── llm/                           # LLM abstraction layer
│       │   ├── __init__.py
│       │   ├── base.py                    # Abstract BaseLLM (invoke, invoke_with_tools)
│       │   ├── bedrock.py                 # Bedrock Nova Pro via Converse API
│       │   └── factory.py                 # LLMFactory for swappable backends
│       │
│       ├── graph/                         # LangGraph conversation orchestration
│       │   ├── __init__.py
│       │   ├── state.py                   # AgentState TypedDict
│       │   ├── agent.py                   # build_graph(): StateGraph construction
│       │   ├── edges.py                   # Conditional edge functions
│       │   └── nodes/                     # Graph node functions
│       │       ├── __init__.py
│       │       ├── entry.py              # Load session, prepare context
│       │       ├── router.py             # LLM-based intent classification
│       │       ├── banking.py            # Banking domain handler
│       │       ├── insurance.py          # Insurance domain handler
│       │       ├── faq.py                # FAQ handler
│       │       ├── escalation.py         # Human escalation handler
│       │       └── respond.py            # Format response, save session
│       │
│       ├── tools/                         # Tool/API calling framework
│       │   ├── __init__.py
│       │   ├── base.py                    # Tool protocol
│       │   ├── registry.py                # Name -> callable registry
│       │   ├── banking/                   # get_account_balance, transfer_funds, etc.
│       │   │   └── __init__.py
│       │   ├── insurance/                 # file_claim, check_claim_status, etc.
│       │   │   └── __init__.py
│       │   └── faq/                       # answer_faq
│       │       └── __init__.py
│       │
│       ├── memory/                        # Session management
│       │   ├── __init__.py
│       │   ├── session.py                 # Session dataclass
│       │   └── store.py                   # Abstract store + InMemoryStore
│       │
│       ├── prompts/                       # LLM prompt templates
│       │   ├── system_prompt.txt
│       │   ├── routing_prompt.txt
│       │   ├── response_prompt.txt
│       │   └── loader.py                  # Template loading + formatting
│       │
│       ├── intents/                       # Intent definitions (YAML)
│       │   ├── banking.yaml               # 10 banking intents
│       │   ├── insurance.yaml             # 10 insurance intents
│       │   ├── faq.yaml                   # 10 FAQ intents
│       │   └── loader.py                  # YAML -> Python objects
│       │
│       └── instructions/                  # Domain behavioral rules (YAML)
│           ├── global.yaml
│           ├── banking.yaml
│           ├── insurance.yaml
│           ├── escalation.yaml
│           └── loader.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py                        # MockLLM, mock tools, shared fixtures
    ├── unit/
    │   ├── test_config.py
    │   ├── test_llm_bedrock.py
    │   ├── test_router_node.py
    │   ├── test_tool_registry.py
    │   └── test_session.py
    └── integration/
        ├── test_graph_flow.py             # End-to-end graph with mock LLM
        └── test_routing_accuracy.py
```

---

## Build-Time Agents (Layer 1)

These are markdown instruction files in `.claude/agents/` that define specialized roles for AI-assisted spec-driven development.

### Development Workflow
```
Product Owner  →  Spec Writer  →  Architect  →  Dev  →  QA
   (ACs)        (Given/When/Then)  (Design)    (Code)  (Validate)
```

| Agent | File | Purpose |
|-------|------|---------|
| **Product Owner** | `.claude/agents/product-owner.md` | Reads feature requests, outputs structured Acceptance Criteria |
| **Spec Writer** | `.claude/agents/spec-writer.md` | Converts ACs into Gherkin `.feature` files in `specs/features/` |
| **Architect** | `.claude/agents/architect.md` | Designs graph nodes, state schema, tool interfaces |
| **Dev** | `.claude/agents/dev.md` | Implements Python code using LangGraph + Bedrock patterns |
| **QA** | `.claude/agents/qa.md` | Runs pytest + behave, validates specs pass, reports gaps |

`CLAUDE.md` at the root ties them together — describes the two-layer architecture, points to agent files, lists `make` targets, and defines the spec-driven workflow.

---

## Runtime Agent Architecture (Layer 2)

### LangGraph Topology

```
         ┌───────┐
         │ entry  │  Load session, prepare context
         └───┬───┘
             │
         ┌───▼───┐
    ┌────┤ router├────┐──────────┐
    │    └───────┘    │          │
┌───▼───┐  ┌────▼────┐ ┌──▼──┐ ┌────▼─────┐
│banking│  │insurance│ │ faq │ │escalation│
└───┬───┘  └────┬────┘ └──┬──┘ └────┬─────┘
    │           │         │         │
    └─────┬─────┘─────────┘         │
    ┌─────▼─────┐                   │
    │tool_execute│  (if tool needed) │
    └─────┬─────┘                   │
          │    ┌────────────────────┘
    ┌─────▼────▼─┐
    │  respond   │  Format response, save session
    └─────┬──────┘
          │
         END
```

### Key Design Decisions

1. **Bedrock Converse API** (not `invoke_model`) — provides native tool-calling support needed by LangGraph
2. **Single graph with conditional edges** — starts simple, domain handlers are nodes that can later be extracted into sub-graphs for domain-specific agents
3. **Python tools in-process** (not Go Lambdas) — LangGraph expects Python callables; can extract to Lambda later
4. **Factory pattern for LLM** — Bedrock for runtime, swappable to Claude/OpenAI for dev/testing
5. **Specs as source of truth** — if a prompt change breaks a spec, the prompt must be fixed

### State Schema (flows through every node)
- Input: `user_message`, `user_id`, `session_id`
- Session: `conversation_history`, `preferences`, `last_intent`
- Routing: `current_intent`, `intent_domain`, `routing_confidence`
- Tool execution: `tool_name`, `tool_args`, `tool_result`, `tool_error`
- Response: `response_text`, `needs_clarification`, `missing_slots`
- Control: `error_count`, `should_escalate`

### Core Dependencies
- `langgraph` — conversation graph orchestration
- `langchain-core`, `langchain-aws` — Bedrock integration
- `boto3` — AWS Bedrock runtime
- `pydantic`, `pydantic-settings` — config and data models
- `pyyaml` — intent/instruction YAML loading
- `fastapi`, `uvicorn` — API layer (Phase 7)

---

## Implementation Phases

### Phase 1: Project Scaffolding
Create all directories, config files (`pyproject.toml`, `Makefile`, `.gitignore`, `.env.example`), and `__init__.py` stubs.

### Phase 2: LLM Abstraction
`llm/base.py` (ABC), `llm/bedrock.py` (Converse API), `llm/factory.py`. Unit tests with mocked boto3.

### Phase 3: Graph Skeleton
`graph/state.py` (TypedDict), `graph/agent.py` (StateGraph), minimal nodes (entry -> router -> respond -> END), `app.py` CLI loop.

### Phase 4: Intent Routing
YAML intent files (30 intents from copilot branch), `intents/loader.py`, prompt templates, `router` node with LLM-based classification, `edges.py` conditional routing.

### Phase 5: Tool Framework & Domain Handlers
`tools/base.py`, `tools/registry.py`, mock banking/insurance tools, domain handler nodes, `tool_execute` node, instruction YAML files.

### Phase 6: Session & Memory
`memory/session.py`, `memory/store.py` (InMemoryStore), multi-turn conversation support.

### Phase 7: Build-Time Agents & Specs
`CLAUDE.md`, `.claude/agents/*.md`, Gherkin feature files, behave step definitions.

---

## Verification

1. `make setup` — creates venv, installs dependencies
2. `make test` — all unit + integration tests pass
3. `make lint` — ruff reports no issues
4. `make run` — starts CLI chat loop, can type a message and get a routed response
5. Manual test: type "What is my account balance?" → routes to banking → calls mock tool → returns formatted response
6. Manual test: type "I need to file a claim" → routes to insurance → calls mock tool → returns formatted response


All done. Here's a summary of what was created:

## Project Structure Created

**55 files** across the complete Nexus project:

### Runtime Agent (Python/LangGraph)
- **`src/nexus/graph/`** — LangGraph StateGraph with 7 nodes: `entry` → `router` → `[banking|insurance|faq|escalation]` → `tool_execute` → `respond` → END
- **`src/nexus/llm/`** — LLM abstraction: `BaseLLM` ABC, `BedrockLLM` (Nova Pro via Converse API), `LLMFactory`
- **`src/nexus/tools/`** — 10 mock tools (5 banking, 4 insurance, 1 FAQ) with registry pattern
- **`src/nexus/memory/`** — Session dataclass + InMemoryStore
- **`src/nexus/intents/`** — 30 intents across 3 YAML files (banking, insurance, faq)
- **`src/nexus/instructions/`** — Domain behavioral rules (global, banking, insurance, escalation)
- **`src/nexus/prompts/`** — System, routing, and response prompt templates
- **`src/nexus/app.py`** — CLI chat loop entry point

### Build-Time Agents (Spec-Driven Dev)
- **`.claude/agents/`** — 5 agent instruction files: Product Owner, Spec Writer, Architect, Dev, QA
- **`CLAUDE.md`** — Top-level orchestrator with project conventions
- **`specs/features/`** — 3 Gherkin feature files (intent routing, banking balance, insurance claim)

### Tests & Config
- **19 tests** (12 unit + 5 integration + 2 config) — all passing
- **Lint clean** via ruff
- `pyproject.toml`, `Makefile`, `.gitignore`, `.env.example`

### Quick start
```
make setup    # venv + install
make test     # 19 tests pass
make lint     # all clean
make run      # CLI chat loop (requires Bedrock credentials)
```


User: when it comes to agentic chatbot that leverage LLM, do we still call the intent? I understand from tranditional chatbot point of view, we call intent and then entities. but what do we call in LLM world? just wanted understand domain language for LLM based chatbot. 

Claude: Great question. The terminology has genuinely shifted with LLM-based agents. Here's the conceptual mapping:

## Traditional NLU Chatbot vs LLM Agentic Chatbot

| Traditional (Lex, Dialogflow) | LLM Agentic (LangGraph, etc.) | What changed |
|------|------|------|
| **Intent** | **Tool selection / Action** | LLM *reasons* about what to do instead of classifying into a fixed label |
| **Entities / Slots** | **Parameters / Arguments** | LLM extracts structured args for tool calls directly — no entity model needed |
| **Sample utterances** | **(not needed)** | LLMs understand language natively — no training examples required |
| **Slot filling dialog** | **Multi-turn reasoning** | LLM asks follow-up questions naturally, not from a slot-filling state machine |
| **Fulfillment** | **Tool execution** | Same idea, but the LLM decides *which* tool and *what* parameters |
| **Dialog flow / State machine** | **Agent orchestration / Planning** | Instead of rigid flows, agents *plan* and *reason* about next steps |
| **Context / Session** | **Memory** | Same concept, but often richer (summaries, preferences, long-term recall) |

## The Key Paradigm Shift

**Traditional**: User says something → Classifier predicts an intent label from a fixed set → Slot extractor pulls entities → Hardcoded fulfillment runs

**LLM Agentic**: User says something → LLM *reasons* about what the user wants → LLM decides which tool to call and with what arguments → LLM generates a natural response from the result

In a pure agentic system, you don't need an `intents/banking.yaml` file with 10 labeled intents at all. You just give the LLM a list of **tools** it can call and let it figure out which one fits:

```
Traditional:
  "What is my balance?" → intent classifier → "check_balance" → call API

Agentic:
  "What is my balance?" → LLM sees tool "get_account_balance" → calls it directly
```

## Where Does Nexus Sit?

Our current Nexus architecture is actually a **hybrid** — we use the LLM as a classifier (router node predicts an intent label), which then maps to tools. This is the `intent/banking.yaml` approach.

A more idiomatic LLM-agent approach would be:

```
# Instead of: router classifies intent → domain handler picks tool
# Do: LLM sees available tools and picks one directly

entry → agent (LLM + tools) → tool_execute → respond → END
```

The LLM itself handles routing, tool selection, and parameter extraction in one step via **tool/function calling** — which is exactly what Bedrock's Converse API supports natively.

## The Modern Vocabulary

| Term | Meaning |
|------|---------|
| **Agent** | An autonomous LLM-powered entity that can reason, plan, and act |
| **Tool** | A function/API the agent can call (this replaces "intent + fulfillment") |
| **Tool calling / Function calling** | The LLM's ability to output structured tool invocations |
| **Planning** | Agent breaks a complex request into steps |
| **Orchestration** | How agents, tools, and steps are coordinated (LangGraph does this) |
| **Grounding** | Connecting LLM reasoning to real data via tools/RAG |
| **Guardrails** | Safety constraints on what the agent can do |
| **Memory** | Short-term (conversation) and long-term (user preferences) context |

## What This Means for Nexus

We could evolve the architecture from the current hybrid (intent classification → tool mapping) to a more native agent approach where the LLM directly selects tools. The graph would simplify:

```
Current (hybrid):
  entry → router → [banking|insurance|faq|escalation] → tool_execute → respond

Future (native agent):
  entry → agent_reason (LLM picks tools directly) → tool_execute → respond
```

The domain handlers and intent YAML files would be replaced by **tool definitions** with rich descriptions that the LLM uses to decide what to call. The `intents/*.yaml` would become documentation for the tools themselves rather than a classification taxonomy.

That said, the hybrid approach has value in production — it gives you more control, auditability, and deterministic routing. Many production systems use it. The pure agentic approach is more flexible but harder to debug and predict.

Want me to refactor the architecture toward the more native agentic pattern, or keep the hybrid approach?

User: /project:dev who are you

Claude: 