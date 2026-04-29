# Nexus — Development Walkthrough

## What Was Built (Session 1 — 2026-04-28)

### Phase 0: Planning & Specs
- **PRD** finalized at v0.3.0 — saved at `docs/PRD.md`
- **8 Feature Specs** written and approved in `specs/features/`
- **5 Technical Blueprints** written in `specs/blueprints/core/`
- **Two-tier spec model** established: Features (business) → Blueprints (technical) → Code → Tests

### Phase 1: Core Infrastructure — COMPLETE
All core modules implemented with tests:

| Module | File | Tests | Status |
|--------|------|-------|--------|
| Shared Types | `core/types.py` | `tests/test_types.py` (11) | ✅ |
| Session Manager | `core/session.py` | `tests/test_session.py` (13) | ✅ |
| Agent Discovery | `core/discovery.py` | `tests/test_discovery.py` (13) | ✅ |
| LLM Client | `core/llm.py` | — (needs AWS) | ✅ |
| Base Agent | `core/base_agent.py` | — (abstract) | ✅ |
| Config | `config.py` | — | ✅ |

**Total: 37 tests passing, 0 warnings**

### Phase 2: Main Agent — COMPLETE
- `agents/main_agent/agent.md` — capability manifest with skills
- `agents/main_agent/persona.md` — tone & style
- `agents/main_agent/instruction.md` — behavioral rules + `<reasoning>` tag
- `agents/main_agent/agent.py` — MainAgent with LangGraph, tool-calling, delegation
- `agents/main_agent/graph.py` — StateGraph: START → process → [route] → delegate/respond → END
- `agents/main_agent/tools.py` — delegate_to_agent + show_capabilities (dynamic from discovery)
- `agents/main_agent/nodes.py` — reasoning extraction helpers
- `agents/main_agent/state.py` — MainAgentState TypedDict
- `app.py` — CLI REPL with enhanced debug panel (tool calls, delegation display)


## What Was Built (Session 2 — 2026-04-29)

### Specs-First Workflow Enforcement
- **PRD §2.1** added: "Development Workflow — Specs First" with cardinal rule: "No code without a blueprint"
- Two-tier spec model codified: Feature Spec → Blueprint → Code → Tests

### Spec Reorganization
Feature specs reorganized from flat files into component folders:

| Folder | Feature Specs |
|--------|--------------|
| `specs/features/main_agent/` | F-001 (Greeting), F-003 (Skill Routing), F-004 (Graceful Decline) |
| `specs/features/live_agent/` | F-005 (Live Agent), F-006 (Chat Bridge) |
| `specs/features/core/` | F-002 (Discovery), F-007 (Debug Panel), F-008 (Scaffolding) |

Blueprint directories created for upcoming work:
- `specs/blueprints/main_agent/` — graph, tools, nodes specs ✅ written
- `specs/blueprints/live_agent/` — empty (for Phase 4)
- `specs/blueprints/contact_center/` — empty (for Phase 5)
- `specs/blueprints/scripts/` — create_agent spec ✅ written

### Phase 3: Agent Scaffolding — COMPLETE
- **Blueprint:** `specs/blueprints/scripts/create_agent.spec.md`
- **Templates:** 9 template files in `agents/_template/`
- **Script:** `scripts/create_agent.py` — creates new agent from templates
- Handles class name derivation, validation, error cases
- Tested: scaffold → discovery → existing tests pass (37/37)

### Main Agent Blueprints — COMPLETE
Three blueprints written for Phase 2 completion:
- `specs/blueprints/main_agent/graph.spec.md` — LangGraph StateGraph with ReAct-style flow
- `specs/blueprints/main_agent/tools.spec.md` — delegate_to_agent + show_capabilities
- `specs/blueprints/main_agent/nodes.spec.md` — process, delegate, tool_response, respond nodes

### Phase 2: Main Agent LangGraph — COMPLETE
- **LangGraph StateGraph** with conditional routing (process → delegate/respond)
- **Tools**: `delegate_to_agent` (dynamic from discovered capabilities), `show_capabilities`
- **Delegation protocol**: summary generation, session handoff, sub-agent invocation, return
- **Scaffolded `live_agent`** via `create_agent.py` as delegation target
- **Enhanced debug panel**: shows tool calls, delegation direction, reasoning
- **51 tests passing** (37 existing + 14 new main_agent tests)
- Added `invoke_with_tools_raw()` to `core/llm.py` for Bedrock-format message loops
- Added `botocore[crt]` to requirements.txt for AWS SSO credential support

**Total: 51 tests passing, 0 warnings**

## What's Next

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 4 | TODO | LiveAgent (F-005: queue routing, F-006: chat bridge) — needs blueprints |
| Phase 5 | TODO | Contact center mock (WebSocket server + MSR console) — needs blueprints |
| Phase 6 | TODO | Integration testing + polish |

## Key Design Decisions

1. **Skills vs Tools** — Skills are external contracts (in `agent.md`, read by discovery). Tools are internal LLM functions (in `tools.py`, used for function calling).
2. **Per-agent conversation history** — No shared history. Delegation produces a summary handed to the target agent.
3. **`@tool` decorator pattern** — Tool schemas auto-generated from Python type hints + docstrings.
4. **LangGraph for all agents** — Consistent pattern even for simple agents (START → process → END).
5. **Regex-based YAML parsing** — Avoided `pyyaml` dependency for agent.md frontmatter.
6. **LiveAgent lifecycle** — 2-min idle timeout, MSR `/end` signal, queue switch returns to main_agent.
7. **Simplified orchestrator graph** — ReAct-style (process → route → delegate/respond) rather than multi-node pipeline. Complexity is in tools and system prompt, not graph topology.
8. **Specs-first workflow** — No code without a blueprint. Feature Spec → Blueprint → Code → Tests.

## How to Resume

1. Read `docs/PRD.md` for the full product requirements
2. Read `docs/walkthrough.md` (this file) for what's been built
3. Check `specs/features/` for approved feature specs (organized by component)
4. Check `specs/blueprints/` for technical blueprints (organized by component)
5. Run tests: `cd nexus && python -m pytest tests/ -v`
6. Continue with next phase from the task list above

## Project Structure

```
nexus/
├── docs/
│   ├── PRD.md                  # Product Requirements Document (v0.3.0 + §2.1)
│   └── walkthrough.md          # This file — development history
├── specs/
│   ├── features/
│   │   ├── core/               # F-002, F-007, F-008
│   │   ├── main_agent/         # F-001, F-003, F-004
│   │   └── live_agent/         # F-005, F-006
│   └── blueprints/
│       ├── core/               # types, session, discovery, llm, base_agent (5 specs)
│       ├── main_agent/         # graph, tools, nodes (3 specs)
│       ├── live_agent/         # (empty — for Phase 4)
│       ├── contact_center/     # (empty — for Phase 5)
│       └── scripts/            # create_agent (1 spec)
├── core/                       # Core infrastructure (implemented)
│   ├── types.py, session.py, discovery.py, llm.py, base_agent.py
├── agents/
│   ├── _template/              # 9 template files for scaffolding
│   └── main_agent/             # Orchestrator (greeting implemented)
├── contact_center/             # TODO: WebSocket server + MSR console
├── scripts/
│   └── create_agent.py         # Agent scaffolding script ✅
├── tests/                      # 37 tests passing
├── app.py                      # CLI entry point
├── config.py                   # Configuration
└── requirements.txt            # Dependencies
```

