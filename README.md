# Agentic Member Assistant POC

A small, runnable financial-services member-assistance proof of concept built with Python and LangGraph. It demonstrates a stable agent graph, dynamically discovered governed skills, deterministic controls, durable conversation state, and replaceable mock integrations. All members, accounts, transactions, URLs, cases, and knowledge in this repository are synthetic.

An interactive, development-only code map is available in
[`graphify-out/graph.html`](graphify-out/graph.html). See
[`docs/graphify-demo.md`](docs/graphify-demo.md) for installation, queries, graph
refresh instructions, and a short team walkthrough. Graphify is an optional
Python 3.10+ developer extra installed with `python -m pip install -e
'.[graphify]'`; the extra includes optional Gemini semantic extraction support
but is not an application runtime dependency.

## What is included

- A fixed LangGraph lifecycle for state-aware goal understanding, safe ordering, durable goal/slot clarification, policy checks, generic skill execution, interruption, resumption, confirmation, and confirmed handoff.
- A provider-neutral `ModelProvider` interface. Direct OpenAI Responses and Amazon Bedrock Converse are isolated adapters behind the same turn-understanding contract. Bedrock supports Amazon Nova and Bedrock-hosted OpenAI models such as GPT-5.6 Terra. A deterministic provider supports offline demos and availability fallback.
- A versioned file catalog that polls a lightweight active routing index. New immutable skill artifacts activate without process restart or graph recompilation; invalid index updates retain the last-known-good catalog.
- One portable, business-facing `SKILL.md` artifact format plus a safe declarative workflow interpreter shared by built-in and custom authoring archetypes. There is no parallel JSON skill representation.
- Approved-knowledge, guided-balance, deterministic internal-transfer, and live-agent skills active at startup. Online-ID recovery is packaged separately for live installation.
- SQLite conversation snapshots and privacy-safe audit events.
- A provider-neutral durable event stream, FastAPI WebSocket/REST service,
  replay cursors, and idempotent member-message IDs. The terminal member client
  uses the same WebSocket contract intended for a future browser chat UI.
- Provider-neutral structured tracing with console, in-memory test, and local Langfuse/OpenTelemetry sinks. Content is redacted and session identifiers are hashed by default.
- Typed mock adapters for member profile, knowledge, accounts, transfers, navigation, and live support.

## Setup

Python 3.9 or later is supported by the base POC. Use Python 3.10 or later for
Bedrock so Boto3 receives current AWS service updates and security fixes; the
last Python 3.9-compatible SDK can run the adapter but emits a deprecation
warning.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,ui,observability,bedrock]'
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

Run the socket service completely offline in one terminal:

```bash
MODEL_PROVIDER=mock member-assistant-server --db data/demo.db
```

Then run the member-only WebSocket client in another terminal:

```bash
member-assistant
```

The member client contains no catalog, state, or tracing commands. Press
Ctrl-D or Ctrl-C to leave it. System operations use `member-assistant-admin`,
skill lifecycle operations use `member-assistant-skills`, and local Langfuse
operations use `member-assistant-observability`.

### Live MSR demo

The optional Streamlit apps provide a browser member experience and a
multi-member MSR workspace. Start the API and each UI in a separate terminal:

```bash
MODEL_PROVIDER=mock member-assistant-server --db data/live-demo.db
member-assistant-member-ui
member-assistant-msr-ui
```

Open the Member UI at `http://localhost:8501` and the MSR UI at
`http://localhost:8502`. The Member UI asks for a name and Member ID; the
Member ID is used directly as the durable `session_id`. Opening another Member
UI with the same ID restores conversation history and receives the same live
assistant or MSR events.

An MSR supplies a display name and joins exactly one of `insurance`, `banking`,
or `advice`. Waiting cases are assigned automatically to the online MSR in that
queue with the fewest active conversations. An MSR can handle several assigned
members by switching conversation tabs. If nobody is online, the member remains
in a durable waiting state and can cancel the request.

The handoff skill collects the reason, lets the configured model derive the
queue, and asks the member to choose a queue when it cannot do so confidently.
The assigned MSR receives minimized recent context as a system summary and the
current member-sentiment signal. During live support, member messages bypass
the conversational graph and route only to the assigned MSR, while sentiment,
audit, and observability updates continue. Either participant can send `/end`;
the member is returned to the virtual assistant automatically.

Run the server with the configurable default OpenAI adapter by omitting the
`MODEL_PROVIDER=mock` prefix. Provider, model, database, catalog, trace, and
retention overrides belong to `member-assistant-server`, not the member client:

```bash
member-assistant-server --provider openai --db data/demo.db --trace both
```

Use a distinct session name for each clean demo. Reusing the same database and
session deliberately restores unfinished tasks and prior clarification state,
provided that the session has not been inactive for 10 minutes:

```bash
member-assistant --session transfer-demo-01
```

Conversation snapshots expire after 10 minutes of inactivity by default. The
application removes expired snapshots at startup, when state is loaded, and
periodically while it is running. A member WebSocket that reaches the same idle
limit receives a terminal `session.expired` event and is then closed with code
`4001`; transport-level ping/pong traffic does not extend the application
session. The demo UI returns to sign-in instead of reconnecting automatically.
Audit events are retained for troubleshooting and skill-gap reporting. Configure
seconds in an environment file, use a CLI override for a particular run, or set
either value to zero to disable expiry:

```bash
SESSION_TTL_SECONDS=600
member-assistant-server --db data/demo.db --session-ttl-minutes 10
```

The default `MODEL_PROVIDER` is `openai`, and the default direct OpenAI model is
`gpt-5.6-luna`. The OpenAI adapter uses the Responses API with
`MODEL_REASONING_EFFORT=low`; it does not send legacy `temperature` options.
Configure `OPENAI_API_KEY` in `~/.secrets/dev.env`.

For provider interoperability, configure each provider's model once and switch
only `MODEL_PROVIDER`:

```dotenv
MODEL_PROVIDER=bedrock
OPENAI_MODEL_ID=gpt-5.6-luna
BEDROCK_MODEL_ID=us.amazon.nova-2-lite-v1:0
# To use Terra through Bedrock instead:
# BEDROCK_MODEL_ID=us.openai.gpt-5.6-terra

BEDROCK_AWS_REGION=us-east-1
BEDROCK_AWS_PROFILE=member-assistant-dev
```

The Bedrock adapter uses the standard AWS credential chain. Do not put AWS
access or secret keys in the project `.env`; use an AWS profile for local work
or a workload/IAM role in a deployed service. The calling identity needs model
inference access, including `bedrock:InvokeModel`, and the selected model must be
available in the configured Region. You can also test a one-off combination
with `member-assistant-server --provider bedrock --model <model-id>`.
`MODEL_REASONING_EFFORT` currently applies only to the direct OpenAI adapter;
Bedrock Converse uses each selected model's default reasoning behavior so the
shared adapter does not send a model-specific option that Nova or Terra might
reject.

An optional Bedrock Guardrail is attached to every Converse call when its ID and
version are both configured:

```dotenv
BEDROCK_GUARDRAIL_ID=your-guardrail-id
BEDROCK_GUARDRAIL_VERSION=DRAFT
BEDROCK_GUARDRAIL_TRACE=disabled
```

The AWS identity also needs permission to apply that guardrail. A
`guardrail_intervened` result becomes the member-facing configured block message
and a redacted audit event. It is a safety decision, not provider downtime, so
the deterministic fallback never bypasses it. Raw guardrail assessments are not
logged even when AWS guardrail tracing is enabled.

If no OpenAI key is present—or an ordinary configured-provider call fails—and
`ALLOW_PROVIDER_FALLBACK=true` (the template default), the runtime safely uses
deterministic catalog routing. Set `ALLOW_PROVIDER_FALLBACK=false` to require the
configured provider and expose API failures as safe streamed turn failures. To use a
different user-secret file, export
`MEMBER_ASSISTANT_ENV_FILE=/path/to/file`; the project `.env` remains the
lower-priority local configuration source. The repository's `.env.example`
contains no secret and is never read at runtime.


Useful system commands are `member-assistant-admin skills`,
`member-assistant-admin state`, `member-assistant-admin trace`,
`member-assistant-admin add-online-id`, and
`member-assistant-admin remove-online-id`.

## Socket and streaming architecture

The process owns one `AgentRuntime` and one compiled LangGraph. Every member
turn passes through that graph; hot-reloaded `SKILL.md` artifacts change the
available goals and declarative execution plan without creating another graph,
restarting the server, or changing the WebSocket protocol.

The WebSocket endpoint is:

```text
/v1/sessions/{session_id}/stream
```

The member sends an idempotent message:

```json
{
  "type": "member.message",
  "message_id": "msg_client_generated_unique_id",
  "content": "Tell me my balance and then help me transfer money"
}
```

The server responds with ordered durable events such as:

```text
turn.accepted
assistant.message
assistant.request_input
assistant.request_confirmation
handoff.offered
turn.completed
```

Each durable event contains `event_id`, `session_id`, `turn_id`, per-turn
`sequence`, `type`, `created_at`, `final`, optional `content`, and safe
`metadata`. Reusing the same `message_id` with the same content replays its
original turn instead of running tools or a consequential action twice. Reusing
it with different content is rejected.

Reconnect with `?after_event_id=<event-id>` to replay only later committed
events. `GET /v1/sessions/{session_id}/events` exposes the same replay log, and
`GET /v1/sessions/{session_id}` returns the durable state plus events for local
inspection. Conversation snapshots, replay events, and idempotency receipts use
the configured session TTL; privacy-safe audit history is retained separately.
Every socket connected to the same session receives the live event stream. Turn
execution runs independently of any one connection, so disconnecting a browser
does not cancel or duplicate the durable graph turn.

This first version streams meaningful conversation events, not hidden model
reasoning and not raw token deltas. Goal detection remains a structured provider
call. Longer grounded responses can later add provider token-delta events behind
the same runtime contract. The same socket transport also carries live-agent
participation and ownership routing for the single-process demo. Durable SQLite
state remains authoritative; the in-process event hubs can later be replaced
with a shared broker for a multi-instance deployment.

## Conversation behavior

Semantic turn understanding runs for every member utterance, with the active
task, current inputs, full input schema, missing field, pending question, and
resume state supplied as context to the provider. One result can identify a new
goal, interpret several active-task inputs, recognize a correction, or report
ambiguity. The runtime accepts only schema-declared slot values above its
confidence threshold, then applies deterministic conversation controls:

- A member can answer more than the field just requested. For example, “from
  saving to checking” supplies both transfer accounts, and “two hundred” can be
  normalized to `200.00`. Mock account tools and schema validators still verify
  those interpretations before the workflow advances.
- A correction made at confirmation invalidates the previous review, restarts
  deterministic validation with the corrected values, and presents a new
  review. It never edits an already-confirmed submission.
- A clear different goal pauses current work. After the interrupting goal is
  served, the member is asked whether to resume or discard the paused goal.
- Close alternative goal candidates produce a durable disambiguation question.
  Explicit multi-goal utterances such as “check my balance and transfer $25”
  remain multiple tasks and are ordered by policy risk. The assistant announces
  that plan, completes the first request, and then asks before beginning the next
  queued request. That transition decision survives a restart and is separate
  from the final confirmation required to submit a consequential action.
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

The LLM supplies structured goal candidates, field-level slot interpretations
with confidence, and the conversational relationship to the active goal. It
does not choose policy outcomes, declare inputs valid, order workflow steps, or
execute tools. Strong catalog keyword matches are merged with model output so an
explicit phrase such as “live agent” cannot be lost because of an invalid model
confidence score. The deterministic fallback deliberately performs narrower
single-field extraction rather than pretending to be a production NLU system.

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

The runtime emits one trace for each member turn, with nested observations for state loading and persistence, semantic turn understanding, skill-gap detection, planning, policy evaluation, skill execution, declarative workflow steps, mock tools, grounded model responses, confirmation, and outcomes. Newly published declarative skills receive the same tracing automatically.

Console tracing is enabled by default. Interactive runs use compact, color-coded output for the important LLM, policy, skill, tool, and turn observations. It records decision evidence such as goal candidates and confidence, selected skill and version, risk tier, policy result, model/provider and fallback status, tool outcome, latency, and provider token usage when available. It does not record hidden model reasoning. Set `TRACE_CONSOLE_FORMAT=json` or pass `--trace-format json` when machine-readable JSON lines are needed; `--log-level DEBUG` also displays lower-level graph and state spans in pretty mode.

### How to read server traces and member events

The server terminal owns model, policy, skill, tool, and Langfuse traces. Read
its compact output from top to bottom as the path taken for one member
utterance. A green check means that stage completed; a red `x` means that stage
raised an error. The member-client terminal receives only the safe conversation
event stream. The time at the right of a server trace is that stage's elapsed
time in milliseconds.

| Output | Meaning |
| --- | --- |
| `HTTP Request ... 200 OK` | Direct OpenAI SDK HTTP logging. It confirms that OpenAI accepted the request; it is not a Langfuse export message. Bedrock calls do not normally print this line. |
| `LLM llm.turn_understanding` | The model interpreted supported goals, all active-task slot updates, corrections, ambiguity, or a skill gap. It did not validate data or execute the goal. |
| `POLICY policy.evaluate` | Deterministic authentication, authorization, risk, and confirmation controls evaluated the selected skill. |
| `TOOL tool.<name>` | A typed integration was called. Every integration in this POC is mock/local even when its name describes accounts, transfers, or a live agent. |
| `SKILL skill.<name>` | The declarative skill workflow completed its current pass. It may have asked for missing input, paused for confirmation, or produced an outcome. |
| `TURN member-assistant.turn` | The root observation summarizing the complete member turn, including model, policy, tools, skill execution, state persistence, and reply. |
| `assistant>` | A member-facing WebSocket message rendered by the member client. |
| `assistant is working…` | The durable `turn.accepted` event arrived and server processing has begun. |
| `model(last call)>` | Completion-event metadata showing which provider/model handled the most recent model operation. |

Common metadata fields are:

| Field | Meaning |
| --- | --- |
| `provider=openai` / `model=gpt-5.6-luna` | The active provider adapter and exact model ID. |
| `endpoint=responses` | The OpenAI Responses API handled the model call. |
| `endpoint=converse` / `region=us-east-1` | Amazon Bedrock Converse handled the call in the displayed AWS Region. |
| `guardrail=enabled` | A configured Bedrock Guardrail was attached. `guardrail=intervened` means it blocked the input or output and fallback was not used. |
| `stop=end_turn` | Bedrock's reason for ending generation. Other useful values include `max_tokens`, `guardrail_intervened`, and `content_filtered`. |
| `request_id` / `provider_ms` | AWS request identifier and Bedrock-reported model latency for troubleshooting. |
| `reasoning=low` | Configured reasoning effort. This is a setting, not hidden reasoning text; chain-of-thought is not logged. |
| `fallback=no` | The configured provider succeeded. `fallback=yes` means the deterministic availability provider handled that operation. |
| `in_tokens` / `out_tokens` | Tokens sent to and returned by the model for this call. |
| `goal_aliases` | Number of model-returned friendly goal labels safely normalized to catalog goal IDs. It appears only when nonzero. |
| `invalid_goals` | Number of undeclared model-returned goals rejected before routing. It appears only when nonzero. |
| `act` | The interpreted conversational act, such as `provide_information`, `correction`, or `new_goal`. |
| `relation` | Whether the utterance continues, replaces, or is ambiguous relative to the active goal. |
| `slots` | Schema-declared active-task fields understood from this utterance. Values remain redacted from the compact trace. |
| `invalid_slots` | Low-confidence or schema-invalid slot interpretations rejected before task state changed. It appears only when nonzero. |
| `skill` | The catalog skill selected for policy or execution. |
| `version` / `artifact` | The selected immutable semantic version and the first 12 characters of its content hash. Langfuse and JSON traces retain the full `skill_artifact_hash`. |
| `risk_tier` | Governance category: `informational`, `navigation`, `read_only`, `consequential`, or `handoff`. It controls policy handling; it is not a model confidence score. |
| `decision=policy_approved` | Deterministic policy allowed the skill to proceed. |
| `confirmation` | Whether a consequential action is waiting for, has received, or does not require confirmation at this stage. |
| `outcome=queued` | The mock workflow's terminal status. For handoff, `queued` means a synthetic support case was created. |
| `goal_clarification` | Whether the runtime is waiting for the member to choose between plausible goals. |
| `handoff_offer` | Whether a proactive frustration/no-progress handoff offer is waiting for yes/no. It remains `no` for a direct member-requested handoff. |
| `next_goal_offer` | Whether the assistant finished one explicitly requested goal and is waiting for permission to begin the next queued goal. |
| `no_goal_turns` | Consecutive turns that did not produce a supported goal; a successful goal resets it to zero. |

For the sample handoff trace, the sequence is: Luna recognized a direct live-agent
goal, deterministic policy approved the governed handoff skill, the mock live-agent
tool created a synthetic case, the skill reported `queued`, and the complete turn
took about 1.16 seconds. `handoff_offer=no` means this was not a pending proactive
offer—it was already processed as a direct request.

Use server overrides when testing:

```bash
# No traces
member-assistant-server --provider mock --trace off

# Human-readable server traces
member-assistant-server --provider mock --trace console --log-level DEBUG

# Preserve the original machine-readable JSON lines
member-assistant-server --provider mock --trace console --trace-format json

# Export only to local Langfuse
member-assistant-server --provider mock --trace langfuse

# Console and Langfuse together
member-assistant-server --provider mock --trace both
```

`member-assistant-admin trace` prints the effective tracing configuration.
Environment equivalents are documented in `.env.example`; put their values in
`~/.secrets/dev.env` or the project `.env`.

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

Start a traced server, use the member client, and then open the
`Agentic Member Assistant POC` project:

```bash
member-assistant-server --provider mock --trace both
# In another terminal:
member-assistant --session tracing-demo
```

For normal OpenAI testing, either set `TRACE_BACKENDS=console,langfuse` or pass
`--trace both` to the server. Restart the server after changing an environment
file, then run `member-assistant-admin trace`; its `backends` list must contain
both `console` and `langfuse`. Exports
are batched and normally appear shortly after a turn. With
`TRACE_HASH_SESSION_ID=true`, Langfuse displays a value such as
`sha256:3806594b03a90823` rather than the raw CLI `--session` value.

If traces are absent, verify both the server and the configured exporter:

```bash
member-assistant-observability status
member-assistant-observability doctor
member-assistant-admin trace
member-assistant --session tracing-check
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

Keep the server and member CLI running. In a third terminal, verify the active
catalog and publish the demo skill:

```bash
member-assistant-admin skills
member-assistant-admin add-online-id
```

The open member client can use the capability as soon as the catalog poller
observes the new revision:

```text
member> What is my balance?
assistant> Which account would you like ...?
member> I forgot my online ID
assistant> Use the approved online-ID recovery page ... Would you like to resume ...?
member> resume
member> checking
```

Then deactivate it for new requests without stopping the server:

```bash
member-assistant-admin remove-online-id
```

`add-online-id` compiles and publishes
`skills/available/online_id_recovery/SKILL.md` as an immutable artifact, then atomically
updates the active routing index. The catalog notices it without restarting,
and the already-compiled graph routes through its generic execution node. New
tasks use the newly active version; tasks already waiting for clarification,
confirmation, or resume remain pinned to their original version and content
hash.

`remove-online-id` deactivates it for new goals without deleting the immutable
artifact. A paused task that already references that version can still resume.
Every publish, activate, rollback, and deactivate operation appends an actor,
timestamp, version, hash, and catalog revision to the local
`skills/catalog/catalog-events.yaml` audit stream.

## Add a skill

Business authors create one `SKILL.md` with structured YAML frontmatter and a
readable Markdown body. It declares ownership, semantic version, goals, inputs,
behavior dimensions, governance, approved tools, response design, optional
workflow, and acceptance scenarios. Publication stores that same source as
`skills/catalog/<name>/<version>/SKILL.md`; `active.yaml` contains only routing
metadata and active-version pointers.

```bash
member-assistant-skills validate skills/available/online_id_recovery/SKILL.md
member-assistant-skills publish skills/available/online_id_recovery/SKILL.md
member-assistant-skills active
member-assistant-skills versions --name online_id_recovery
member-assistant-skills deactivate online_id_recovery
```

Built-in archetypes are authoring presets, not a closed list of business
capabilities. A custom archetype works without new Python when it compiles to
the allowlisted operations: `collect`, `call_tool`, `select`, `validate`,
`validate_decimal`, `set`, `confirm`, and `respond`. Static response,
tool-backed response, guided selection, and navigation recipes receive a
synthesized workflow. Explicit workflows are reserved for capabilities that
need deterministic sequencing. If a referenced tool or action does not exist,
publication fails; adding that tool adapter is the intended platform-code
extension.

Different content cannot overwrite an existing name/version. Increment the
semantic version, publish it, and use `member-assistant-skills activate` to move
the active pointer forward or back. Consequential calls must remain immediately
after confirmation and still pass deterministic policy at execution time.

The complete contract, call flow, behavior axes, and production control-plane
roadmap are in [Nexus Skill v1 authoring and publication](docs/skill-authoring-and-publication.md).

## Tests

```bash
pytest
```

The suite covers personalized greeting, no-goal escalation offers, goal
disambiguation, natural slot fulfillment, grounded FAQ answers, balance
clarification and restart durability, multi-goal ordering, transfer
review/confirmation/execution, authentication policy, interruption with resume
and discard, confirmed live-agent handoff, runtime skill discovery, custom
archetypes without Python, immutable publication and rollback, metadata-first
loading, exact version pinning across restart, tool-dependency rejection, stable
graph identity, invalid-catalog rollback, direct OpenAI requests, Bedrock
Converse compatibility for Nova/Terra, non-bypassable Guardrail interventions,
semantic event ordering, WebSocket delivery, reconnect replay, TTL cleanup, and
message idempotency.

## Project map

```text
src/member_assistant/
  runtime.py, models.py       one stable graph and explicit conversation/task state
  events.py                   provider/transport-neutral durable event contract
  server.py, server_cli.py    FastAPI REST/WebSocket transport and service entrypoint
  cli.py, admin_cli.py        member socket client and separate system controls
  catalog.py                  metadata-first discovery, lazy artifacts, watcher
  skill_authoring.py          SKILL.md compiler, acceptance gates, publisher
  skill_cli.py                validate, publish, inspect, activate/deactivate
  state_store.py, policy.py   SQLite durability/audit and deterministic controls
  observability.py            console/memory tracing and Langfuse OTLP exporter
  providers/                  shared turn contract, OpenAI, Bedrock, offline adapters
  skills/                     one validated declarative workflow interpreter
  tools/                      typed mock adapters and generic tool registry
skills/catalog/               active.yaml plus immutable versioned SKILL.md artifacts
skills/available/             business-authored candidate SKILL.md files
data/knowledge.json           approved mock FAQ content
tests/                        automated acceptance scenarios
observability/                local Langfuse v4 Docker Compose stack
```

## Intentional POC simplifications

- Keyword routing and catalog-defined extraction rules are the deterministic fallback and test double; they are deliberately transparent rather than a production NLU system.
- The declarative operation set is intentionally small. A novel integration requires a tool adapter; a novel reusable control may require a new platform operation, but never a capability-specific executor.
- The file publisher and polling watcher model a control plane locally; production needs authenticated approval, artifact signing/provenance, durable object storage, event-driven fleet rollout, compatibility gates, and retained versions for in-flight work.
- Every capability uses the same `SKILL.md` contract. The catalog has no legacy JSON loader or capability-specific Python executor.
- SQLite stores one local process's state; production would use encrypted shared storage, retention controls, and LangGraph-compatible distributed checkpoints.
- The socket POC supports durable member event streaming and replay but not yet
  authenticated multi-participant rooms, distributed fan-out, or a real live-agent
  work queue. The live-agent skill still invokes a mock tool.
- Authentication and authorizations are synthetic session flags. URLs, balances, transfer receipts, and handoff cases are mock values only.
- Policy/audit coverage demonstrates control boundaries but does not claim production compliance, fraud controls, or regulated-advice support.
