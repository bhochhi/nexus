# Graph Report - nexus  (2026-09-02)

## Corpus Check
- 92 files · ~83,959 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1156 nodes · 2390 edges · 82 communities (67 shown, 15 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 272 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `918ee0a0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- CatalogValidationError
- AgentRuntime
- SQLiteConversationStore
- Any
- Settings
- runtime_factory
- runtime.py
- Agentic_Chat_Architecture_Deck.md
- msr_ui.py
- Agentic Member Assistant POC
- Agentic Member Assistant POC: Architecture and Design Proposal
- What You Must Do When Invoked
- create_app
- SkillMatch
- Graphify engineer guide
- LiveSupportBroker
- BedrockProvider
- TurnAnalysis
- Agentic Conversational Platform Architecture
- 5. Platform components
- OpenAIProvider
- tools/__init__.py
- SkillRoutingDefinition
- test_bedrock_provider.py
- 4. Architectural principles
- MockAccountTool
- Member-facing skill title
- ValueError
- test_providers.py
- graphify reference: extra exports and benchmark
- DeterministicProvider
- MockHandoffTool
- 14. Implementation roadmap
- FallbackProvider
- Codex build prompt: Agentic Member Assistant POC
- _NaturalTurnProvider
- graphify reference: query, path, explain
- 13. Initial use cases
- test_interruption_and_catalog.py
- Flattened skill schema migration plan
- 11. Live-agent handoff
- ui_launcher.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- 2. Why evolve from Lex-style intent architecture?
- Conversation-first demo runbook
- Live-agent handoff
- _UnknownSkillProvider
- _NoisyBalanceProvider
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- Approved knowledge
- 3. Core language model for stakeholders
- Skill Authoring and Publication
- Internal transfer
- Live-agent handoff
- LocalKnowledgeTool
- test_declarative_skills.py
- AGENTS.md
- extraction-spec.md
- online_id_recovery/SKILL.md
- approved_knowledge/2.0.0/SKILL.md
- guided_balance/2.0.0/SKILL.md
- 2.1.0/SKILL.md
- live_agent_handoff/2.0.0/SKILL.md
- online_id_recovery/3.0.0/SKILL.md
- agentic-member-assistant
- _ContextAwareSemanticProvider
- MockTransferTool
- Guided balance
- Internal transfer
- Live-agent handoff
- Nexus Skill v1: authoring and publication
- 12. Vendor-agnostic deployment view
- Live-agent handoff
- Conversation context and memory policy
- Console tracing reference
- .__init__
- test_live_support.py
- SessionEventHub
- _SemanticInitialGoalProvider

## God Nodes (most connected - your core abstractions)
1. `runtime_factory()` - 90 edges
2. `AgentRuntime` - 81 edges
3. `SkillRoutingDefinition` - 46 edges
4. `SQLiteConversationStore` - 46 edges
5. `DeterministicProvider` - 36 edges
6. `CatalogValidationError` - 32 edges
7. `TurnAnalysis` - 31 edges
8. `SkillMarkdownCompiler` - 31 edges
9. `SkillCatalog` - 30 edges
10. `SkillMatch` - 30 edges

## Surprising Connections (you probably didn't know these)
- `test_catalog_rejects_a_consequential_call_not_immediately_after_confirmation()` --uses--> `SkillDefinition`  [INFERRED]
  tests/test_declarative_skills.py → src/member_assistant/catalog.py
- `runtime_factory()` --uses--> `SkillCatalog`  [INFERRED]
  tests/conftest.py → src/member_assistant/catalog.py
- `test_every_catalog_capability_is_a_versioned_skill_markdown()` --uses--> `SkillCatalog`  [INFERRED]
  tests/test_skill_authoring.py → src/member_assistant/catalog.py
- `test_bedrock_attaches_guardrail_to_converse_request()` --uses--> `BedrockProvider`  [INFERRED]
  tests/test_bedrock_provider.py → src/member_assistant/providers/bedrock_provider.py
- `test_bedrock_error_keeps_safe_aws_metadata_and_redacts_credentials()` --uses--> `BedrockProvider`  [INFERRED]
  tests/test_bedrock_provider.py → src/member_assistant/providers/bedrock_provider.py

## Import Cycles
- None detected.

## Communities (82 total, 15 thin omitted)

### Community 0 - "CatalogValidationError"
Cohesion: 0.05
Nodes (45): _artifact_hash(), CatalogValidationError, Any, Path, Watch routing metadata and lazily load immutable SKILL.md artifacts., Load one exact artifact; routing never requires this full definition., Convenience for diagnostics that explicitly need every full skill., Refresh the active pointer; invalid updates retain the last-known-good set. (+37 more)

### Community 1 - "AgentRuntime"
Cohesion: 0.07
Nodes (22): RLock, ConversationState, Message, PendingClarification, PendingGoalClarification, PendingHandoffOffer, PendingTaskTransition, Provider-neutral and graph-state contracts used across the application. (+14 more)

### Community 2 - "SQLiteConversationStore"
Cohesion: 0.06
Nodes (28): datetime, Row, RuntimeError, AssistantEvent, Any, Provider- and transport-neutral conversation stream events., One durable event produced while processing a member turn. The runtime owns…, __getattr__() (+20 more)

### Community 3 - "Any"
Cohesion: 0.06
Nodes (35): Protocol, _attribute_key(), build_observability(), _compact_value(), _CompositeObservation, _ConsoleObservation, ConsoleTraceSink, _json_text() (+27 more)

### Community 4 - "Settings"
Cohesion: 0.06
Nodes (43): main(), _parser(), Any, ArgumentParser, Local system operations kept separate from the member chat client., _trace_settings(), _color(), main() (+35 more)

### Community 5 - "runtime_factory"
Cohesion: 0.09
Nodes (45): fixture, runtime_factory(), _GapAwareProvider, _QueuedHistoryRecoveryProvider, Recovers initially missed queued-goal inputs from member evidence., test_account_reference_with_type_and_suffix_prefers_the_specific_account(), test_affirmative_answer_to_two_goal_choice_requests_a_specific_choice(), test_ambiguous_goal_reply_can_select_both_requests_in_order() (+37 more)

### Community 6 - "runtime.py"
Cohesion: 0.12
Nodes (19): Validated, file-based skill discovery with last-known-good reloads., SkillDefinition, PolicyDecision, PolicyEngine, Deterministic authorization, tool, and confirmation gates., Stable LangGraph orchestration runtime., ABC, Any (+11 more)

### Community 7 - "Agentic_Chat_Architecture_Deck.md"
Cohesion: 0.05
Nodes (37): Bedrock and guardrails sit behind platform-owned interfaces, Every turn follows the same governable loop, Federated governance: capabilities declare the lane; the platform enforces it, From building every intent to governing reusable capabilities at scale, From Intent-Based Chatbots to Objective-Driven Agentic Conversations, Intent-centric systems are predictable, but conversations are not, Interruptions do not break the conversation; they reprioritize goals, Agentic Chat Architecture Deck (+29 more)

### Community 8 - "msr_ui.py"
Cohesion: 0.08
Nodes (21): _add_message(), conversation(), _process(), Any, fragment, Next-generation Streamlit member chat for the live-support demo., _reset(), console() (+13 more)

### Community 9 - "Agentic Member Assistant POC"
Cohesion: 0.13
Nodes (15): Add a skill, Agentic Member Assistant POC, Conversation behavior, Hot-reload demonstration, How to read server traces and member events, Intentional POC simplifications, Live MSR demo, Local Langfuse (+7 more)

### Community 10 - "Agentic Member Assistant POC: Architecture and Design Proposal"
Cohesion: 0.06
Nodes (31): 10. Safety, privacy, and compliance controls, 11. Observability and quality management, 12. Business operating model, 13. Delivery roadmap, 14. Initial success measures, 15. Decisions to make next, 16. Recommended decision, 1. Executive summary (+23 more)

### Community 11 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 12 - "create_app"
Cohesion: 0.13
Nodes (19): BaseModel, FastAPI, _async_events(), create_app(), FastAPI transport for durable member-assistant conversations., Consume a synchronous runtime stream without blocking the ASGI loop. The…, Build the API around one shared runtime and one compiled LangGraph., SessionRequest (+11 more)

### Community 13 - "SkillMatch"
Cohesion: 0.19
Nodes (12): A discovery-time selection of one single-goal skill., SkillMatch, Amazon Bedrock Runtime Converse adapter. No AWS types escape this module., OpenAI adapter. No OpenAI types escape this module., parse_json_object(), parse_turn_analysis(), Any, Provider-neutral prompt and parser for conversational turn understanding. (+4 more)

### Community 14 - "Graphify engineer guide"
Cohesion: 0.15
Nodes (13): A skill changed but the application behavior did not, A slot was filled from the wrong phrase, Conversation state behaves differently after restart, Explore the HTML graph, Graphify engineer guide, How to choose a command, Keep the graph fresh, Learn the architecture or plan a refactor (+5 more)

### Community 15 - "LiveSupportBroker"
Cohesion: 0.29
Nodes (5): LiveSupportBroker, OnlineAgent, Any, Queueing and participant routing for live member support., Automatically matches waiting cases to the least-active online MSR.

### Community 16 - "BedrockProvider"
Cohesion: 0.18
Nodes (9): ProviderError, ProviderSafetyError, A provider failure with bounded, non-secret troubleshooting metadata., Return safe fields that can be attached to a fallback trace., A provider safety decision that another provider must not bypass., BedrockProvider, Any, Exception (+1 more)

### Community 17 - "TurnAnalysis"
Cohesion: 0.20
Nodes (6): Provider-neutral semantic interpretation of one member turn., A clear member objective that no currently installed skill supports., One model-interpreted active-task input with bounded confidence., SkillGap, SlotUpdate, TurnAnalysis

### Community 18 - "Agentic Conversational Platform Architecture"
Cohesion: 0.14
Nodes (14): 10.1 Response pipeline, 10.2 Response modes, 10. Response composition and guardrails, 15. Acceptance criteria, 16. Reference notes, 1.1 Current POC boundary, 1. Executive summary, 6. Per-turn lifecycle (+6 more)

### Community 19 - "5. Platform components"
Cohesion: 0.14
Nodes (14): 5.10 Response Composer, 5.11 Guardrails + Policy, 5.12 Model Provider Gateway, 5.13 Observability + Audit, 5.1 Session Manager, 5.2 Conversation Orchestrator, 5.3 Conversation Analyzer, 5.4 Task Manager (+6 more)

### Community 20 - "OpenAIProvider"
Cohesion: 0.32
Nodes (4): OpenAIProvider, Any, Exception, Keep useful API diagnostics while redacting credentials and long payloads.

### Community 21 - "tools/__init__.py"
Cohesion: 0.16
Nodes (8): MockTools, Path, Replaceable mock integration adapters., Return the stable dependency manifest exposed to skill publishers., MockMemberProfileTool, Synthetic member-profile adapter used for conversational personalization., MockNavigationTool, Approved navigation-link adapter.

### Community 22 - "SkillRoutingDefinition"
Cohesion: 0.17
Nodes (14): Small catalog record used for routing without loading executable content., SkillRoutingDefinition, ModelProvider, ABC, Any, Stable contract that insulates the runtime and skills from model vendors., All provider-specific behavior is constrained to implementations here., Describe the most recent call without exposing prompt content. (+6 more)

### Community 23 - "test_bedrock_provider.py"
Cohesion: 0.29
Nodes (9): parametrize, _FakeBedrockClient, _response(), test_bedrock_attaches_guardrail_to_converse_request(), test_bedrock_error_keeps_safe_aws_metadata_and_redacts_credentials(), test_bedrock_guardrail_id_and_version_are_an_atomic_configuration(), test_bedrock_nova_and_terra_share_converse_turn_contract(), test_fallback_provider_never_bypasses_a_safety_error() (+1 more)

### Community 24 - "4. Architectural principles"
Cohesion: 0.17
Nodes (12): 4. Architectural principles, Bounded working context, P10. Low-code means no orchestrator changes, not no engineering ever, P1. Conversationally adaptive, operationally governed, P2. Model advises; platform decides and persists, P3. Members own objectives; skills define capabilities; the platform owns goals and tasks, P4. Every turn asks two questions, P5. Skills declare execution mode (+4 more)

### Community 25 - "MockAccountTool"
Cohesion: 0.33
Nodes (4): AccountBalance, MockAccountTool, Any, Mock account data adapter.

### Community 26 - "Member-facing skill title"
Cohesion: 0.33
Nodes (5): Conversation behavior, Inputs and interpretation, Member-facing skill title, Safety and boundaries, When to use

### Community 27 - "ValueError"
Cohesion: 0.25
Nodes (5): Any, Any, NavigationResult, Any, ValueError

### Community 28 - "test_providers.py"
Cohesion: 0.42
Nodes (7): _FakeResponses, _provider(), test_non_reasoning_openai_model_omits_reasoning_parameter(), test_openai_analysis_uses_responses_api_and_returns_skill_gap(), test_openai_error_preserves_safe_api_diagnostics_and_redacts_key(), test_openai_response_generation_uses_responses_output_text(), test_openai_understands_multiple_active_task_slots()

### Community 29 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 30 - "DeterministicProvider"
Cohesion: 0.22
Nodes (7): DeterministicProvider, Any, Recognize a small set of unambiguous safety-critical capability gaps. This…, _CapabilityGapProvider, _NoSlotSemanticProvider, Simulates an LLM declining to bind an ambiguous-looking reply., Simulates a model that incorrectly marks capability help as a skill gap.

### Community 31 - "MockHandoffTool"
Cohesion: 0.36
Nodes (5): HandoffReceipt, HandoffRequest, MockHandoffTool, Any, Mock live-support routing adapter.

### Community 32 - "14. Implementation roadmap"
Cohesion: 0.25
Nodes (8): 14. Implementation roadmap, Slice 1 — Platform skeleton, Slice 2 — Account balance, Slice 3 — FAQ, Slice 4 — Money transfer, Slice 5 — Interruption/resume, Slice 6 — Live agent, Slice 7 — Production hardening

### Community 34 - "Codex build prompt: Agentic Member Assistant POC"
Cohesion: 0.29
Nodes (6): Architecture requirements, Codex build prompt: Agentic Member Assistant POC, Demonstration and tests, Implement these initial skills, Required conversation behavior, Technology and scope

### Community 35 - "_NaturalTurnProvider"
Cohesion: 0.17
Nodes (12): _NaturalTurnProvider, Exercises generic pending-answer and correction controls., Models semantic multi-slot extraction and natural-number normalization., _SemanticBindingProvider, test_low_confidence_account_suffix_is_not_accepted_as_amount(), test_semantic_correction_can_update_and_fill_multiple_slots(), test_semantic_correction_revalidates_and_replaces_confirmation(), test_semantic_slot_correction_restarts_validation_while_collecting_input() (+4 more)

### Community 36 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 37 - "13. Initial use cases"
Cohesion: 0.33
Nodes (6): 13.1 Account balance, 13.2 Money transfer, 13.3 FAQ / knowledge answer, 13.4 Interruption during transfer, 13.5 Live-agent handoff, 13. Initial use cases

### Community 38 - "test_interruption_and_catalog.py"
Cohesion: 0.53
Nodes (5): _install_navigation(), test_hot_discovery_then_interrupt_and_resume(), test_interruption_can_be_discarded(), test_invalid_hot_edit_retains_last_valid_skill(), test_unpublished_skill_file_does_not_change_active_catalog()

### Community 39 - "Flattened skill schema migration plan"
Cohesion: 0.18
Nodes (11): Architectural invariants, Definition of done, Flattened skill schema migration plan, Outcome, Phase 1: author the v3 skill artifacts, Phase 2: compiler, validation, and publication, Phase 3: semantic discovery contract, Phase 4: planning and durable runtime state (+3 more)

### Community 40 - "11. Live-agent handoff"
Cohesion: 0.40
Nodes (5): 11.1 Requirements, 11.2 WebSocket endpoints, 11.3 Event envelope, 11.4 Handoff flow, 11. Live-agent handoff

### Community 41 - "ui_launcher.py"
Cohesion: 0.60
Nodes (4): _launch(), member_main(), msr_main(), Installed entry points for the two Streamlit demo applications.

### Community 42 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 43 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 44 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 45 - "2. Why evolve from Lex-style intent architecture?"
Cohesion: 0.50
Nodes (4): 2.1 Current familiar pattern, 2.2 Where it struggles, 2.3 Proposed pattern, 2. Why evolve from Lex-style intent architecture?

### Community 46 - "Conversation-first demo runbook"
Cohesion: 0.50
Nodes (3): Conversation-first demo runbook, Live MSR setup, Presenter guardrails

### Community 47 - "Live-agent handoff"
Cohesion: 0.29
Nodes (6): Agent-facing context, Conversation behavior, Inputs and interpretation, Live-agent handoff, Safety and boundaries, When to use

### Community 48 - "_UnknownSkillProvider"
Cohesion: 0.50
Nodes (4): Simulates a semantic model returning a skill absent from the catalog., test_installed_skill_match_routes_without_provider_goal_identifier(), test_persisted_duplicate_goal_clarification_recovers_on_yes(), _UnknownSkillProvider

### Community 49 - "_NoisyBalanceProvider"
Cohesion: 0.50
Nodes (3): _NoisyBalanceProvider, Simulates an LLM that speculatively fills account from the intent text., test_speculative_model_slot_uses_neutral_elicitation_then_validates_reply()

### Community 52 - "Approved knowledge"
Cohesion: 0.33
Nodes (5): Approved knowledge, Conversation behavior, Inputs and interpretation, Safety and boundaries, When to use

### Community 53 - "3. Core language model for stakeholders"
Cohesion: 0.50
Nodes (4): 3.1 Avoid confusing language, 3.2 The hierarchy, 3.3 Queued work is not interrupted work, 3. Core language model for stakeholders

### Community 54 - "Skill Authoring and Publication"
Cohesion: 0.67
Nodes (3): Skill Authoring and Publication, Online ID Recovery Skill, Active Catalog Index

### Community 57 - "LocalKnowledgeTool"
Cohesion: 0.27
Nodes (5): KnowledgeResult, LocalKnowledgeTool, Any, Path, Approved local knowledge retrieval adapter.

### Community 68 - "_ContextAwareSemanticProvider"
Cohesion: 0.50
Nodes (3): _ContextAwareSemanticProvider, Uses bounded conversation state to resolve an ordinal reference., test_semantic_provider_can_resolve_slot_from_bounded_conversation_context()

### Community 69 - "MockTransferTool"
Cohesion: 0.29
Nodes (5): MockTransferTool, Any, Idempotent mock internal-transfer adapter., TransferReceipt, TransferRequest

### Community 70 - "Guided balance"
Cohesion: 0.33
Nodes (5): Conversation behavior, Guided balance, Inputs and interpretation, Safety and boundaries, When to use

### Community 72 - "Internal transfer"
Cohesion: 0.33
Nodes (5): Conversation behavior, Inputs and interpretation, Internal transfer, Safety and boundaries, When to use

### Community 74 - "Live-agent handoff"
Cohesion: 0.33
Nodes (5): Conversation behavior, Inputs and interpretation, Live-agent handoff, Safety and boundaries, When to use

### Community 75 - "Nexus Skill v1: authoring and publication"
Cohesion: 0.16
Nodes (7): Archetypes are presets, not a closed capability taxonomy, Commands, Nexus Skill v1: authoring and publication, One authoring file, not four required files, Publication and call flow, What a production platform still needs, LangGraph

### Community 76 - "12. Vendor-agnostic deployment view"
Cohesion: 0.67
Nodes (3): 12.1 Deployment principle, 12.2 Provider abstraction rule, 12. Vendor-agnostic deployment view

### Community 77 - "Live-agent handoff"
Cohesion: 0.29
Nodes (6): Agent-facing context, Conversation behavior, Inputs and interpretation, Live-agent handoff, Safety and boundaries, When to use

### Community 78 - "Conversation context and memory policy"
Cohesion: 0.33
Nodes (6): Context supplied on every semantic turn, Conversation context and memory policy, Evolution beyond the POC, Live-agent handoff summary, Reusing a value from history, Why the full transcript is not sent on every turn

### Community 79 - "Console tracing reference"
Cohesion: 0.17
Nodes (12): Categories and observation names, Common provider and model fields, Console tracing reference, Did a provider fallback occur?, Fields available in JSON and Langfuse, Policy, skill, tool, gap, and turn fields, Reading one line, Understanding fields (`LLM llm.turn_understanding`) (+4 more)

### Community 80 - ".__init__"
Cohesion: 0.50
Nodes (3): HandoffEnded, Publish, SentimentAnalyzer

### Community 84 - "test_live_support.py"
Cohesion: 0.50
Nodes (6): _GroundedHandoffSummaryProvider, _member_turn(), _queue_banking_handoff(), _receive_until(), test_live_support_assigns_routes_messages_updates_sentiment_and_ends(), test_waiting_member_can_cancel_and_return_to_virtual_assistant()

### Community 86 - "SessionEventHub"
Cohesion: 0.29
Nodes (3): Any, In-process fan-out for every socket watching the same session. Durable SQLite…, SessionEventHub

### Community 88 - "_SemanticInitialGoalProvider"
Cohesion: 0.67
Nodes (3): Returns semantic goal inputs that conflict with shape-based extraction., _SemanticInitialGoalProvider, test_semantic_goal_inputs_override_shape_based_fallback_extraction()

## Knowledge Gaps
- **245 isolated node(s):** `agentic-member-assistant`, `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)`, `Step 1 - Ensure graphify is installed` (+240 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 463 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `runtime_factory()` connect `runtime_factory` to `CatalogValidationError`, `AgentRuntime`, `SQLiteConversationStore`, `Any`, `_NaturalTurnProvider`, `_ContextAwareSemanticProvider`, `runtime.py`, `test_interruption_and_catalog.py`, `create_app`, `_UnknownSkillProvider`, `_NoisyBalanceProvider`, `test_live_support.py`, `test_bedrock_provider.py`, `_SemanticInitialGoalProvider`, `test_declarative_skills.py`, `test_providers.py`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `AgentRuntime` connect `AgentRuntime` to `CatalogValidationError`, `SQLiteConversationStore`, `Any`, `Settings`, `runtime_factory`, `runtime.py`, `create_app`, `SkillRoutingDefinition`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `SQLiteConversationStore` connect `SQLiteConversationStore` to `AgentRuntime`, `Settings`, `runtime_factory`, `runtime.py`, `LiveSupportBroker`, `.__init__`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `runtime_factory()` (e.g. with `SkillCatalog` and `AgentRuntime`) actually correct?**
  _`runtime_factory()` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `AgentRuntime` (e.g. with `__getattr__()` and `SkillCatalog`) actually correct?**
  _`AgentRuntime` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `SkillRoutingDefinition` (e.g. with `ModelProvider` and `BedrockProvider`) actually correct?**
  _`SkillRoutingDefinition` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `SQLiteConversationStore` (e.g. with `LiveSupportBroker` and `AgentRuntime`) actually correct?**
  _`SQLiteConversationStore` has 9 INFERRED edges - model-reasoned connections that need verification._