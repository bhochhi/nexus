# Graph Report - nexus-graphify  (2026-08-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 740 nodes · 1911 edges · 29 communities (27 shown, 2 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 225 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2caabf2a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28

## God Nodes (most connected - your core abstractions)
1. `AgentRuntime` - 80 edges
2. `runtime_factory()` - 67 edges
3. `SQLiteConversationStore` - 46 edges
4. `SkillRoutingDefinition` - 45 edges
5. `SkillCatalog` - 30 edges
6. `DeterministicProvider` - 29 edges
7. `CatalogValidationError` - 29 edges
8. `Settings` - 28 edges
9. `BedrockProvider` - 27 edges
10. `SkillMarkdownCompiler` - 26 edges

## Surprising Connections (you probably didn't know these)
- `test_every_catalog_capability_is_a_versioned_skill_markdown()` --uses--> `SkillCatalog`  [INFERRED]
  tests/test_skill_authoring.py → src/member_assistant/catalog.py
- `test_bedrock_attaches_guardrail_to_converse_request()` --uses--> `BedrockProvider`  [INFERRED]
  tests/test_bedrock_provider.py → src/member_assistant/providers/bedrock_provider.py
- `test_bedrock_error_keeps_safe_aws_metadata_and_redacts_credentials()` --uses--> `BedrockProvider`  [INFERRED]
  tests/test_bedrock_provider.py → src/member_assistant/providers/bedrock_provider.py
- `test_bedrock_guardrail_id_and_version_are_an_atomic_configuration()` --uses--> `BedrockProvider`  [INFERRED]
  tests/test_bedrock_provider.py → src/member_assistant/providers/bedrock_provider.py
- `test_bedrock_nova_and_terra_share_converse_turn_contract()` --uses--> `BedrockProvider`  [INFERRED]
  tests/test_bedrock_provider.py → src/member_assistant/providers/bedrock_provider.py

## Import Cycles
- None detected.

## Communities (29 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (49): Validated, file-based skill discovery with last-known-good reloads., Small catalog record used for routing without loading executable content., SkillRoutingDefinition, GoalMatch, ModelProvider, ProviderError, ProviderSafetyError, ABC (+41 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (22): RLock, ConversationState, Message, PendingClarification, PendingGoalClarification, PendingHandoffOffer, PendingTaskTransition, Provider-neutral and graph-state contracts used across the application. (+14 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (28): datetime, Row, RuntimeError, AssistantEvent, Any, Provider- and transport-neutral conversation stream events., One durable event produced while processing a member turn. The runtime owns…, __getattr__() (+20 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (35): Protocol, _attribute_key(), build_observability(), _compact_value(), _CompositeObservation, _ConsoleObservation, ConsoleTraceSink, _json_text() (+27 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (29): AccountBalance, MockAccountTool, Any, Mock account data adapter., HandoffReceipt, HandoffRequest, MockHandoffTool, Any (+21 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (38): _color(), main(), _model_line(), _parser(), Any, ArgumentParser, Member-only WebSocket chat client., _render_event() (+30 more)

### Community 6 - "Community 6"
Cohesion: 0.17
Nodes (13): ABC, Any, Common contracts for skill implementations., SkillContext, SkillExecutor, SkillResult, DeclarativeSkillExecutor, Any (+5 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (34): fixture, runtime_factory(), _DisplayNameGoalProvider, _GapAwareProvider, Simulates a semantic model returning a friendly label as the goal ID., test_ambiguous_goals_are_clarified_and_answer_is_durable(), test_balance_account_number_follow_up_continues_last_read_only_skill(), test_balance_clarification_and_durable_resume_after_restart() (+26 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (18): _add_message(), conversation(), _process(), Any, fragment, Next-generation Streamlit member chat for the live-support demo., _reset(), console() (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.16
Nodes (11): HandoffEnded, Publish, SentimentAnalyzer, LiveSupportBroker, OnlineAgent, Any, Queueing and participant routing for live member support., Automatically matches waiting cases to the least-active online MSR. (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (8): Path, Watch routing metadata and lazily load immutable SKILL.md artifacts., Load one exact artifact; routing never requires this full definition., Convenience for diagnostics that explicitly need every full skill., Refresh the active pointer; invalid updates retain the last-known-good set., Validate and publish one SKILL.md without changing the platform., Deactivate new routing without deleting versions used by durable tasks., SkillCatalog

### Community 11 - "Community 11"
Cohesion: 0.17
Nodes (13): BaseModel, FastAPI, _async_events(), create_app(), FastAPI transport for durable member-assistant conversations., Consume a synchronous runtime stream without blocking the ASGI loop. The…, Build the API around one shared runtime and one compiled LangGraph., SessionRequest (+5 more)

### Community 12 - "Community 12"
Cohesion: 0.21
Nodes (7): _artifact_hash(), Any, SkillDefinition, PolicyDecision, PolicyEngine, Deterministic authorization, tool, and confirmation gates., test_catalog_rejects_a_consequential_call_not_immediately_after_confirmation()

### Community 13 - "Community 13"
Cohesion: 0.30
Nodes (4): FileSkillPublisher, PublicationReceipt, Publish immutable SKILL.md artifacts and atomically move active pointers., Stop routing new work while retaining every immutable version.

### Community 14 - "Community 14"
Cohesion: 0.46
Nodes (6): CatalogValidationError, Any, Path, Parse structured frontmatter and optional YAML sections from SKILL.md., SkillMarkdownCompiler, test_publication_rejects_a_missing_tool_dependency()

### Community 15 - "Community 15"
Cohesion: 0.29
Nodes (9): parametrize, _FakeBedrockClient, _response(), test_bedrock_attaches_guardrail_to_converse_request(), test_bedrock_error_keeps_safe_aws_metadata_and_redacts_credentials(), test_bedrock_guardrail_id_and_version_are_an_atomic_configuration(), test_bedrock_nova_and_terra_share_converse_turn_contract(), test_fallback_provider_never_bypasses_a_safety_error() (+1 more)

### Community 16 - "Community 16"
Cohesion: 0.27
Nodes (5): CompiledSkill, DeactivationReceipt, Compile one business-facing SKILL.md into an immutable runtime artifact., Apply acceptance and platform-dependency gates before publication., SkillPublicationValidator

### Community 17 - "Community 17"
Cohesion: 0.42
Nodes (7): _FakeResponses, _provider(), test_non_reasoning_openai_model_omits_reasoning_parameter(), test_openai_analysis_uses_responses_api_and_returns_skill_gap(), test_openai_error_preserves_safe_api_diagnostics_and_redacts_key(), test_openai_response_generation_uses_responses_output_text(), test_openai_understands_multiple_active_task_slots()

### Community 18 - "Community 18"
Cohesion: 0.28
Nodes (8): _guided_source(), Path, test_catalog_loads_routing_metadata_before_full_artifact(), test_deactivation_stops_new_routing_but_preserves_inflight_version(), test_every_catalog_capability_is_a_versioned_skill_markdown(), test_one_skill_markdown_can_add_a_custom_archetype_without_python(), test_paused_task_resumes_with_pinned_version_after_publish_and_restart(), test_publication_is_immutable_idempotent_and_rollbackable()

### Community 19 - "Community 19"
Cohesion: 0.38
Nodes (6): main(), _parser(), Any, ArgumentParser, Local system operations kept separate from the member chat client., _trace_settings()

### Community 20 - "Community 20"
Cohesion: 0.29
Nodes (3): Any, In-process fan-out for every socket watching the same session. Durable SQLite…, SessionEventHub

### Community 21 - "Community 21"
Cohesion: 0.38
Nodes (6): main(), _parser(), Any, ArgumentParser, Authoring and publication commands for the file-backed skill registry., _receipt()

### Community 22 - "Community 22"
Cohesion: 0.29
Nodes (7): _NaturalTurnProvider, Models semantic multi-slot extraction and natural-number normalization., test_low_confidence_account_suffix_is_not_accepted_as_amount(), test_semantic_correction_revalidates_and_replaces_confirmation(), test_semantic_turn_understanding_collects_multiple_slots_and_word_amount(), test_semantic_turn_understanding_normalizes_disfluent_word_amount(), test_semantic_understanding_continues_an_inflight_deactivated_version()

### Community 23 - "Community 23"
Cohesion: 0.53
Nodes (5): _install_navigation(), test_hot_discovery_then_interrupt_and_resume(), test_interruption_can_be_discarded(), test_invalid_hot_edit_retains_last_valid_skill(), test_unpublished_skill_file_does_not_change_active_catalog()

### Community 24 - "Community 24"
Cohesion: 0.73
Nodes (5): _member_turn(), _queue_banking_handoff(), _receive_until(), test_live_support_assigns_routes_messages_updates_sentiment_and_ends(), test_waiting_member_can_cancel_and_return_to_virtual_assistant()

### Community 25 - "Community 25"
Cohesion: 0.60
Nodes (4): _launch(), member_main(), msr_main(), Installed entry points for the two Streamlit demo applications.

### Community 26 - "Community 26"
Cohesion: 0.50
Nodes (3): _NoisyBalanceProvider, Simulates an LLM that speculatively fills account from the intent text., test_speculative_model_slot_uses_neutral_elicitation_then_validates_reply()

## Knowledge Gaps
- **1 isolated node(s):** `agentic-member-assistant`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 174 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentRuntime` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 7`, `Community 10`, `Community 11`, `Community 12`?**
  _High betweenness centrality (0.186) - this node is a cross-community bridge._
- **Why does `SQLiteConversationStore` connect `Community 2` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 7`, `Community 9`, `Community 19`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Why does `runtime_factory()` connect `Community 7` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 10`, `Community 11`, `Community 12`, `Community 15`, `Community 17`, `Community 18`, `Community 22`, `Community 23`, `Community 24`, `Community 26`, `Community 27`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `AgentRuntime` (e.g. with `__getattr__()` and `SkillCatalog`) actually correct?**
  _`AgentRuntime` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 65 inferred relationships involving `runtime_factory()` (e.g. with `SkillCatalog` and `AgentRuntime`) actually correct?**
  _`runtime_factory()` has 65 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `SQLiteConversationStore` (e.g. with `LiveSupportBroker` and `AgentRuntime`) actually correct?**
  _`SQLiteConversationStore` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `SkillRoutingDefinition` (e.g. with `ModelProvider` and `BedrockProvider`) actually correct?**
  _`SkillRoutingDefinition` has 9 INFERRED edges - model-reasoned connections that need verification._