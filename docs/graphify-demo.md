# Graphify architecture demo

Graphify is development tooling for understanding this repository. It builds a
code knowledge graph that engineers can inspect in a browser or query from a
coding assistant. It is not part of the member-assistant runtime, does not
replace LangGraph, and must not be pointed at member data, local databases,
secrets, logs, or production traces.

## Install

Graphify requires Python 3.10 or newer. It is exposed as a separate project
extra because the base application continues to support Python 3.9. With an
existing Python 3.10+ project environment, install it using ordinary `pip`:

```bash
python -m pip install -e '.[graphify]'
```

To install the test tools and Graphify together:

```bash
python -m pip install -e '.[dev,graphify]'
```

If the application's virtual environment uses Python 3.9, create a small
Graphify-only environment using any Python 3.10+ executable already installed
on the workstation:

```bash
python3.11 -m venv .venv-graphify
source .venv-graphify/bin/activate
python -m pip install -e '.[graphify]'
```

Replace `python3.11` with `python3.10`, `python3.12`, or `python3.13` as
available. No `uv` or `pipx` installation is required. The PyPI package name
has two trailing `y` characters; the installed command is `graphify`.

The project-scoped Codex skill and guidance are already checked in under
`.codex/skills/graphify/` and `AGENTS.md`. Installing the CLI makes those
instructions and the checked-in `.codex/hooks.json` refresh check operational;
it does not add Graphify to the member-assistant process.

## View the checked-in graph

Open `graphify-out/graph.html` in a browser. It is a static, interactive view:

- search for `AgentRuntime`, `stream_chat`, or `_build_graph`;
- select a node to inspect callers and dependencies;
- filter communities to reduce visual noise;
- use `graphify-out/GRAPH_REPORT.md` for a text summary; and
- open `graphify-out/CALL_FLOW.html` for a presentation-oriented call-flow view.

The checked-in graph is generated from source code only. This keeps generation
deterministic and avoids sending repository documents to an LLM backend.

## Query the graph

Run these from the repository root:

```bash
graphify query "How does a member WebSocket message reach AgentRuntime?"
graphify query "What calls the transfer tool and what policy code is nearby?" --dfs
graphify query "Where is durable conversation state loaded and saved?"
graphify path "stream_session" "execute_transfer"
graphify explain "AgentRuntime"
graphify affected "ConversationState" --depth 3
```

Every result should be treated as navigation evidence, not proof of runtime
behavior. Confirm important findings in source and tests, especially inferred or
ambiguous relationships.

## Refresh after code changes

For an incremental AST-only refresh:

```bash
graphify update .
graphify export callflow-html graphify-out/graph.json \
  --output graphify-out/CALL_FLOW.html
```

For a clean source-only rebuild:

```bash
graphify extract . --code-only --out .
graphify export callflow-html graphify-out/graph.json \
  --output graphify-out/CALL_FLOW.html
```

Commit `graphify-out/graph.json`, `graphify-out/graph.html`,
`graphify-out/GRAPH_REPORT.md`, and `graphify-out/CALL_FLOW.html`. Local cache,
manifest, cost, and model-generated labeling files are intentionally ignored.

## Suggested team walkthrough

1. Open the interactive graph and locate `AgentRuntime`.
2. Follow `stream_chat` into the compiled LangGraph lifecycle.
3. Trace policy and confirmation paths before skill/tool execution.
4. Locate SQLite conversation-state and durable-event persistence.
5. Run an impact query for `ConversationState` to preview the future checkpoint
   migration blast radius.

Graphify output is a snapshot. Refresh it whenever source-level architecture
changes are merged.
