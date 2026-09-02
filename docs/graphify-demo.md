# Graphify engineer guide

Graphify turns this repository into a local, persistent knowledge graph. It is
useful when the question is about relationships rather than a single known
file: request flow, ownership, dependencies, change impact, or where to begin
debugging an unfamiliar behavior.

Graphify is development tooling. It is not part of the member-assistant
runtime, and it does not record what happened in a live conversation. Use
application logs, OpenTelemetry, or Langfuse for runtime evidence; use Graphify
to understand the code paths that could have produced that evidence.

Generated artifacts stay under `graphify-out/`. Graphify does not modify
application source under `src/`.

## Quick start

The project virtual environment currently provides Graphify 0.9.53. Calling
the executable by its project-relative path avoids relying on an activated
shell:

```bash
.venv/bin/graphify --version
.venv/bin/graphify query \
  "How does a member message move through AgentRuntime?"
.venv/bin/graphify explain "AgentRuntime"
open graphify-out/graph.html                 # macOS
```

On Linux, use `xdg-open graphify-out/graph.html`.

If the virtual environment has not been prepared:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -e '.[graphify]'
```

## How to choose a command

| Need | Command | What it provides |
| --- | --- | --- |
| Understand a behavior or subsystem | `graphify query "<question>"` | A small, question-relevant subgraph with source locations |
| Focus on one class, function, or concept | `graphify explain "<name>"` | Its role, neighbors, and supporting context |
| Prove how two things connect | `graphify path "<A>" "<B>"` | The relationship chain between them |
| Estimate change impact | `graphify affected "<name>" --depth 3` | Downstream nodes that may be affected |
| Find architectural hubs | `graphify god-nodes` | Highly connected entry points and coordinating components |
| Explore visually | Open `graphify-out/graph.html` | Searchable, interactive graph exploration |
| Read a broad snapshot | Open `graphify-out/GRAPH_REPORT.md` | Generated architecture overview and graph statistics |

Start with `query`, `path`, or `explain`. They return a scoped result and are
usually more useful than reading the entire generated report or grepping the
whole repository.

## The workflow Codex uses

For a Nexus codebase question, Codex follows this sequence:

1. Ask the existing graph a natural-language question with `graphify query`.
2. Use `path` when a claimed relationship needs to be verified, or `explain`
   when a component needs more context.
3. Open only the source files and tests surfaced by that graph slice.
4. Compare the static relationships with runtime logs or a transcript when
   diagnosing actual behavior.
5. Make and test the change.
6. Run `graphify update .` so later questions see the new code structure.

This is how Graphify reduces exploration time: it narrows the initial search,
but source code and tests remain the final authority.

## Nexus troubleshooting examples

Run these from the repository root.

### A slot was filled from the wrong phrase

For example, an account suffix such as `2003` was incorrectly interpreted as
a transfer amount:

```bash
.venv/bin/graphify query \
  "How are semantic slot updates extracted, validated, and applied during a turn?"
.venv/bin/graphify explain "TurnAnalysis"
.venv/bin/graphify path "AgentRuntime" "DeclarativeSkillExecutor"
.venv/bin/graphify affected "SlotUpdate" --depth 3
```

Use the result to locate the provider contract, runtime application logic,
skill executor, and relevant tests. Then compare those static paths with the
failing transcript to determine whether extraction, validation, or state
application was responsible.

### The assistant repeats a disambiguation question

```bash
.venv/bin/graphify query \
  "How does the runtime distinguish a confirmation from intent disambiguation?"
.venv/bin/graphify path "AgentRuntime" "DeterministicProvider"
.venv/bin/graphify explain "FallbackProvider"
```

This helps separate responsibilities among the LLM provider, deterministic
fallback, route selection, and the runtime state machine.

### A skill changed but the application behavior did not

```bash
.venv/bin/graphify query \
  "How does the active skill catalog reach AgentRuntime and skill execution?"
.venv/bin/graphify explain "SkillCatalog"
.venv/bin/graphify path "SkillCatalog" "AgentRuntime" --undirected
```

The resulting graph slice is a good starting point for checking catalog
loading, active-version selection, parsing, caching, and executor wiring.

### Conversation state behaves differently after restart

```bash
.venv/bin/graphify query \
  "How are active goals, collected slots, and pending confirmations persisted?"
.venv/bin/graphify path "AgentRuntime" "SQLiteConversationStore"
.venv/bin/graphify affected "ConversationState" --depth 3
```

Pair this with storage inspection and restart tests. The graph shows possible
relationships; it cannot show the values from a particular live session.

### Learn the architecture or plan a refactor

```bash
.venv/bin/graphify god-nodes
.venv/bin/graphify explain "AgentRuntime"
.venv/bin/graphify query \
  "What are the major stages of the member-assistant turn lifecycle?"
.venv/bin/graphify affected "TurnAnalysis" --depth 3
```

`god-nodes` identifies architectural hubs. `affected` gives a first-pass blast
radius before changing a shared contract, but it should be followed by source
inspection and tests because dynamic behavior may not appear in a static graph.

## Explore the HTML graph

Open the interactive graph directly; no application server is required:

```bash
open graphify-out/graph.html                 # macOS
xdg-open graphify-out/graph.html             # Linux
```

A practical exploration loop is:

1. Search for a known anchor such as `AgentRuntime`, `TurnAnalysis`, or
   `SkillCatalog`.
2. Select the node to inspect its type, source location, community, and nearby
   relationships.
3. Zoom into its community and follow edges to callers, callees, tests,
   configuration, or related concepts.
4. Treat `EXTRACTED` relationships as code-derived evidence. Treat
   `INFERRED` or `AMBIGUOUS` relationships as leads to verify in source.
5. Switch to the CLI `path` command when the visual graph is too dense and an
   exact A-to-B relationship is needed.
6. Open the returned source locations and confirm the behavior in code.

`graphify-out/CALL_FLOW.html` is a more presentation-oriented call-flow view.
Regenerate it after a structural change:

```bash
.venv/bin/graphify export callflow-html graphify-out/graph.json \
  --output graphify-out/CALL_FLOW.html
open graphify-out/CALL_FLOW.html
```

The main generated artifacts are:

| Artifact | Best use |
| --- | --- |
| `graphify-out/graph.html` | Interactive exploration and search |
| `graphify-out/CALL_FLOW.html` | High-level walkthroughs and demos |
| `graphify-out/GRAPH_REPORT.md` | Broad architecture summary and statistics |
| `graphify-out/graph.json` | CLI queries and machine-readable graph data |

## Keep the graph fresh

After meaningful source-code changes, run:

```bash
.venv/bin/graphify update .
```

This performs an incremental, AST-based refresh without an API call. If a
large intentional refactor or deletion triggers Graphify's shrink protection,
review the change first and then use:

```bash
.venv/bin/graphify update . --force
```

For automatic local refreshes, Graphify also supports repository hooks:

```bash
.venv/bin/graphify hook install
.venv/bin/graphify hook status
```

Dirty files under `graphify-out/` are expected after an update. They are
generated review artifacts, not a reason to skip Graphify queries.

The incremental `update` command refreshes source-code structure. If semantic
content from documentation, PDFs, or images must be rebuilt, perform a full
extraction with an approved semantic backend. That may send supported content
to the provider and consume billable tokens, so follow organizational data
handling rules and never commit API keys. For example, with an approved Gemini
configuration:

```bash
export GEMINI_API_KEY="your-key"
.venv/bin/graphify extract . --backend gemini --mode deep --out .
.venv/bin/graphify cluster-only . --backend=gemini
```

For a deterministic code-only rebuild that does not call an LLM:

```bash
.venv/bin/graphify extract . --code-only --out .
.venv/bin/graphify cluster-only . --no-label
```

## What Graphify cannot tell you

- It is a snapshot and is only as current as the last refresh.
- It shows static and semantic relationships, not the exact route taken by a
  live request, its timing, model output, or stored values.
- Dynamically resolved calls and configuration-driven behavior may be
  incomplete.
- Inferred relationships are hypotheses, not proof.
- It complements source review, tests, logs, and traces; it does not replace
  them.

For this repository, `AGENTS.md` instructs Codex to query the graph first for
codebase questions and to update it after code changes. Engineers can use the
same pattern manually: graph first to narrow the problem, source and runtime
evidence to prove it, then refresh the graph after the fix.
