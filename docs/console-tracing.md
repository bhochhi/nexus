# Console tracing reference

The member-assistant server emits one trace for each member turn. Nested
observations show how the platform understood the turn, applied policy, executed
a skill, called tools, changed durable state, and produced the response. This
reference describes the human-readable `pretty` console format. Use JSON format
when you need every recorded field rather than the curated troubleshooting view.

## Reading one line

A pretty trace line has this shape:

```text
✓ LLM    llm.turn_understanding  provider=openai | model=gpt-5.6-luna | goals=internal_transfer@0.96 | 842ms
```

| Part | Meaning |
| --- | --- |
| `✓` | The observation completed without raising an error. |
| `x` | The observation raised an error. Look for `failure_type`, provider error fields, or the JSON event's `error_type`. |
| `LLM` | Troubleshooting category derived from the observation name. It is not the logger severity. |
| `llm.turn_understanding` | Stable observation name. Use this name when filtering JSON or Langfuse. |
| `key=value` | Curated metadata or output fields. Fields that are absent or empty are omitted. |
| `842ms` | Wall-clock duration of this observation, including nested work it performed. |

Observations print when they finish, not when they start. A child tool or workflow
line can therefore appear before its enclosing `SKILL` line, and the root `TURN`
line normally appears last. Not every turn uses every observation.

`INFO`, `DEBUG`, `WARNING`, and `ERROR` are logging severities. They are separate
from the colored `LLM`, `POLICY`, `SKILL`, `TOOL`, `GAP`, `TURN`, and `TRACE`
categories. Uvicorn and third-party libraries can also emit ordinary `INFO`
lines; for example, `HTTP Request ... 200 OK` confirms a provider HTTP request
and is not a member-assistant trace observation.

## Categories and observation names

| Category | Observation names | What it means | Default visibility |
| --- | --- | --- | --- |
| `TURN` | `member-assistant.turn` | Root summary for one accepted member message and its final assistant reply. It encloses the other observations. | `INFO` |
| `LLM` | `llm.turn_understanding` | The provider interpreted goals, conversation semantics, active-task slot updates, corrections, sentiment, or a skill gap. It does not validate or execute a financial action. | `INFO` |
| `LLM` | `llm.live_sentiment` | A standalone live-sentiment analysis request. | `INFO` |
| `LLM` | `llm.grounded_response` | A model composed wording from skill-controlled instructions and facts. It is not open-ended tool execution. | `INFO` |
| `POLICY` | `policy.evaluate` | Deterministic authentication, authorization, dependency, risk, and confirmation controls evaluated a selected skill. | `INFO` |
| `SKILL` | `skill.<skill-name>` | One pass through the selected declarative skill. It can finish, request input, request confirmation, or fail safely. | `INFO` |
| `TOOL` | `tool.<tool>.<action>` | A typed tool action ran. Tools in this POC are mock or local. | `INFO` |
| `GAP` | `skill_gap.detected` | The model found a clear member objective but no active catalog skill supported it with sufficient confidence. | `INFO` |
| `TRACE` | `workflow.<operation>` | One declarative workflow operation such as `collect`, `select`, `validate`, `confirm`, `call_tool`, or `respond`. | `DEBUG`, or any error |
| `TRACE` | `graph.<node>` | One orchestration-graph node, such as understanding, planning, policy, execution, advancement, or finalization. | `DEBUG`, or any error |
| `TRACE` | `state.load`, `state.persist` | Durable conversation state was loaded or saved. | `DEBUG`, or any error |
| `TRACE` | `response.controlled_reception`, `response.template`, `response.grounded_template` | Controlled platform or skill copy was rendered without an unconstrained model response. | `DEBUG`, or any error |

At the default `INFO` setting, pretty output includes the root turn and the LLM,
policy, skill, tool, and skill-gap families. Set `TRACE_LOG_LEVEL=DEBUG` or pass
`--log-level DEBUG` to include the lower-level `TRACE` families. An observation
that fails is printed even when its family would otherwise be hidden.

## Common provider and model fields

| Pretty field | Source field | Meaning |
| --- | --- | --- |
| `requested` | `configured_provider` | Provider requested by configuration when a different fallback provider handled the operation. |
| `provider` | `provider` | Provider that actually handled the operation, such as `openai`, `bedrock`, or `deterministic`. |
| `model` | `model` | Exact model or deterministic-router identifier. |
| `endpoint` | `api_endpoint` | Provider API surface, such as OpenAI `responses` or Bedrock `converse`. |
| `reasoning` | `reasoning_effort` | Configured reasoning effort. It is not hidden reasoning text; chain-of-thought is never traced. |
| `region` | `aws_region` | AWS Region used for a Bedrock request. |
| `guardrail` | `guardrail_enabled` | Whether a configured Bedrock Guardrail was attached. |
| `guardrail_intervened` | `guardrail_intervened` | Whether the provider guardrail blocked input or output. A safety intervention is not bypassed with deterministic fallback. |
| `stop_reason` | `stop_reason` | Provider reason for ending generation, for example `end_turn`, `max_tokens`, `content_filtered`, or `guardrail_intervened`. |
| `request_id` | `provider_request_id` | Provider request identifier used to correlate an API-side issue. |
| `provider_ms` | `provider_latency_ms` | Latency reported by the provider, distinct from the observation's total duration. |
| `fallback` | `fallback_used` | `yes` when the deterministic availability provider handled the operation; `no` when the configured provider succeeded. |
| `reason` | `fallback_reason` | Why fallback was selected, such as `missing_api_key` or a bounded provider error code. |
| `failure_type` | `failure_type` | Safe exception class associated with a provider failure. |
| `http_status` | `provider_status` | Provider HTTP status when available. |
| `error_code` | `provider_error_code` | Safe provider error code. |
| `error_param` | `provider_error_param` | Request parameter identified by the provider as invalid. |
| `in_tokens` | `input_tokens` | Provider-reported input-token count for this operation. |
| `out_tokens` | `output_tokens` | Provider-reported output-token count for this operation. |

Provider fields describe the most recent model operation attached to that
observation. They do not prove that every nested operation used a model.

## Understanding fields (`LLM llm.turn_understanding`)

| Pretty field | Meaning |
| --- | --- |
| `goals=skill@confidence,...` | Up to five catalog skill candidates and their semantic confidence. When accepted candidates exist, those are shown; otherwise all candidates are shown. Confidence is routing evidence, not authorization. |
| `act` | Conversation act, such as `new_goal`, `provide_information`, `correction`, `confirmation`, `capability_question`, or `small_talk`. |
| `relation` | Relationship to the active goal, such as continuing, correcting, replacing, interrupting, or unrelated. |
| `slots` | Names of schema-declared active-task inputs understood from this utterance. Compact pretty output never shows their values. |
| `invalid_slots` | Number of low-confidence or schema-invalid slot updates rejected before task state changed. It appears only when nonzero. |
| `invalid_skills` | Number of provider-returned skill names rejected because they were not in the supplied discovery catalog. It appears only when nonzero. |
| `goal_aliases` | Number of friendly provider labels normalized to catalog identifiers, when an adapter reports that compatibility count. |
| `invalid_goals` | Legacy compatibility field for older adapters that still report rejected goal identifiers. New single-goal skill routing reports `invalid_skills`. |

The understanding observation performs semantic interpretation only. Catalog
validation, deterministic policy, skill validation, and tools remain separate
observations so a confident model match cannot directly authorize execution.

## Policy, skill, tool, gap, and turn fields

| Field | Seen on | Meaning |
| --- | --- | --- |
| `skill` | `POLICY`, `SKILL`, `TOOL`, `TURN` | Stable catalog skill name selected for that stage. |
| `version` | `POLICY`, `SKILL` | Immutable semantic version of the selected skill definition. |
| `artifact` | `POLICY`, `SKILL` | First 12 characters of the skill content hash in pretty output. JSON and Langfuse retain the full hash. |
| `risk_tier` | `POLICY`, `SKILL` | Governance tier: `informational`, `navigation`, `read_only`, `consequential`, or `handoff`. It is not model confidence. |
| `decision` | `POLICY` | Deterministic policy event, such as `policy_approved`, `confirmation_required`, `confirmation_denied`, or another denial reason. |
| `policy_result` | `POLICY` | Compatibility field used by policy integrations that provide a separate result label. |
| `outcome` | `TURN` | Current skill outcome status, such as `completed`, `queued`, `failed`, or a controlled provider-safety result. |
| `confirmation` | `POLICY`, `TURN` | Confirmation state, such as `not_required`, `required`, `confirmed`, or `denied`. |
| `goal_clarification` | `TURN` | Whether the runtime is waiting for the member to choose between plausible goals. |
| `handoff_offer` | `TURN` | Whether a proactive live-agent offer is waiting for a yes/no answer. |
| `next_goal_offer` | `TURN` | Whether a task-transition decision is pending. Queued goals normally advance automatically; this flag is primarily relevant to a paused or explicitly gated transition. |
| `no_goal_turns` | `TURN` | Consecutive turns that produced neither a supported goal nor progress on the active task. |
| `gap_category` | `GAP` | Stable aggregation category for the unsupported objective. |
| `gap_objective` | `GAP` | Sanitized plain-language objective understood by the provider. |
| `gap_confidence` | `GAP` | Confidence that the member expressed this unsupported objective. |

Tool action names are carried in the stable observation name—for example,
`tool.mock_accounts.list_eligible_balances`. The pretty view intentionally keeps
tool arguments, returned balances, account identifiers, and slot values out of
the compact line. Use JSON or Langfuse for the full structured observation,
subject to the content-capture setting.

## Fields available in JSON and Langfuse

Pretty output is an allowlisted summary. It does not print every recorded field.
Use either of these when troubleshooting requires the full hierarchy:

```bash
member-assistant-server --trace console --trace-format json --log-level DEBUG
member-assistant-server --trace langfuse
```

Structured observations include:

- `trace_id`, `span_id`, and `parent_span_id` for correlation;
- `name`, observation `type`, `status`, and `duration_ms`;
- root trace metadata such as the hashed session ID, environment, turn ID, and
  catalog revision;
- observation `metadata`, `input`, and `output` objects;
- workflow fields such as operation, step index, next step, and result status;
- graph fields such as node, next action, goal count, active skill, and task
  status;
- tool argument/result summaries—or their captured values when explicitly
  enabled; and
- state and response summaries.

`TRACE_INCLUDE_CONTENT=false` is the safe default. It replaces member messages,
assistant replies, model prompts, tool arguments, tool results, and financial
values with shape or length summaries. `TRACE_INCLUDE_CONTENT=true` (or
`--trace-content`) records those values in every configured trace backend,
including the console JSON stream and Langfuse. Existing redacted traces cannot
be reconstructed after capture is enabled.

Session IDs remain hashed independently when `TRACE_HASH_SESSION_ID=true`.
Captured content can still contain member or financial data, so enable it only
in an appropriately controlled debugging environment and turn it off afterward.

## Useful troubleshooting patterns

### Why was a skill selected?

Find `llm.turn_understanding`, compare `goals`, `act`, `relation`, and `slots`,
then follow the selected skill into `policy.evaluate`. A high-confidence match
with a policy denial means routing worked and governance stopped execution.

### Why did the assistant ask another question?

Run at `DEBUG` and inspect the `workflow.collect` or `workflow.select` observation
inside `skill.<name>`. Then inspect the `TURN` flags to distinguish missing task
input from goal clarification, handoff confirmation, or task transition.

### Did a provider fallback occur?

On the relevant `LLM` line, look for `fallback=yes`, `requested=<provider>`, and
`reason=<cause>`. The `provider` field tells you which adapter actually produced
the result.

### Was an action executed?

Follow `POLICY policy.evaluate` to `SKILL skill.<name>` and then to the applicable
`TOOL` observation. A skill asking for input or confirmation is not evidence that
the consequential tool ran. Use the tool observation and final `TURN outcome` as
the execution evidence.
