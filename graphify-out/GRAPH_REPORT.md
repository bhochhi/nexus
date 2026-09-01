# Graph Report - nexus  (2026-08-31)

## Corpus Check
- 82 files · ~68,718 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1034 nodes · 2208 edges · 68 communities (53 shown, 15 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 244 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6262d24b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- SkillCatalog
- AgentRuntime
- SQLiteConversationStore
- Any
- Settings
- runtime_factory
- catalog.py
- Agentic_Chat_Architecture_Deck.md
- msr_ui.py
- Agentic Member Assistant POC
- Agentic Member Assistant POC: Architecture and Design Proposal
- What You Must Do When Invoked
- create_app
- ValueError
- ProviderError
- LiveSupportBroker
- BedrockProvider
- GoalMatch
- Agentic Conversational Platform Architecture
- 5. Platform components
- OpenAIProvider
- DeterministicProvider
- ModelProvider
- test_bedrock_provider.py
- 4. Architectural principles
- MockAccountTool
- LocalKnowledgeTool
- MockTransferTool
- test_providers.py
- graphify reference: extra exports and benchmark
- runtime.py
- MockHandoffTool
- 14. Implementation roadmap
- FallbackProvider
- Codex build prompt: Agentic Member Assistant POC
- _NaturalTurnProvider
- graphify reference: query, path, explain
- 13. Initial use cases
- test_interruption_and_catalog.py
- test_live_support.py
- 11. Live-agent handoff
- ui_launcher.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- 2. Why evolve from Lex-style intent architecture?
- Conversation-first demo runbook
- .__init__
- _DisplayNameGoalProvider
- _NoisyBalanceProvider
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- 10. Response composition and guardrails
- 3. Core language model for stakeholders
- Skill Authoring and Publication
- Internal transfer
- Live-agent handoff
- test_declarative_skills.py
- _CapabilityGapProvider
- AGENTS.md
- extraction-spec.md
- online_id_recovery/SKILL.md
- approved_knowledge/2.0.0/SKILL.md
- guided_balance/2.0.0/SKILL.md
- 2.1.0/SKILL.md
- live_agent_handoff/2.0.0/SKILL.md
- online_id_recovery/3.0.0/SKILL.md
- agentic-member-assistant

## God Nodes (most connected - your core abstractions)
1. `AgentRuntime` - 80 edges
2. `runtime_factory()` - 80 edges
3. `SQLiteConversationStore` - 46 edges
4. `SkillRoutingDefinition` - 45 edges
5. `SkillCatalog` - 30 edges
6. `DeterministicProvider` - 30 edges
7. `CatalogValidationError` - 29 edges
8. `Settings` - 28 edges
9. `BedrockProvider` - 27 edges
10. `SkillMarkdownCompiler` - 26 edges

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

## Communities (68 total, 15 thin omitted)

### Community 0 - "SkillCatalog"
Cohesion: 0.05
Nodes (47): main(), _parser(), Any, ArgumentParser, Local system operations kept separate from the member chat client., _trace_settings(), _artifact_hash(), CatalogValidationError (+39 more)

### Community 1 - "AgentRuntime"
Cohesion: 0.07
Nodes (25): RLock, Small catalog record used for routing without loading executable content., SkillRoutingDefinition, ConversationState, Message, PendingClarification, PendingGoalClarification, PendingHandoffOffer (+17 more)

### Community 2 - "SQLiteConversationStore"
Cohesion: 0.07
Nodes (20): datetime, Row, RuntimeError, AssistantEvent, Any, One durable event produced while processing a member turn. The runtime owns…, new_conversation_state(), Any (+12 more)

### Community 3 - "Any"
Cohesion: 0.06
Nodes (35): Protocol, _attribute_key(), build_observability(), _compact_value(), _CompositeObservation, _ConsoleObservation, ConsoleTraceSink, _json_text() (+27 more)

### Community 4 - "Settings"
Cohesion: 0.07
Nodes (37): _color(), main(), _model_line(), _parser(), Any, ArgumentParser, Member-only WebSocket chat client., _render_event() (+29 more)

### Community 5 - "runtime_factory"
Cohesion: 0.10
Nodes (40): fixture, runtime_factory(), _GapAwareProvider, test_account_reference_with_type_and_suffix_prefers_the_specific_account(), test_affirmative_answer_to_two_goal_choice_requests_a_specific_choice(), test_ambiguous_goal_reply_can_select_both_requests_in_order(), test_ambiguous_goal_reply_can_state_an_ordered_plan(), test_ambiguous_goals_are_clarified_and_answer_is_durable() (+32 more)

### Community 6 - "catalog.py"
Cohesion: 0.12
Nodes (18): Validated, file-based skill discovery with last-known-good reloads., SkillDefinition, PolicyDecision, PolicyEngine, Deterministic authorization, tool, and confirmation gates., ABC, Any, Common contracts for skill implementations. (+10 more)

### Community 7 - "Agentic_Chat_Architecture_Deck.md"
Cohesion: 0.05
Nodes (37): Bedrock and guardrails sit behind platform-owned interfaces, Every turn follows the same governable loop, Federated governance: capabilities declare the lane; the platform enforces it, From building every intent to governing reusable capabilities at scale, From Intent-Based Chatbots to Objective-Driven Agentic Conversations, Intent-centric systems are predictable, but conversations are not, Interruptions do not break the conversation; they reprioritize goals, Agentic Chat Architecture Deck (+29 more)

### Community 8 - "msr_ui.py"
Cohesion: 0.08
Nodes (21): _add_message(), conversation(), _process(), Any, fragment, Next-generation Streamlit member chat for the live-support demo., _reset(), console() (+13 more)

### Community 9 - "Agentic Member Assistant POC"
Cohesion: 0.06
Nodes (32): Add semantic extraction with Gemini, Browser fallback: serve the files locally, Generate the files when they are absent, Graphify architecture demo, Install, Query the graph, Refresh after code changes, Suggested team walkthrough (+24 more)

### Community 10 - "Agentic Member Assistant POC: Architecture and Design Proposal"
Cohesion: 0.06
Nodes (31): 10. Safety, privacy, and compliance controls, 11. Observability and quality management, 12. Business operating model, 13. Delivery roadmap, 14. Initial success measures, 15. Decisions to make next, 16. Recommended decision, 1. Executive summary (+23 more)

### Community 11 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 12 - "create_app"
Cohesion: 0.11
Nodes (18): BaseModel, FastAPI, _async_events(), create_app(), Any, FastAPI transport for durable member-assistant conversations., In-process fan-out for every socket watching the same session. Durable SQLite…, Consume a synchronous runtime stream without blocking the ASGI loop. The… (+10 more)

### Community 13 - "ValueError"
Cohesion: 0.12
Nodes (12): MockTools, Any, Replaceable mock integration adapters., Return the stable dependency manifest exposed to skill publishers., MockMemberProfileTool, Any, Synthetic member-profile adapter used for conversational personalization., MockNavigationTool (+4 more)

### Community 14 - "ProviderError"
Cohesion: 0.27
Nodes (7): ProviderError, ProviderSafetyError, A provider failure with bounded, non-secret troubleshooting metadata., A provider safety decision that another provider must not bypass., build_provider(), Provider construction and safe fallback behavior., Model-provider adapters.

### Community 15 - "LiveSupportBroker"
Cohesion: 0.29
Nodes (5): LiveSupportBroker, OnlineAgent, Any, Queueing and participant routing for live member support., Automatically matches waiting cases to the least-active online MSR.

### Community 16 - "BedrockProvider"
Cohesion: 0.30
Nodes (4): BedrockProvider, Any, Exception, Use Bedrock Converse for both Amazon Nova and Bedrock-hosted OpenAI models.

### Community 17 - "GoalMatch"
Cohesion: 0.17
Nodes (16): GoalMatch, Stable contract that insulates the runtime and skills from model vendors., Provider-neutral semantic interpretation of one member turn., A clear member objective that no currently installed skill supports., SkillGap, TurnAnalysis, Amazon Bedrock Runtime Converse adapter. No AWS types escape this module., OpenAI adapter. No OpenAI types escape this module. (+8 more)

### Community 18 - "Agentic Conversational Platform Architecture"
Cohesion: 0.13
Nodes (14): 12.1 Deployment principle, 12.2 Provider abstraction rule, 12. Vendor-agnostic deployment view, 15. Acceptance criteria, 16. Reference notes, 1.1 Current POC boundary, 1. Executive summary, 6. Per-turn lifecycle (+6 more)

### Community 19 - "5. Platform components"
Cohesion: 0.14
Nodes (14): 5.10 Response Composer, 5.11 Guardrails + Policy, 5.12 Model Provider Gateway, 5.13 Observability + Audit, 5.1 Session Manager, 5.2 Conversation Orchestrator, 5.3 Conversation Analyzer, 5.4 Job Manager (+6 more)

### Community 20 - "OpenAIProvider"
Cohesion: 0.32
Nodes (4): OpenAIProvider, Any, Exception, Keep useful API diagnostics while redacting credentials and long payloads.

### Community 21 - "DeterministicProvider"
Cohesion: 0.25
Nodes (6): One model-interpreted active-task input with bounded confidence., SlotUpdate, DeterministicProvider, Any, Offline provider used by tests and as a safe availability fallback., Recognize a small set of unambiguous safety-critical capability gaps. This…

### Community 22 - "ModelProvider"
Cohesion: 0.17
Nodes (7): ModelProvider, ABC, Any, All provider-specific behavior is constrained to implementations here., Describe the most recent call without exposing prompt content., Understand objectives, task-relative inputs, and optional gaps. Offline…, Return safe fields that can be attached to a fallback trace.

### Community 23 - "test_bedrock_provider.py"
Cohesion: 0.29
Nodes (9): parametrize, _FakeBedrockClient, _response(), test_bedrock_attaches_guardrail_to_converse_request(), test_bedrock_error_keeps_safe_aws_metadata_and_redacts_credentials(), test_bedrock_guardrail_id_and_version_are_an_atomic_configuration(), test_bedrock_nova_and_terra_share_converse_turn_contract(), test_fallback_provider_never_bypasses_a_safety_error() (+1 more)

### Community 24 - "4. Architectural principles"
Cohesion: 0.18
Nodes (11): 4. Architectural principles, P10. Low-code means no orchestrator changes, not no engineering ever, P1. Conversationally adaptive, operationally governed, P2. Model advises; platform decides and persists, P3. Members own objectives; platform owns jobs; jobs own execution plans, P4. Every turn asks two questions, P5. Skills declare execution mode, P6. Structured understanding, not hidden reasoning as control flow (+3 more)

### Community 25 - "MockAccountTool"
Cohesion: 0.33
Nodes (4): AccountBalance, MockAccountTool, Any, Mock account data adapter.

### Community 26 - "LocalKnowledgeTool"
Cohesion: 0.27
Nodes (5): KnowledgeResult, LocalKnowledgeTool, Any, Path, Approved local knowledge retrieval adapter.

### Community 27 - "MockTransferTool"
Cohesion: 0.29
Nodes (5): MockTransferTool, Any, Idempotent mock internal-transfer adapter., TransferReceipt, TransferRequest

### Community 28 - "test_providers.py"
Cohesion: 0.42
Nodes (7): _FakeResponses, _provider(), test_non_reasoning_openai_model_omits_reasoning_parameter(), test_openai_analysis_uses_responses_api_and_returns_skill_gap(), test_openai_error_preserves_safe_api_diagnostics_and_redacts_key(), test_openai_response_generation_uses_responses_output_text(), test_openai_understands_multiple_active_task_slots()

### Community 29 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 30 - "runtime.py"
Cohesion: 0.22
Nodes (8): Provider- and transport-neutral conversation stream events., __getattr__(), Any, Agentic Member Assistant proof of concept., Avoid importing LangGraph when a lightweight utility module is used., AssistantReply, Stable LangGraph orchestration runtime., SQLite persistence for inspectable conversation state and audit events.

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
Cohesion: 0.29
Nodes (7): _NaturalTurnProvider, Models semantic multi-slot extraction and natural-number normalization., test_low_confidence_account_suffix_is_not_accepted_as_amount(), test_semantic_correction_revalidates_and_replaces_confirmation(), test_semantic_turn_understanding_collects_multiple_slots_and_word_amount(), test_semantic_turn_understanding_normalizes_disfluent_word_amount(), test_semantic_understanding_continues_an_inflight_deactivated_version()

### Community 36 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 37 - "13. Initial use cases"
Cohesion: 0.33
Nodes (6): 13.1 Account balance, 13.2 Money transfer, 13.3 FAQ / knowledge answer, 13.4 Interruption during transfer, 13.5 Live-agent handoff, 13. Initial use cases

### Community 38 - "test_interruption_and_catalog.py"
Cohesion: 0.53
Nodes (5): _install_navigation(), test_hot_discovery_then_interrupt_and_resume(), test_interruption_can_be_discarded(), test_invalid_hot_edit_retains_last_valid_skill(), test_unpublished_skill_file_does_not_change_active_catalog()

### Community 39 - "test_live_support.py"
Cohesion: 0.73
Nodes (5): _member_turn(), _queue_banking_handoff(), _receive_until(), test_live_support_assigns_routes_messages_updates_sentiment_and_ends(), test_waiting_member_can_cancel_and_return_to_virtual_assistant()

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

### Community 47 - ".__init__"
Cohesion: 0.50
Nodes (3): HandoffEnded, Publish, SentimentAnalyzer

### Community 48 - "_DisplayNameGoalProvider"
Cohesion: 0.50
Nodes (4): _DisplayNameGoalProvider, Simulates a semantic model returning a friendly label as the goal ID., test_display_name_goal_is_canonicalized_without_false_clarification(), test_persisted_duplicate_goal_clarification_recovers_on_yes()

### Community 49 - "_NoisyBalanceProvider"
Cohesion: 0.50
Nodes (3): _NoisyBalanceProvider, Simulates an LLM that speculatively fills account from the intent text., test_speculative_model_slot_uses_neutral_elicitation_then_validates_reply()

### Community 52 - "10. Response composition and guardrails"
Cohesion: 0.67
Nodes (3): 10.1 Response pipeline, 10.2 Response modes, 10. Response composition and guardrails

### Community 53 - "3. Core language model for stakeholders"
Cohesion: 0.67
Nodes (3): 3.1 Avoid confusing language, 3.2 The hierarchy, 3. Core language model for stakeholders

### Community 54 - "Skill Authoring and Publication"
Cohesion: 0.67
Nodes (3): Skill Authoring and Publication, Online ID Recovery Skill, Active Catalog Index

### Community 58 - "_CapabilityGapProvider"
Cohesion: 0.67
Nodes (3): _CapabilityGapProvider, Simulates a model that incorrectly marks capability help as a skill gap., test_capability_question_with_else_before_can_uses_catalog_response()

## Knowledge Gaps
- **186 isolated node(s):** `agentic-member-assistant`, `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)`, `Step 1 - Ensure graphify is installed` (+181 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 387 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SQLiteConversationStore` connect `SQLiteConversationStore` to `SkillCatalog`, `AgentRuntime`, `Settings`, `runtime_factory`, `catalog.py`, `.__init__`, `LiveSupportBroker`, `runtime.py`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `AgentRuntime` connect `AgentRuntime` to `SkillCatalog`, `SQLiteConversationStore`, `Any`, `Settings`, `runtime_factory`, `catalog.py`, `create_app`, `runtime.py`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `runtime_factory()` connect `runtime_factory` to `SkillCatalog`, `AgentRuntime`, `SQLiteConversationStore`, `Any`, `_NaturalTurnProvider`, `test_interruption_and_catalog.py`, `test_live_support.py`, `create_app`, `_DisplayNameGoalProvider`, `_NoisyBalanceProvider`, `test_bedrock_provider.py`, `test_declarative_skills.py`, `_CapabilityGapProvider`, `test_providers.py`, `runtime.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `AgentRuntime` (e.g. with `__getattr__()` and `SkillCatalog`) actually correct?**
  _`AgentRuntime` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 78 inferred relationships involving `runtime_factory()` (e.g. with `SkillCatalog` and `AgentRuntime`) actually correct?**
  _`runtime_factory()` has 78 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `SQLiteConversationStore` (e.g. with `LiveSupportBroker` and `AgentRuntime`) actually correct?**
  _`SQLiteConversationStore` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `SkillRoutingDefinition` (e.g. with `ModelProvider` and `BedrockProvider`) actually correct?**
  _`SkillRoutingDefinition` has 9 INFERRED edges - model-reasoned connections that need verification._