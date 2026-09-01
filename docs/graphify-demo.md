# Graphify architecture demo

Graphify creates a static knowledge graph from this repository. It helps the
team explore code structure, dependencies, and possible request paths. It is
development tooling—not part of the member-assistant runtime and not a live
request trace. Use OpenTelemetry/Langfuse for runtime behavior.

Graphify does not modify anything under `src/`; generated files stay under
`graphify-out/`.

## Setup

This project uses Python 3.13.x and the project `.venv`:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[graphify]'

python --version       # Python 3.13.x
graphify --version     # graphify 0.9.53
```

No `uv` or `pipx` installation is required.

## Build without an LLM

Use this deterministic workflow when you only want source-code relationships.
It does not require an API key or consume model tokens:

```bash
graphify extract . --code-only --out .
graphify cluster-only . --no-label
graphify export callflow-html graphify-out/graph.json \
  --output graphify-out/CALL_FLOW.html
```

## Build with Gemini

Gemini adds semantic concepts and relationships from supported documentation,
PDFs, and images, and gives communities descriptive names. It can consume
billable tokens and may send supported repository content to Gemini, so follow
your organization's data-handling policy. Never commit the API key.

```bash
export GEMINI_API_KEY="your-key"
test -n "$GEMINI_API_KEY" && echo "Gemini key is configured"

graphify extract . --backend gemini --mode deep --out .
graphify cluster-only . --backend=gemini
graphify export callflow-html graphify-out/graph.json \
  --output graphify-out/CALL_FLOW.html
```

## View and query

No application server is required:

```bash
# macOS
open graphify-out/graph.html
open graphify-out/CALL_FLOW.html

# Linux
xdg-open graphify-out/graph.html
```

Queries traverse the existing local graph and do not call Gemini:

```bash
graphify query "How does a member message move through AgentRuntime?"
graphify explain "AgentRuntime"
graphify path "create_app" "SQLiteConversationStore"
graphify affected "ConversationState" --depth 3
```

The main outputs are:

- `graphify-out/graph.html`: interactive architecture graph
- `graphify-out/CALL_FLOW.html`: presentation-oriented static call flow
- `graphify-out/GRAPH_REPORT.md`: architecture summary and suggested questions
- `graphify-out/graph.json`: queryable graph data

## Refresh and commit

After ordinary source-code changes, refresh the AST graph locally without an
LLM:

```bash
graphify update .
graphify export callflow-html graphify-out/graph.json \
  --output graphify-out/CALL_FLOW.html
```

Commit the four main outputs listed above. Cache, manifest, cost, and local
Graphify metadata are ignored by Git.
