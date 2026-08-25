# Agentic Member Assistant POC

A small, runnable financial-services member-assistance proof of concept built with Python and LangGraph. It demonstrates a stable agent graph, dynamically discovered governed skills, deterministic controls, durable conversation state, and replaceable mock integrations. All members, accounts, transactions, URLs, cases, and knowledge in this repository are synthetic.

## What is included

- A fixed LangGraph lifecycle for state-aware goal understanding, safe ordering, durable goal/slot clarification, policy checks, generic skill execution, interruption, resumption, confirmation, and confirmed handoff.
- A provider-neutral `ModelProvider` interface. `MODEL_PROVIDER=openai` and `MODEL_ID=gpt-5.6-luna` are the demo defaults; OpenAI Responses API code is isolated in one adapter. A deterministic provider supports offline demos and tests and is the availability fallback by default.
- A JSON skill catalog that is polled while the process runs. Valid changes activate without graph recompilation. Invalid edits retain the last-known-good definition.
- One safe declarative workflow interpreter shared by five reusable execution types: `knowledge`, `guided_resolution`, `deterministic_workflow`, `navigation`, and `human_handoff`.
- Approved-knowledge, guided-balance, deterministic internal-transfer, and live-agent skills active at startup. Online-ID recovery is packaged separately for live installation.
- SQLite conversation snapshots and privacy-safe audit events.
- Provider-neutral structured tracing with console, in-memory test, and local Langfuse/OpenTelemetry sinks. Content is redacted and session identifiers are hashed by default.
- Typed mock adapters for member profile, knowledge, accounts, transfers, navigation, and live support.

## Setup

Python 3.9 or later is supported.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,observability]'
```

Copy the safe template to the default user-secret location and add your API
key. The application loads both the project's `.env` and
`~/.secrets/dev.env` automatically. Variables exported by the shell take
precedence, followed by the user secret file, the project `.env`, and built-in
defaults. `.env.example` is a template only and is never loaded:

```bash
mkdir -p ~/.secrets
cp .env.example ~/.secrets/dev.env
```

Run completely offline:

```bash
MODEL_PROVIDER=mock member-assistant --db data/demo.db
```

Run with the configurable default OpenAI adapter:

```bash
member-assistant --db data/demo.db
```

Use a distinct session name for each clean demo. Reusing the same database and
session deliberately restores unfinished tasks and prior clarification state,
provided that the session has not been inactive for 10 minutes:

```bash
member-assistant --db data/demo.db --session transfer-demo-01
```

Conversation snapshots expire after 10 minutes of inactivity by default. The
application removes expired snapshots at startup, when state is loaded, and
periodically while it is running. Audit events are retained for troubleshooting
and skill-gap reporting. Configure seconds in an environment file, use a CLI
override for a particular run, or set either value to zero to disable expiry:

```bash
SESSION_TTL_SECONDS=600
member-assistant --db data/demo.db --session-ttl-minutes 10
```

The default `MODEL_PROVIDER` is `openai`, and the default model is `gpt-5.6-luna`. The OpenAI adapter uses the Responses API with `MODEL_REASONING_EFFORT=low`; it does not send legacy `temperature` options. Configure `OPENAI_API_KEY` in `~/.secrets/dev.env`. If no key is present—or the provider fails—and `ALLOW_PROVIDER_FALLBACK=true` (the template default), the runtime safely uses deterministic catalog routing. Set `ALLOW_PROVIDER_FALLBACK=false` to require the configured provider and expose API failures directly in the CLI. To use a different user-secret file, export `MEMBER_ASSISTANT_ENV_FILE=/path/to/file`; the project `.env` remains the lower-priority local configuration source. The repository's `.env.example` contains no secret and is never read at runtime.


Useful CLI commands are `/skills`, `/state`, `/trace`, `/add-online-id`, and `/quit`.

## Conversation behavior

Goal understanding runs for every member utterance, with the active task,
missing field, pending question, and resume state supplied as context to the
provider. The runtime then applies deterministic conversation controls:

- A plausible answer to a requested slot is collected and validated before it
  is treated as a new task. Natural mock-account references such as `checking
  in 1001` and `saving 2002` are normalized.
- A clear different goal pauses current work. After the interrupting goal is
  served, the member is asked whether to resume or discard the paused goal.
- Close alternative goal candidates produce a durable disambiguation question.
  Explicit multi-goal utterances such as “check my balance and transfer $25”
  remain multiple tasks and are ordered by policy risk.
- Greeting and capability-help behavior is a cross-cutting conversation policy,
  not a business skill competing for selection. A synthetic member-profile tool
  loads the preferred name once per durable session, and the assistant greets
  the member once. Greetings and unmatched-request guidance list only currently
  installed catalog skills; each goal supplies its member-facing `display_name`.
  On an unmatched turn, the provider writes a short, constrained receptionist
  response that distinguishes a clear-but-unavailable request from a genuinely
  unclear request. The deterministic provider supplies the safe friendly fallback.
- Frustration, an explicit live-agent request, or three consecutive unproductive
  turns creates a yes/no handoff offer. No case is created until the member says
  yes; the existing declarative handoff skill then receives the active goal and
  completed-step context.

The LLM supplies structured goal candidates and extracted inputs, but does not
choose policy outcomes or execute consequential tools. Strong catalog keyword
matches are merged with model output so an explicit phrase such as “live agent”
cannot be lost because of an invalid model confidence score.

The same understanding result can contain a `skill_gap` when the member has a
clear objective but no installed skill supports it. The assistant acknowledges
the understood objective and states that it does not currently have that ability.
The runtime writes a `skill_gap` audit event and a visible `skill_gap.detected`
trace with a sanitized objective, stable business category, confidence, catalog
revision, provider, and model. It does not place the raw member utterance in the
skill-gap audit payload. Small talk, unclear fragments, and plausible slot answers
are not skill gaps and continue through normal clarification behavior.

Filter Langfuse observations by `skill_gap.detected` to review individual gaps.
The durable SQLite audit can also be aggregated by business category:

```bash
sqlite3 data/demo.db "SELECT json_extract(payload_json, '$.category') AS category, COUNT(*) AS requests, ROUND(AVG(json_extract(payload_json, '$.confidence')), 2) AS avg_confidence FROM audit_events WHERE event_type = 'skill_gap' GROUP BY category ORDER BY requests DESC;"
```

## Logging and tracing

The runtime emits one trace for each member turn, with nested observations for state loading and persistence, LangGraph nodes, goal detection, skill-gap detection, planning, policy evaluation, skill execution, declarative workflow steps, mock tools, grounded model responses, confirmation, and outcomes. New JSON-only skills receive the same tracing automatically.

Console tracing is enabled by default. Interactive runs use compact, color-coded output for the important LLM, policy, skill, tool, and turn observations. It records decision evidence such as goal candidates and confidence, selected skill and version, risk tier, policy result, model/provider and fallback status, tool outcome, latency, and OpenAI token usage when available. It does not record hidden model reasoning. Set `TRACE_CONSOLE_FORMAT=json` or pass `--trace-format json` when machine-readable JSON lines are needed; `--log-level DEBUG` also displays lower-level graph and state spans in pretty mode.

### How to read the CLI trace

Read the compact output from top to bottom as the path taken for one member
utterance. A green check means that stage completed; a red `x` means that stage
raised an error. The time at the right is that stage's elapsed time in
milliseconds.

| Output | Meaning |
| --- | --- |
| `HTTP Request ... 200 OK` | OpenAI SDK HTTP logging. It confirms that OpenAI accepted the request; it is not a Langfuse export message. |
| `LLM llm.goal_detection` | The model analyzed the utterance for supported goals, extracted inputs, ambiguity, or a skill gap. It did not execute the goal. |
| `POLICY policy.evaluate` | Deterministic authentication, authorization, risk, and confirmation controls evaluated the selected skill. |
| `TOOL tool.<name>` | A typed integration was called. Every integration in this POC is mock/local even when its name describes accounts, transfers, or a live agent. |
| `SKILL skill.<name>` | The declarative skill workflow completed its current pass. It may have asked for missing input, paused for confirmation, or produced an outcome. |
| `TURN member-assistant.turn` | The root observation summarizing the complete member turn, including model, policy, tools, skill execution, state persistence, and reply. |
| `assistant>` | The member-facing reply. |
| `model(last call)>` | A concise verification of which configured provider/model actually handled the most recent model operation. |

Common metadata fields are:

| Field | Meaning |
| --- | --- |
| `provider=openai` / `model=gpt-5.6-luna` | The active provider adapter and exact model ID. |
| `endpoint=responses` | The OpenAI Responses API handled the model call. |
| `reasoning=low` | Configured reasoning effort. This is a setting, not hidden reasoning text; chain-of-thought is not logged. |
| `fallback=no` | The configured provider succeeded. `fallback=yes` means the deterministic availability provider handled that operation. |
| `in_tokens` / `out_tokens` | Tokens sent to and returned by the model for this call. |
| `skill` | The catalog skill selected for policy or execution. |
| `risk_tier` | Governance category: `informational`, `navigation`, `read_only`, `consequential`, or `handoff`. It controls policy handling; it is not a model confidence score. |
| `decision=policy_approved` | Deterministic policy allowed the skill to proceed. |
| `confirmation` | Whether a consequential action is waiting for, has received, or does not require confirmation at this stage. |
| `outcome=queued` | The mock workflow's terminal status. For handoff, `queued` means a synthetic support case was created. |
| `goal_clarification` | Whether the runtime is waiting for the member to choose between plausible goals. |
| `handoff_offer` | Whether a proactive frustration/no-progress handoff offer is waiting for yes/no. It remains `no` for a direct member-requested handoff. |
| `no_goal_turns` | Consecutive turns that did not produce a supported goal; a successful goal resets it to zero. |

For the sample handoff trace, the sequence is: Luna recognized a direct live-agent
goal, deterministic policy approved the governed handoff skill, the mock live-agent
tool created a synthetic case, the skill reported `queued`, and the complete turn
took about 1.16 seconds. `handoff_offer=no` means this was not a pending proactive
offer—it was already processed as a direct request.

Use CLI overrides when testing:

```bash
# No traces
member-assistant --provider mock --trace off

# Human-readable chat on stdout and structured trace JSON on stderr
member-assistant --provider mock --trace console --log-level DEBUG

# Preserve the original machine-readable JSON lines
member-assistant --provider mock --trace console --trace-format json

# Export only to local Langfuse
member-assistant --provider mock --trace langfuse

# Console and Langfuse together
member-assistant --provider mock --trace both
```

`/trace` prints the active tracing configuration. Environment equivalents are documented in `.env.example`; put their values in `~/.secrets/dev.env` or the project `.env`.

### Local Langfuse

The repository includes a local-only Langfuse v4 Docker Compose stack. It runs Langfuse web and worker services plus PostgreSQL, ClickHouse, Redis, and MinIO. Only the UI on `127.0.0.1:3000` and the local MinIO API on `127.0.0.1:9090` are published; Langfuse product telemetry is disabled. The static credentials are intentionally for an isolated development POC and must not be reused or exposed on a shared host.

```bash
member-assistant-observability up
member-assistant-observability status
member-assistant-observability doctor
member-assistant-observability url
```

Open [http://localhost:3000](http://localhost:3000) and sign in with:

```text
demo@member-assistant.local
local-observability-demo
```

Generate a trace and then open the `Agentic Member Assistant POC` project:

```bash
member-assistant --provider mock --trace both --session tracing-demo
```

For normal OpenAI testing, either set `TRACE_BACKENDS=console,langfuse` or pass
`--trace both`. Restart the CLI after changing an environment file, then enter
`/trace`; its `backends` list must contain both `console` and `langfuse`. Exports
are batched and normally appear shortly after a turn. With
`TRACE_HASH_SESSION_ID=true`, Langfuse displays a value such as
`sha256:3806594b03a90823` rather than the raw CLI `--session` value.

If traces are absent, verify both the server and the configured exporter:

```bash
member-assistant-observability status
member-assistant-observability doctor
member-assistant --trace both --session tracing-check
# In the CLI:
/trace
```

`doctor` verifies server health, project-key authentication, and the latest
ingested observation. Seeing console trace lines alone proves only that the
console backend is active; it does not prove that Langfuse export is enabled.

Try “Transfer $50 from checking to savings,” inspect the trace, then answer “yes” and compare the two turns in the same hashed Langfuse session. Stop the stack without deleting trace volumes using:

```bash
member-assistant-observability down
```

The application sends standard OTLP/HTTP observations to Langfuse. Langfuse is an optional visualization and analysis destination; SQLite conversation state and audit events remain authoritative.

### Privacy controls

`TRACE_INCLUDE_CONTENT=false` is the default. Model prompts, member messages, mock balances, tool arguments/results, and replies are replaced with shape and length summaries. Session identifiers are SHA-256-derived labels when `TRACE_HASH_SESSION_ID=true`. For this synthetic local POC only, `--trace-content` can expose mock inputs and outputs in traces. Do not enable it with real member or financial data.

## Hot-reload demonstration

Start the CLI and verify that four skills are active:

```text
member> /skills
member> What is my balance?
assistant> Which account would you like ...?
member> /add-online-id
member> I forgot my online ID
assistant> Use the approved online-ID recovery page ... Would you like to resume ...?
member> resume
member> checking
```

`/add-online-id` atomically copies `skills/available/online_id.json` into `skills/catalog/`. The catalog notices it without restarting, and the already-compiled graph routes through its generic execution node. To return the checked-out demo to its initial four-skill state, remove that copied catalog file before the next run.

## Add a skill

Create one JSON file per skill. The catalog contract requires a name, version, generic execution type, description, owner, risk tier, supported goals and routing keywords, JSON input schema, allowed tools, response template, input-extraction metadata, and a declarative workflow. Give each goal a natural, member-facing `display_name`; the receptionist and goal-disambiguation copy derive their wording from it. Put approved candidate definitions in `skills/available/`, then copy or atomically publish one into `skills/catalog/`.

Skill types describe reusable execution patterns, not business capabilities. For example, account balance is a `guided_resolution`; internal transfer is a `deterministic_workflow`. The workflow uses a validated operation set: `collect`, `call_tool`, `select`, `validate`, `validate_decimal`, `set`, `confirm`, and `respond`. Adding a new skill that composes these operations and existing tools requires only a new JSON file. If a required integration does not exist, add a tool adapter; the common LangGraph and workflow interpreter do not change. Invalid files are reported by `/skills` and never replace the last valid version.

Consequential tool calls must be marked in the workflow and must immediately follow a `confirm` step. The catalog rejects definitions that violate this order or reference a tool outside the skill's `allowed_tools`.

## Tests

```bash
pytest
```

The suite covers personalized greeting, no-goal escalation offers, goal disambiguation, natural slot fulfillment, grounded FAQ answers, balance clarification and restart durability, multi-goal ordering, transfer review/confirmation/execution, authentication policy, interruption with resume and discard, confirmed live-agent handoff, runtime skill discovery, a configuration-only new guided skill, stable graph identity, and invalid-catalog rollback.

## Project map

```text
src/member_assistant/
  runtime.py, models.py       stable graph and explicit conversation/task state
  catalog.py                  discovery, validation, watcher, last-known-good cache
  state_store.py, policy.py   SQLite durability/audit and deterministic controls
  observability.py            console/memory tracing and Langfuse OTLP exporter
  providers/                  provider-neutral contract, OpenAI, offline provider
  skills/                     one validated declarative workflow interpreter
  tools/                      typed mock adapters and generic tool registry
  cli.py                      local chat demo
skills/catalog/               four startup definitions
skills/available/             online-ID definition for hot installation
data/knowledge.json           approved mock FAQ content
tests/                        automated acceptance scenarios
observability/                local Langfuse v4 Docker Compose stack
```

## Intentional POC simplifications

- Keyword routing and catalog-defined extraction rules are the deterministic fallback and test double; they are deliberately transparent rather than a production NLU system.
- The declarative operation set is intentionally small. A novel integration requires a tool adapter; a novel reusable control may require a new platform operation, but never a capability-specific executor.
- The file watcher is a local polling thread, not a governed publishing service.
- SQLite stores one local process's state; production would use encrypted shared storage, retention controls, and LangGraph-compatible distributed checkpoints.
- Authentication and authorizations are synthetic session flags. URLs, balances, transfer receipts, and handoff cases are mock values only.
- Policy/audit coverage demonstrates control boundaries but does not claim production compliance, fraud controls, or regulated-advice support.
