# Graphify architecture demo

Graphify is development tooling for understanding this repository. It builds a
code knowledge graph that engineers can inspect in a browser or query from a
coding assistant. It is not part of the member-assistant runtime, does not
replace LangGraph, and must not be pointed at member data, local databases,
secrets, logs, or production traces.

## What this visualization represents

The generated graph is a **static source-code map**. It reads Python symbols,
imports, calls, types, and inferred relationships to show the routes a request
can take through the code. `CALL_FLOW.html` is a presentation of those static
relationships; it is not a recording of a request that actually ran.

For this application, Graphify helps navigate the possible path from FastAPI
and WebSocket handling into `AgentRuntime.stream_chat`, the compiled LangGraph,
policy evaluation, generic skill execution, tools, durable events, and the
SQLite state store. It is especially useful for architecture reviews and change
impact analysis.

Graphify does not show runtime inputs, the exact branch selected for one member,
model/tool latency, failures, or checkpoint state. Use the application's
OpenTelemetry/Langfuse tracing and durable event stream for a live request
trace. Graphify and runtime observability are complementary views:

| View | Answers |
| --- | --- |
| Graphify | What code is connected, and what could be affected by a change? |
| Langfuse/OpenTelemetry | What happened during this particular request? |
| Durable event/state store | What member-visible events and state were persisted? |

Graphify reads source files but does not rewrite, lint, test, or instrument
anything under `src/`. All generated repository artifacts stay under
`graphify-out/`. The project Codex hook only checks for Graphify guidance; it is
not an application runtime hook or a source-code quality gate.

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

First run these commands from the repository root:

```bash
pwd
ls graphify-out/graph.html graphify-out/CALL_FLOW.html
```

If `graphify-out/graph.html` does not exist, confirm that the machine has the
branch containing the Graphify artifacts. During review that is
`codex/graphify-demo`; after merge it will be `codex/demo`:

```bash
git fetch origin
git switch codex/graphify-demo  # use codex/demo after the feature is merged
git pull
```

If `git switch` reports that the branch is unknown, it has not been pushed to
the shared remote yet. The branch owner must push it or merge it before another
machine can receive the checked-in graph.

Open the static files using the command appropriate for the workstation:

```bash
# macOS
open graphify-out/graph.html
open graphify-out/CALL_FLOW.html

# Linux
xdg-open graphify-out/graph.html

# Windows PowerShell
Start-Process graphify-out/graph.html
```

The interactive graph supports the following walkthrough:

- search for `AgentRuntime`, `stream_chat`, or `_build_graph`;
- select a node to inspect callers and dependencies;
- filter communities to reduce visual noise;
- use `graphify-out/GRAPH_REPORT.md` for a text summary; and
- open `graphify-out/CALL_FLOW.html` for a presentation-oriented call-flow view.

The checked-in graph is generated from source code only. This keeps generation
deterministic and avoids sending repository documents to an LLM backend.

### Browser fallback: serve the files locally

A server is not normally required. If corporate browser policy blocks local
`file://` pages, start a local static server from the repository root:

```bash
python -m http.server 8765 --bind 127.0.0.1
```

Keep that terminal running and open:

- `http://127.0.0.1:8765/graphify-out/graph.html`
- `http://127.0.0.1:8765/graphify-out/CALL_FLOW.html`

Stop the server with `Ctrl-C`. It is only a local file server; the member
assistant does not need to be running.

### Generate the files when they are absent

After installing the `graphify` extra, a first-time source-only build is:

```bash
graphify extract . --code-only --out .
graphify cluster-only . --no-label
graphify export callflow-html graphify-out/graph.json \
  --output graphify-out/CALL_FLOW.html
```

This creates the graph JSON, interactive HTML, architecture report, and call-flow
HTML locally without an LLM or API key.

## Query the graph

Run these from the repository root:

```bash
graphify query "Where is durable conversation state loaded and saved?"
graphify path "create_app" "stream_chat"
graphify path "AgentRuntime" "PolicyEngine"
graphify path "AgentRuntime" "SQLiteConversationStore"
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
graphify cluster-only . --no-label
graphify export callflow-html graphify-out/graph.json \
  --output graphify-out/CALL_FLOW.html
```

Commit `graphify-out/graph.json`, `graphify-out/graph.html`,
`graphify-out/GRAPH_REPORT.md`, and `graphify-out/CALL_FLOW.html`. Local cache,
manifest, cost, and model-generated labeling files are intentionally ignored.

## Suggested team walkthrough

1. Open `CALL_FLOW.html` for the static application overview.
2. Open the interactive graph and search for `AgentRuntime`.
3. Demonstrate the gateway-to-runtime relationship with
   `graphify path "create_app" "stream_chat"`.
4. Show the policy and persistence dependencies with
   `graphify path "AgentRuntime" "PolicyEngine"` and
   `graphify path "AgentRuntime" "SQLiteConversationStore"`.
5. Follow `stream_chat` into the compiled LangGraph lifecycle and generic skill
   execution nodes.
6. Run `graphify affected "ConversationState" --depth 3` to preview the future
   checkpoint-migration blast radius.
7. Contrast this static view with one real member-turn trace in Langfuse.

Graphify output is a snapshot. Refresh it whenever source-level architecture
changes are merged.
