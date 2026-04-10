# Nexus — Product Requirements Document

> A reusable specification for building an agentic conversational AI platform for financial services, using modern LLM-native architecture.

---

## 1. Vision

Build **Nexus**, an agentic AI assistant for banking and insurance that uses LLM-native tool calling — not traditional intent classification — to reason about user requests, select appropriate tools, execute actions, and respond naturally.

The agent **reasons** about what the user needs, **acts** by calling tools, **observes** the results, and **responds** with grounded natural language. This is the ReAct (Reason + Act) pattern, not the traditional NLU pipeline of intent → entity → fulfillment.

---

## 2. Glossary: Modern Agentic Vocabulary

These terms replace traditional chatbot terminology throughout this document and codebase:

| Modern Term | Replaces | Definition |
|-------------|----------|------------|
| **Agent** | Bot / Chatbot | An autonomous LLM-powered entity that can reason, plan, and take actions |
| **Tool** | Intent + Fulfillment / Skill | A function or API the agent can invoke. Defined by name, description, and parameter schema |
| **Tool calling** | Intent classification + Slot filling | The LLM's ability to output structured function invocations with arguments, in a single reasoning step |
| **Reasoning** | NLU / Intent matching | The LLM analyzing what the user needs and deciding how to respond |
| **Planning** | Dialog flow / State machine | The agent decomposing a complex request into a sequence of actions |
| **Observation** | Fulfillment response | The result returned by a tool that feeds back into the agent's reasoning loop |
| **Orchestration** | Dialog management | How the agent's reasoning, actions, and observations are coordinated (via LangGraph) |
| **Grounding** | N/A | Connecting the LLM's reasoning to real data via tools and RAG, preventing hallucination |
| **Memory** | Session / Context | Short-term (conversation buffer) and long-term (vector-backed user history, preferences) |
| **Guardrails** | Validation rules | Safety constraints: PII masking, compliance rules, action limits, content filtering |
| **State** | Session variables | The structured data flowing through the orchestration graph at each step |
| **System prompt** | Bot persona / Instructions | The foundational instructions that define the agent's behavior, domain knowledge, and constraints |

### The ReAct Loop

This is the core pattern for how the agent processes every user message:

```
User message
    │
    ▼
┌─────────┐     ┌─────────┐     ┌─────────┐
│ REASON  │────►│   ACT   │────►│ OBSERVE │──┐
│         │     │         │     │         │  │
│ What    │     │ Call a  │     │ Read    │  │
│ does    │     │ tool    │     │ the     │  │
│ the     │     │ with    │     │ tool    │  │
│ user    │     │ args    │     │ result  │  │
│ need?   │     │         │     │         │  │
└─────────┘     └─────────┘     └────┬────┘  │
                                     │       │
                              ┌──────▼───┐   │
                              │ RESPOND  │   │
                              │          │   │
                              │ Generate │   │
                              │ natural  │   │
                              │ language │   │
                              └──────────┘   │
                                     │       │
                              (or loop back if
                               more actions needed)
```

---

## 3. System Architecture

### 3.1 Two-Layer Design

Nexus has two distinct layers:

**Layer 1 — Build-Time AI Agents** (development workflow)
AI coding assistants that use spec-driven development to build and maintain the runtime agent. These use Claude, GPT, or any capable model during development.

**Layer 2 — Runtime Agent** (the product)
The agentic chatbot itself. This MUST use **Amazon Nova Pro** via **AWS Bedrock** as its LLM. It uses **Amazon Titan Text Embeddings V2** for any vector/RAG capabilities.

### 3.2 Runtime Agent Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Nexus Runtime Agent                          │
│                                                                  │
│   User ──► [entry] ──► [reason] ──► [act] ──► [observe] ──►    │
│                            │           │          │              │
│                            │     ┌─────▼─────┐   │              │
│                            │     │ Tool Call  │   │              │
│                            │     │            │   │              │
│                            │     │ Banking:   │   │              │
│                            │     │  balance   │   │              │
│                            │     │  transfer  │   │              │
│                            │     │  fraud     │   │              │
│                            │     │            │   │              │
│                            │     │ Insurance: │   │              │
│                            │     │  claims    │   │              │
│                            │     │  policy    │   │              │
│                            │     │  quotes    │   │              │
│                            │     │            │   │              │
│                            │     │ Knowledge: │   │              │
│                            │     │  RAG/FAQ   │   │              │
│                            │     └────────────┘   │              │
│                            │                      │              │
│                       [respond] ◄─────────────────┘              │
│                            │                                     │
│                         User ◄───                                │
│                                                                  │
│   ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐    │
│   │ Nova Pro    │  │ Titan V2       │  │ Memory Store     │    │
│   │ (Bedrock)   │  │ (Embeddings)   │  │ (In-Memory /     │    │
│   │ Reasoning + │  │ Vector search  │  │  DynamoDB)       │    │
│   │ Tool calling│  │ for RAG        │  │                  │    │
│   └─────────────┘  └────────────────┘  └──────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 Graph Topology (LangGraph)

The agent operates as a **StateGraph** where each node is a step in the ReAct loop:

```
entry ──► reason ──► act ──► observe ──► respond ──► END
              │                              │
              └──────── (loop if needed) ◄───┘
```

| Node | Responsibility |
|------|----------------|
| **entry** | Load memory (conversation history, user preferences). Prepare agent state |
| **reason** | LLM analyzes the user message + history + available tools. Decides: call a tool, ask a follow-up, or respond directly |
| **act** | Execute the tool selected by the LLM. Dispatch via tool registry |
| **observe** | Feed tool results back into state. Check for errors or need for additional actions |
| **respond** | LLM generates a natural language response grounded in tool observations. Save to memory |

**Key difference from traditional chatbots**: There is no "router" node that classifies into a fixed intent taxonomy. The LLM in the `reason` node sees ALL available tools and decides which one to call based on its understanding of the user's request.

### 3.4 How Tool Calling Works (Not Intent Classification)

Traditional chatbot:
```
"What is my balance?"
  → NLU classifier → intent: "check_balance" (from a fixed list of 30)
  → Slot extractor → entities: { account_type: "checking" }
  → Fulfillment → call API → response
```

Nexus agentic approach:
```
"What is my balance?"
  → LLM sees tool definitions:
      - get_account_balance(user_id, account_type?) → "Retrieve account balance"
      - transfer_funds(from, to, amount) → "Transfer money between accounts"
      - file_claim(policy_id, description) → "File an insurance claim"
      - ... (all tools)
  → LLM reasons: "User wants their balance" → calls get_account_balance
  → Tool returns: { balance: 4250.75, account: "****4521", type: "checking" }
  → LLM responds: "Your checking account (****4521) has a balance of $4,250.75."
```

The LLM does routing, parameter extraction, and tool selection in ONE step via the Bedrock Converse API's native tool calling.

---

## 4. Technology Stack

### 4.1 Runtime Agent (the product)

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Language** | Python 3.11+ | LangGraph ecosystem, Bedrock SDK support |
| **Orchestration** | LangGraph | Graph-based agent orchestration with state management, supports ReAct loops |
| **Reasoning LLM** | Amazon Nova Pro (`amazon.nova-pro-v1:0`) via Bedrock | Runtime LLM for reasoning, tool calling, and response generation |
| **LLM API** | Bedrock Converse API (`boto3 bedrock-runtime`) | Native tool calling support, multi-turn conversation, unified interface |
| **Embeddings** | Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`) via Bedrock | Vector embeddings for RAG knowledge base |
| **Vector Store** | FAISS (local) / Bedrock Knowledge Bases (production) | Semantic search over domain knowledge |
| **Memory** | In-memory (dev) / DynamoDB (production) | Conversation history and user preferences |
| **Config** | pydantic-settings + `.env` | Type-safe configuration |
| **Data formats** | YAML (tool definitions, guardrails), `.txt` (prompt templates) | Human-readable, version-controlled |
| **Testing** | pytest | Unit, integration, and agent behavior tests |
| **Linting** | ruff | Fast Python linter and formatter |

### 4.2 Build-Time Agents (development workflow)

| Component | Technology |
|-----------|-----------|
| AI coding assistants | Claude Code with custom agents and slash commands |
| Spec format | Gherkin (Given/When/Then) in `.feature` files |
| Workflow | Product Owner → Spec Writer → Architect → Dev → QA |

### 4.3 Key Dependencies

```
langgraph>=0.2
langchain-core>=0.3
langchain-aws>=0.2
boto3>=1.35
pydantic>=2.0
pydantic-settings>=2.0
python-dotenv>=1.0
pyyaml>=6.0
faiss-cpu>=1.7  # for local vector store
```

---

## 5. Agent Capabilities

### 5.1 Tool Definitions (Replace "Intents")

Tools are the actions the agent can take. Each tool is defined by:
- **Name**: Machine identifier (e.g., `get_account_balance`)
- **Description**: Natural language description the LLM reads to decide when to use it
- **Parameters**: JSON Schema defining the arguments
- **Domain**: Logical grouping (banking, insurance, knowledge)

#### Banking Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_account_balance` | Retrieve the current balance for a user's bank account | `user_id`, `account_type?` |
| `transfer_funds` | Transfer money between accounts or to another person | `from_account`, `to_account`, `amount` |
| `get_transactions` | Retrieve recent transaction history | `user_id`, `limit?`, `date_range?` |
| `report_fraud` | Report a suspicious or unauthorized transaction | `user_id`, `transaction_id?`, `description` |
| `freeze_card` | Temporarily freeze a debit or credit card | `user_id`, `card_id?` |
| `activate_card` | Activate a new or replacement card | `user_id`, `card_last_four` |
| `dispute_transaction` | Dispute a specific transaction | `user_id`, `transaction_id`, `reason` |
| `get_account_details` | Retrieve account metadata (type, open date, status) | `user_id`, `account_id?` |
| `update_contact_info` | Update phone, email, or address on file | `user_id`, `field`, `new_value` |
| `open_account` | Start the process of opening a new account | `user_id`, `account_type` |

#### Insurance Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `file_claim` | File a new insurance claim | `user_id`, `policy_id`, `claim_type`, `description` |
| `check_claim_status` | Check the status of an existing claim | `user_id`, `claim_id` |
| `get_policy_details` | Retrieve details of an insurance policy | `user_id`, `policy_id?` |
| `request_quote` | Request a quote for a new insurance policy | `user_id`, `policy_type`, `details` |
| `update_policy` | Update details on an existing policy | `user_id`, `policy_id`, `changes` |
| `add_vehicle` | Add a vehicle to an auto insurance policy | `user_id`, `policy_id`, `vehicle_info` |
| `remove_vehicle` | Remove a vehicle from a policy | `user_id`, `policy_id`, `vehicle_id` |
| `renew_policy` | Renew an expiring policy | `user_id`, `policy_id` |
| `cancel_policy` | Cancel an active policy | `user_id`, `policy_id`, `reason` |
| `roadside_assistance` | Request roadside assistance | `user_id`, `location`, `issue_type` |

#### Knowledge Tools (RAG)

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_knowledge_base` | Search the knowledge base for answers to general questions | `query` |
| `get_faq_answer` | Retrieve a specific FAQ answer | `topic` |

### 5.2 Guardrails

Safety and compliance constraints enforced at the orchestration layer:

| Guardrail | Rule |
|-----------|------|
| **PII Protection** | Never reveal full account numbers, SSNs, or card numbers. Mask all but last 4 digits |
| **Financial Data** | Never hallucinate financial data. Always ground responses in tool results |
| **High-Value Actions** | Require explicit confirmation before executing transfers > $500 or policy cancellations |
| **Authentication** | Validate user identity context before accessing account data |
| **Escalation** | Transfer to human when: user expresses frustration, request is outside capabilities, or tool errors persist |
| **Compliance** | Do not promise claim outcomes. Do not provide financial advice. Add disclaimers where required |
| **Content Safety** | Reject off-topic requests. Stay within financial services domain |

### 5.3 Memory Architecture

| Memory Type | Storage | Purpose | Lifecycle |
|-------------|---------|---------|-----------|
| **Conversation buffer** | In state (`conversation_history`) | Current dialog turns | Per session |
| **Session memory** | In-memory store / DynamoDB | User preferences, last action, session metadata | Across turns, expires |
| **Long-term memory** | Vector store (FAISS / Bedrock KB) | User interaction patterns, product knowledge | Persistent |

---

## 6. Orchestration Design (LangGraph)

### 6.1 Agent State

```python
class AgentState(TypedDict, total=False):
    # Input
    user_message: str
    user_id: str
    session_id: str

    # Memory
    conversation_history: list[dict]   # [{"role": "user|assistant", "content": "..."}]
    user_preferences: dict

    # Agent reasoning
    reasoning: str                      # LLM's chain-of-thought (for debugging)
    selected_tool: str                  # Tool the LLM chose to call
    tool_arguments: dict                # Arguments extracted by the LLM
    requires_confirmation: bool         # High-value action needs user OK

    # Tool observation
    tool_result: dict                   # Result from tool execution
    tool_error: str                     # Error message if tool failed

    # Response
    response_text: str                  # Final natural language response
    follow_up_needed: bool              # Agent wants to ask a clarifying question

    # Control
    action_count: int                   # Number of tool calls this turn (loop guard)
    should_escalate: bool               # Transfer to human agent
```

### 6.2 Graph Definition

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)

graph.add_node("entry", entry_node)
graph.add_node("reason", reason_node)
graph.add_node("act", act_node)
graph.add_node("observe", observe_node)
graph.add_node("respond", respond_node)

graph.set_entry_point("entry")

graph.add_edge("entry", "reason")
graph.add_conditional_edges("reason", should_act_or_respond, {
    "act": "act",           # LLM selected a tool
    "respond": "respond",   # LLM can respond directly (no tool needed)
    "escalate": "respond",  # Escalation path
})
graph.add_edge("act", "observe")
graph.add_conditional_edges("observe", should_continue_or_respond, {
    "reason": "reason",     # Need another tool call (multi-step)
    "respond": "respond",   # Done, generate response
})
graph.add_edge("respond", END)
```

### 6.3 Multi-Step Reasoning Example

```
User: "Transfer $200 from checking to savings"

  reason  → LLM decides: first check balance to confirm sufficient funds
  act     → calls get_account_balance(user_id, "checking")
  observe → balance is $4,250.75 — sufficient

  reason  → LLM decides: execute the transfer ($200 < $500, no confirmation needed)
  act     → calls transfer_funds("checking", "savings", 200)
  observe → transfer successful, confirmation #TXN-9284

  respond → "Done! I've transferred $200 from your checking to savings.
             Confirmation: TXN-9284. Your new checking balance is $4,050.75."
```

---

## 7. RAG Architecture (Knowledge Grounding)

For questions that don't require tool calls, the agent uses Retrieval-Augmented Generation:

```
User question
      │
      ▼
┌──────────────────┐     ┌──────────────────────────────┐
│  Titan V2        │     │  Vector Store                 │
│  Embeddings      │────►│  (FAISS / Bedrock KB)         │
│  (query → vector)│     │                              │
└──────────────────┘     │  Domain knowledge:           │
                         │  - Product docs              │
                         │  - FAQs                      │
                         │  - Policy terms              │
                         │  - Fee schedules             │
                         └──────────┬───────────────────┘
                                    │ top-k chunks
                                    ▼
                         ┌──────────────────────┐
                         │  Nova Pro (Bedrock)   │
                         │  Reason over chunks + │
                         │  user question        │
                         │  → grounded answer    │
                         └──────────────────────┘
```

### Embedding Model

- **Model**: Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`)
- **Dimensions**: 1024
- **Access**: Bedrock `invoke_model` API
- **Use cases**: Document chunking, semantic search, FAQ matching

### Knowledge Sources

| Source | Content | Update Frequency |
|--------|---------|-----------------|
| Product docs | Account types, features, limits | Monthly |
| FAQs | Common questions and answers | Weekly |
| Policy terms | Insurance policy language, coverage details | Quarterly |
| Fee schedules | Banking fees, insurance premiums | Monthly |
| Compliance docs | Regulatory disclosures, disclaimers | As needed |

---

## 8. Project Structure

```
nexus/
├── PRD.md                                 # This document
├── CLAUDE.md                              # Build-time agent orchestration guide
├── README.md                              # Setup, usage, architecture overview
├── Makefile                               # setup, test, lint, format, run, clean
├── pyproject.toml                         # Python project config + dependencies
├── requirements.txt                       # Pinned dependency versions
├── .env.example
├── .gitignore
│
├── .claude/
│   ├── agents/                            # Agent personas (YAML frontmatter + markdown)
│   │   ├── product-owner.md
│   │   ├── spec-writer.md
│   │   ├── architect.md
│   │   ├── dev.md
│   │   └── qa.md
│   └── commands/                          # Slash commands (skills)
│       ├── plan.md                        # /project:plan
│       ├── spec-write.md                  # /project:spec-write
│       ├── architect.md                   # /project:architect
│       ├── dev.md                         # /project:dev
│       └── qa.md                          # /project:qa
│
├── specs/features/                        # Gherkin specs (source of truth)
│
├── src/nexus/
│   ├── app.py                             # CLI entry point
│   ├── config.py                          # pydantic-settings + .env
│   │
│   ├── llm/                               # LLM abstraction layer
│   │   ├── base.py                        # BaseLLM ABC (invoke, invoke_with_tools)
│   │   ├── bedrock.py                     # Nova Pro via Bedrock Converse API
│   │   ├── embeddings.py                  # Titan V2 embeddings via Bedrock
│   │   └── factory.py                     # LLMFactory for swappable backends
│   │
│   ├── graph/                             # LangGraph agent orchestration
│   │   ├── state.py                       # AgentState TypedDict
│   │   ├── agent.py                       # build_graph(): StateGraph construction
│   │   ├── edges.py                       # Conditional edge functions
│   │   └── nodes/
│   │       ├── entry.py                   # Load memory, prepare context
│   │       ├── reason.py                  # LLM reasoning + tool selection
│   │       ├── act.py                     # Tool execution dispatch
│   │       ├── observe.py                 # Process tool results
│   │       └── respond.py                 # Generate response, save memory
│   │
│   ├── tools/                             # Tool implementations
│   │   ├── base.py                        # Tool protocol
│   │   ├── registry.py                    # ToolRegistry (name → callable)
│   │   ├── definitions/                   # Tool schemas (YAML)
│   │   │   ├── banking.yaml
│   │   │   ├── insurance.yaml
│   │   │   └── knowledge.yaml
│   │   ├── banking/                       # Banking domain tools
│   │   ├── insurance/                     # Insurance domain tools
│   │   └── knowledge/                     # RAG / FAQ tools
│   │
│   ├── memory/                            # Memory management
│   │   ├── session.py                     # Conversation memory
│   │   ├── store.py                       # Abstract store + InMemoryStore
│   │   └── vector.py                      # Vector store for RAG
│   │
│   ├── guardrails/                        # Safety and compliance
│   │   ├── rules.yaml                     # Guardrail definitions
│   │   └── enforcer.py                    # Pre/post action checks
│   │
│   └── prompts/                           # LLM prompt templates
│       ├── system_prompt.txt              # Agent persona and instructions
│       ├── reasoning_prompt.txt           # Tool selection reasoning
│       └── response_prompt.txt            # Response generation
│
└── tests/
    ├── conftest.py                        # MockLLM, mock tools, fixtures
    ├── unit/
    └── integration/
```

---

## 9. Build-Time Workflow

```
/project:plan "add vehicle to insurance policy"
  → Product Owner produces ACs

/project:spec-write <ACs>
  → Spec Writer produces specs/features/insurance_add_vehicle.feature

/project:architect "design add_vehicle tool and guardrails"
  → Architect produces component design

/project:dev "implement add_vehicle tool per architecture"
  → Developer produces src/nexus/tools/insurance/add_vehicle.py + tests

/project:qa
  → QA validates: tests pass, lint clean, specs satisfied
```

---

## 10. Success Criteria

### Functional

- [ ] Agent handles banking and insurance requests using tool calling (not intent classification)
- [ ] Agent selects the correct tool without a fixed intent taxonomy
- [ ] Agent extracts tool parameters from natural conversation
- [ ] Agent chains multiple tool calls for complex requests
- [ ] Agent uses RAG (Titan V2 embeddings) to answer knowledge questions
- [ ] Agent maintains conversation memory across turns
- [ ] Guardrails prevent PII exposure, hallucinated data, and unauthorized actions
- [ ] Agent escalates to human when it cannot help

### Technical

- [ ] Runtime LLM is Amazon Nova Pro via Bedrock Converse API
- [ ] Embeddings use Amazon Titan Text Embeddings V2
- [ ] Orchestration uses LangGraph StateGraph with ReAct loop
- [ ] Tool definitions are declarative (YAML) with JSON Schema parameters
- [ ] Factory pattern for LLM allows swapping during development/testing
- [ ] All tests pass with MockLLM (no AWS credentials needed)
- [ ] `make test` passes, `make lint` is clean

### Agent Behavior

- [ ] "What is my balance?" → calls `get_account_balance` → responds with balance
- [ ] "Transfer $200 to savings" → calls `transfer_funds` → confirms with reference number
- [ ] "I need to file a claim" → calls `file_claim` → returns claim ID and status
- [ ] "What are your hours?" → searches knowledge base → responds with grounded answer
- [ ] "asdfghjkl" → agent says it doesn't understand, offers help
- [ ] "I'm frustrated, let me talk to someone" → escalates to human agent

---

## 11. Future Evolution

### Phase 1 (Current): Single Agent
One agent with all tools. Simple ReAct loop.

### Phase 2: Domain Agents
Split into specialized agents with a supervisor:
```
Supervisor Agent (routes to domain agents)
  ├── Banking Agent (banking tools only)
  ├── Insurance Agent (insurance tools only)
  └── Knowledge Agent (RAG tools only)
```

### Phase 3: Multi-Agent Collaboration
Agents delegate to each other for cross-domain requests.

### Phase 4: Production Hardening
DynamoDB for memory, Bedrock Knowledge Bases for managed RAG, Bedrock Guardrails for managed safety, API Gateway WebSocket for real-time chat.

---

## 12. Using This Document

This PRD is designed to be given directly to an AI coding agent as a prompt:

```
"Build the Nexus agentic chatbot platform as described in PRD.md.
 Use Python, LangGraph, and AWS Bedrock (Nova Pro for reasoning,
 Titan V2 for embeddings). Follow the ReAct pattern for agent
 orchestration. Start with Phase 1: single agent with all tools."
```

The AI coding agent should:
1. Read this PRD for architecture and requirements
2. Read CLAUDE.md for project conventions and build workflow
3. Use `/project:plan` → `/project:spec-write` → `/project:architect` → `/project:dev` → `/project:qa`
4. **Tools replace intents. Reasoning replaces classification. Memory replaces sessions.**
