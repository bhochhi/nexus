# Graph Report - nexus  (2026-09-02)

## Corpus Check
- 147 files · ~105,585 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1568 nodes · 2762 edges · 132 communities (101 shown, 31 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 252 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `83cc8d10`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- SkillMarkdownCompiler
- AgentRuntime
- SQLiteConversationStore
- Any
- Settings
- runtime_factory
- DeclarativeSkillExecutor
- Agentic_Chat_Architecture_Deck.md
- msr_ui.py
- Agentic Member Assistant POC
- Agentic Member Assistant POC: Architecture and Design Proposal
- What You Must Do When Invoked
- create_app
- bedrock_provider.py
- Graphify engineer guide
- LiveSupportBroker
- BedrockProvider
- TurnAnalysis
- Agentic Conversational Platform Architecture
- 5. Platform components
- OpenAIProvider
- tools/__init__.py
- runtime.py
- test_bedrock_provider.py
- 4. Architectural principles
- spec_workflow.py
- Member-facing skill title
- SkillMatch
- test_providers.py
- graphify reference: extra exports and benchmark
- SkillRoutingDefinition
- Internal account transfer
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
- Capability development and release environments
- Guided account balance
- AGENTS.md
- extraction-spec.md
- online_id_recovery/SKILL.md
- approved_knowledge/2.0.0/SKILL.md
- guided_balance/2.0.0/SKILL.md
- guided_balance/2.1.0/SKILL.md
- live_agent_handoff/2.0.0/SKILL.md
- online_id_recovery/3.0.0/SKILL.md
- agentic-member-assistant
- _ContextAwareSemanticProvider
- Live-agent handoff
- Guided balance
- Approved knowledge answers
- Internal transfer
- Online-ID recovery navigation
- Live-agent handoff
- README.md
- 12. Vendor-agnostic deployment view
- Live-agent handoff
- Conversation context and memory policy
- Console tracing reference
- Development-agent workflow guide
- Capability authoring and delivery
- Capability name
- Capability name
- Capability name
- Capability name
- SessionEventHub
- Capability name
- _SemanticInitialGoalProvider
- Spec-driven development for Nexus
- Change title
- Specification baseline and rebuild readiness
- Nexus platform constitution
- Portable specifications are the engineering source of truth
- Separate platform deployment from capability distribution
- Model output is advisory and platform decisions are authoritative
- Capabilities execute through a bounded declarative runtime surface
- Governed conversation lifecycle
- Reception and capability gaps
- Session streaming and live support
- Conversation orchestration
- Durable task state
- Capability registry
- Governed execution
- Model provider boundary
- Response composition and grounding
- Observability and audit
- Decision title
- Feature name
- Foundation name
- Nexus specification schema
- Nexus Skill v1: authoring and publication
- Capability authoring packages
- Portable platform specifications
- _CapabilityGapProvider
- _QueuedHistoryRecoveryProvider
- CLAUDE.md
- copilot-instructions.md
- approved-knowledge/SKILL.md
- guided-balance/SKILL.md
- internal-transfer/SKILL.md
- live-agent-handoff/SKILL.md
- online-id-recovery/SKILL.md
- nexus-impact-analysis/SKILL.md
- nexus-implementation-planning/SKILL.md
- nexus-implementation/SKILL.md
- nexus-independent-verification/SKILL.md
- nexus-promotion/SKILL.md
- nexus-release-evidence/SKILL.md
- nexus-spec-driven-development/SKILL.md
- nexus-specification-analysis/SKILL.md
- nexus-specification-validation/SKILL.md

## God Nodes (most connected - your core abstractions)
1. `runtime_factory()` - 90 edges
2. `AgentRuntime` - 81 edges
3. `SkillRoutingDefinition` - 46 edges
4. `SQLiteConversationStore` - 46 edges
5. `DeterministicProvider` - 36 edges
6. `SkillMarkdownCompiler` - 33 edges
7. `CatalogValidationError` - 32 edges
8. `TurnAnalysis` - 31 edges
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

## Communities (132 total, 31 thin omitted)

### Community 0 - "SkillMarkdownCompiler"
Cohesion: 0.05
Nodes (49): _artifact_hash(), CatalogValidationError, Any, Path, ValueError, Watch routing metadata and lazily load immutable SKILL.md artifacts., Load one exact artifact; routing never requires this full definition., Convenience for diagnostics that explicitly need every full skill. (+41 more)

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
Cohesion: 0.10
Nodes (40): fixture, runtime_factory(), _GapAwareProvider, test_account_reference_with_type_and_suffix_prefers_the_specific_account(), test_affirmative_answer_to_two_goal_choice_requests_a_specific_choice(), test_ambiguous_goal_reply_can_select_both_requests_in_order(), test_ambiguous_goal_reply_can_state_an_ordered_plan(), test_ambiguous_goals_are_clarified_and_answer_is_durable() (+32 more)

### Community 6 - "DeclarativeSkillExecutor"
Cohesion: 0.16
Nodes (14): SkillDefinition, ABC, Any, Common contracts for skill implementations., SkillContext, SkillExecutor, SkillResult, DeclarativeSkillExecutor (+6 more)

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
Cohesion: 0.11
Nodes (25): BaseModel, FastAPI, _async_events(), create_app(), FastAPI transport for durable member-assistant conversations., Consume a synchronous runtime stream without blocking the ASGI loop. The…, Build the API around one shared runtime and one compiled LangGraph., SessionRequest (+17 more)

### Community 13 - "bedrock_provider.py"
Cohesion: 0.24
Nodes (10): Amazon Bedrock Runtime Converse adapter. No AWS types escape this module., OpenAI adapter. No OpenAI types escape this module., parse_json_object(), parse_turn_analysis(), Any, Provider-neutral prompt and parser for conversational turn understanding., Decode a JSON object, tolerating a provider's optional Markdown fence., Validate model output against only the currently supplied skill contracts. (+2 more)

### Community 14 - "Graphify engineer guide"
Cohesion: 0.15
Nodes (13): A skill changed but the application behavior did not, A slot was filled from the wrong phrase, Conversation state behaves differently after restart, Explore the HTML graph, Graphify engineer guide, How to choose a command, Keep the graph fresh, Learn the architecture or plan a refactor (+5 more)

### Community 15 - "LiveSupportBroker"
Cohesion: 0.21
Nodes (8): HandoffEnded, Publish, SentimentAnalyzer, LiveSupportBroker, OnlineAgent, Any, Queueing and participant routing for live member support., Automatically matches waiting cases to the least-active online MSR.

### Community 16 - "BedrockProvider"
Cohesion: 0.28
Nodes (6): ProviderError, A provider failure with bounded, non-secret troubleshooting metadata., BedrockProvider, Any, Exception, Use Bedrock Converse for both Amazon Nova and Bedrock-hosted OpenAI models.

### Community 17 - "TurnAnalysis"
Cohesion: 0.26
Nodes (4): Provider-neutral semantic interpretation of one member turn., One model-interpreted active-task input with bounded confidence., SlotUpdate, TurnAnalysis

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
Cohesion: 0.05
Nodes (31): AccountBalance, MockAccountTool, Any, Mock account data adapter., HandoffReceipt, HandoffRequest, MockHandoffTool, Any (+23 more)

### Community 22 - "runtime.py"
Cohesion: 0.15
Nodes (17): Validated, file-based skill discovery with last-known-good reloads., PolicyDecision, PolicyEngine, Deterministic authorization, tool, and confirmation gates., ModelProvider, ProviderSafetyError, ABC, Stable contract that insulates the runtime and skills from model vendors. (+9 more)

### Community 23 - "test_bedrock_provider.py"
Cohesion: 0.29
Nodes (9): parametrize, _FakeBedrockClient, _response(), test_bedrock_attaches_guardrail_to_converse_request(), test_bedrock_error_keeps_safe_aws_metadata_and_redacts_credentials(), test_bedrock_guardrail_id_and_version_are_an_atomic_configuration(), test_bedrock_nova_and_terra_share_converse_turn_contract(), test_fallback_provider_never_bypasses_a_safety_error() (+1 more)

### Community 24 - "4. Architectural principles"
Cohesion: 0.17
Nodes (12): 4. Architectural principles, Bounded working context, P10. Low-code means no orchestrator changes, not no engineering ever, P1. Conversationally adaptive, operationally governed, P2. Model advises; platform decides and persists, P3. Members own objectives; skills define capabilities; the platform owns goals and tasks, P4. Every turn asks two questions, P5. Skills declare execution mode (+4 more)

### Community 25 - "spec_workflow.py"
Cohesion: 0.15
Nodes (21): evidence(), _load_markdown(), _load_yaml(), main(), _parser(), Any, ArgumentParser, Path (+13 more)

### Community 26 - "Member-facing skill title"
Cohesion: 0.33
Nodes (5): Conversation behavior, Inputs and interpretation, Member-facing skill title, Safety and boundaries, When to use

### Community 27 - "SkillMatch"
Cohesion: 0.15
Nodes (7): Any, Describe the most recent call without exposing prompt content., Understand objectives, task-relative inputs, and optional gaps. Offline…, Backward-compatible name for callers that have not migrated yet., Return safe fields that can be attached to a fallback trace., A discovery-time selection of one single-goal skill., SkillMatch

### Community 28 - "test_providers.py"
Cohesion: 0.42
Nodes (7): _FakeResponses, _provider(), test_non_reasoning_openai_model_omits_reasoning_parameter(), test_openai_analysis_uses_responses_api_and_returns_skill_gap(), test_openai_error_preserves_safe_api_diagnostics_and_redacts_key(), test_openai_response_generation_uses_responses_output_text(), test_openai_understands_multiple_active_task_slots()

### Community 29 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 30 - "SkillRoutingDefinition"
Cohesion: 0.30
Nodes (5): Small catalog record used for routing without loading executable content., SkillRoutingDefinition, DeterministicProvider, Any, Recognize a small set of unambiguous safety-critical capability gaps. This…

### Community 31 - "Internal account transfer"
Cohesion: 0.12
Nodes (15): Acceptance criteria, Complete request, Decline, Edge cases and failures, Examples, Governance and integrations, Incomplete request, Internal account transfer (+7 more)

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
Cohesion: 0.24
Nodes (7): _NoSlotSemanticProvider, Simulates an LLM declining to bind an ambiguous-looking reply., Simulates a semantic model returning a skill absent from the catalog., test_installed_skill_match_routes_without_provider_goal_identifier(), test_persisted_duplicate_goal_clarification_recovers_on_yes(), test_runtime_does_not_blindly_bind_raw_text_when_semantics_return_no_slot(), _UnknownSkillProvider

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

### Community 57 - "Capability development and release environments"
Cohesion: 0.14
Nodes (14): Authoring UI and portable source, Capability development and release environments, Decisions at a glance, Environment and version model, Local development in the current repository, Near term: one repository, Possible later split, Production catalog and hot reload (+6 more)

### Community 58 - "Guided account balance"
Cohesion: 0.14
Nodes (13): Acceptance criteria, Correction, Edge cases and failures, Examples, Governance and integrations, Guided account balance, Member scenarios, Purpose and member value (+5 more)

### Community 68 - "_ContextAwareSemanticProvider"
Cohesion: 0.50
Nodes (3): _ContextAwareSemanticProvider, Uses bounded conversation state to resolve an ordinal reference., test_semantic_provider_can_resolve_slot_from_bounded_conversation_context()

### Community 69 - "Live-agent handoff"
Cohesion: 0.14
Nodes (13): Acceptance criteria, Ambiguous queue, Clear queue, Edge cases and failures, Examples, Governance and integrations, Interrupted work, Live-agent handoff (+5 more)

### Community 70 - "Guided balance"
Cohesion: 0.33
Nodes (5): Conversation behavior, Guided balance, Inputs and interpretation, Safety and boundaries, When to use

### Community 71 - "Approved knowledge answers"
Cohesion: 0.15
Nodes (12): Acceptance criteria, Approved knowledge answers, Edge cases and failures, Examples, Governance and integrations, Member scenarios, No approved source, Purpose and member value (+4 more)

### Community 72 - "Internal transfer"
Cohesion: 0.33
Nodes (5): Conversation behavior, Inputs and interpretation, Internal transfer, Safety and boundaries, When to use

### Community 73 - "Online-ID recovery navigation"
Cohesion: 0.15
Nodes (12): Acceptance criteria, Direct request, Edge cases and failures, Examples, Governance and integrations, Member scenarios, Online-ID recovery navigation, Purpose and member value (+4 more)

### Community 74 - "Live-agent handoff"
Cohesion: 0.33
Nodes (5): Conversation behavior, Inputs and interpretation, Live-agent handoff, Safety and boundaries, When to use

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
Cohesion: 0.15
Nodes (12): Categories and observation names, Common provider and model fields, Console tracing reference, Did a provider fallback occur?, Fields available in JSON and Langfuse, Policy, skill, tool, gap, and turn fields, Reading one line, Understanding fields (`LLM llm.turn_understanding`) (+4 more)

### Community 80 - "Development-agent workflow guide"
Cohesion: 0.18
Nodes (10): Claude Code, Codex, Cross-agent handoff, Deterministic helper commands, Development-agent workflow guide, GitHub Copilot, Guardrails, Lifecycle stages (+2 more)

### Community 81 - "Capability authoring and delivery"
Cohesion: 0.18
Nodes (10): Acceptance criteria, Business-authored draft, Capability authoring and delivery, Edge cases, Examples, Purpose, Required behavior, Required platform extension (+2 more)

### Community 82 - "Capability name"
Cohesion: 0.18
Nodes (10): Acceptance criteria, Capability name, Edge cases and failures, Examples, Governance and integrations, Member scenarios, Purpose and member value, Required behavior (+2 more)

### Community 83 - "Capability name"
Cohesion: 0.18
Nodes (10): Acceptance criteria, Capability name, Edge cases and failures, Examples, Governance and integrations, Member scenarios, Purpose and member value, Required behavior (+2 more)

### Community 84 - "Capability name"
Cohesion: 0.18
Nodes (10): Acceptance criteria, Capability name, Edge cases and failures, Examples, Governance and integrations, Member scenarios, Purpose and member value, Required behavior (+2 more)

### Community 85 - "Capability name"
Cohesion: 0.18
Nodes (10): Acceptance criteria, Capability name, Edge cases and failures, Examples, Governance and integrations, Member scenarios, Purpose and member value, Required behavior (+2 more)

### Community 86 - "SessionEventHub"
Cohesion: 0.29
Nodes (3): Any, In-process fan-out for every socket watching the same session. Durable SQLite…, SessionEventHub

### Community 87 - "Capability name"
Cohesion: 0.18
Nodes (10): Acceptance criteria, Capability name, Edge cases and failures, Examples, Governance and integrations, Member scenarios, Purpose and member value, Required behavior (+2 more)

### Community 88 - "_SemanticInitialGoalProvider"
Cohesion: 0.67
Nodes (3): Returns semantic goal inputs that conflict with shape-based extraction., _SemanticInitialGoalProvider, test_semantic_goal_inputs_override_shape_based_fallback_extraction()

### Community 89 - "Spec-driven development for Nexus"
Cohesion: 0.20
Nodes (10): Authority and artifact model, Baseline authority and rebuild readiness, Capability authoring experience, Capability publication and runtime discovery, Development workflow, Draft preview and shared test, Mandatory platform-impact decision, Near-term implementation sequence (+2 more)

### Community 90 - "Change title"
Cohesion: 0.20
Nodes (9): Acceptance and verification impact, Affected artifacts, Change title, Classification, Dependency and release order, Platform capability-surface comparison, Relevant specifications, Requested outcome (+1 more)

### Community 91 - "Specification baseline and rebuild readiness"
Cohesion: 0.22
Nodes (8): Certification gate, Current baseline classification, Pinning and change policy, Rebuild-complete package, Specification baseline and rebuild readiness, Two meanings of source of truth, What the baseline covers well, Why a specification-only rebuild is not certified

### Community 92 - "Nexus platform constitution"
Cohesion: 0.25
Nodes (7): Nexus platform constitution, Principles, Purpose, Quality gates, Safety and governance, Specification authority, Terminology

### Community 93 - "Portable specifications are the engineering source of truth"
Cohesion: 0.25
Nodes (7): Alternatives considered, Consequences, Context, Decision, Enforcement, Portable specifications are the engineering source of truth, Supersession

### Community 94 - "Separate platform deployment from capability distribution"
Cohesion: 0.25
Nodes (7): Alternatives considered, Consequences, Context, Decision, Enforcement, Separate platform deployment from capability distribution, Supersession

### Community 95 - "Model output is advisory and platform decisions are authoritative"
Cohesion: 0.25
Nodes (7): Alternatives considered, Consequences, Context, Decision, Enforcement, Model output is advisory and platform decisions are authoritative, Supersession

### Community 96 - "Capabilities execute through a bounded declarative runtime surface"
Cohesion: 0.25
Nodes (7): Alternatives considered, Capabilities execute through a bounded declarative runtime surface, Consequences, Context, Decision, Enforcement, Supersession

### Community 97 - "Governed conversation lifecycle"
Cohesion: 0.25
Nodes (7): Acceptance criteria, Edge cases, Examples, Governed conversation lifecycle, Purpose, Required behavior, Verification

### Community 98 - "Reception and capability gaps"
Cohesion: 0.25
Nodes (7): Acceptance criteria, Edge cases, Examples, Purpose, Reception and capability gaps, Required behavior, Verification

### Community 99 - "Session streaming and live support"
Cohesion: 0.25
Nodes (7): Acceptance criteria, Edge cases, Examples, Purpose, Required behavior, Session streaming and live support, Verification

### Community 100 - "Conversation orchestration"
Cohesion: 0.25
Nodes (7): Conversation orchestration, Failure behavior, Interfaces, Invariants, Purpose, Responsibilities, Verification

### Community 101 - "Durable task state"
Cohesion: 0.25
Nodes (7): Durable task state, Failure behavior, Interfaces, Invariants, Purpose, Responsibilities, Verification

### Community 102 - "Capability registry"
Cohesion: 0.25
Nodes (7): Capability registry, Failure behavior, Interfaces, Invariants, Purpose, Responsibilities, Verification

### Community 103 - "Governed execution"
Cohesion: 0.25
Nodes (7): Failure behavior, Governed execution, Interfaces, Invariants, Purpose, Responsibilities, Verification

### Community 104 - "Model provider boundary"
Cohesion: 0.25
Nodes (7): Failure behavior, Interfaces, Invariants, Model provider boundary, Purpose, Responsibilities, Verification

### Community 105 - "Response composition and grounding"
Cohesion: 0.25
Nodes (7): Failure behavior, Interfaces, Invariants, Purpose, Response composition and grounding, Responsibilities, Verification

### Community 106 - "Observability and audit"
Cohesion: 0.25
Nodes (7): Failure behavior, Interfaces, Invariants, Observability and audit, Purpose, Responsibilities, Verification

### Community 107 - "Decision title"
Cohesion: 0.25
Nodes (7): Alternatives considered, Consequences, Context, Decision, Decision title, Enforcement, Supersession

### Community 108 - "Feature name"
Cohesion: 0.25
Nodes (7): Acceptance criteria, Edge cases, Examples, Feature name, Purpose, Required behavior, Verification

### Community 109 - "Foundation name"
Cohesion: 0.25
Nodes (7): Failure behavior, Foundation name, Interfaces, Invariants, Purpose, Responsibilities, Verification

### Community 110 - "Nexus specification schema"
Cohesion: 0.29
Nodes (6): Artifact boundaries, Authority layers, Change package, Common identity, Lifecycle, Nexus specification schema

### Community 111 - "Nexus Skill v1: authoring and publication"
Cohesion: 0.33
Nodes (6): Archetypes are presets, not a closed capability taxonomy, Commands, Nexus Skill v1: authoring and publication, One authoring file, not four required files, Publication and call flow, What a production platform still needs

### Community 112 - "Capability authoring packages"
Cohesion: 0.40
Nodes (4): Archetype templates, Capability authoring packages, Current capability packages, Two related lifecycles

### Community 113 - "Portable platform specifications"
Cohesion: 0.50
Nodes (3): Layout, Portable platform specifications, Terms

### Community 114 - "_CapabilityGapProvider"
Cohesion: 0.67
Nodes (3): _CapabilityGapProvider, Simulates a model that incorrectly marks capability help as a skill gap., test_capability_question_with_else_before_can_uses_catalog_response()

### Community 115 - "_QueuedHistoryRecoveryProvider"
Cohesion: 0.67
Nodes (3): _QueuedHistoryRecoveryProvider, Recovers initially missed queued-goal inputs from member evidence., test_queued_task_missing_inputs_are_elicited_without_reconsent()

## Knowledge Gaps
- **530 isolated node(s):** `agentic-member-assistant`, `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)`, `Step 1 - Ensure graphify is installed` (+525 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 811 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentRuntime` connect `AgentRuntime` to `SkillMarkdownCompiler`, `SQLiteConversationStore`, `Any`, `Settings`, `runtime_factory`, `DeclarativeSkillExecutor`, `create_app`, `runtime.py`, `SkillRoutingDefinition`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `runtime_factory()` connect `runtime_factory` to `SkillMarkdownCompiler`, `AgentRuntime`, `SQLiteConversationStore`, `Any`, `_NaturalTurnProvider`, `_ContextAwareSemanticProvider`, `test_interruption_and_catalog.py`, `create_app`, `_UnknownSkillProvider`, `_NoisyBalanceProvider`, `_CapabilityGapProvider`, `_QueuedHistoryRecoveryProvider`, `runtime.py`, `test_bedrock_provider.py`, `_SemanticInitialGoalProvider`, `test_providers.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `SQLiteConversationStore` connect `SQLiteConversationStore` to `AgentRuntime`, `Settings`, `runtime_factory`, `LiveSupportBroker`, `runtime.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `runtime_factory()` (e.g. with `SkillCatalog` and `AgentRuntime`) actually correct?**
  _`runtime_factory()` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `AgentRuntime` (e.g. with `__getattr__()` and `SkillCatalog`) actually correct?**
  _`AgentRuntime` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `SkillRoutingDefinition` (e.g. with `ModelProvider` and `BedrockProvider`) actually correct?**
  _`SkillRoutingDefinition` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `SQLiteConversationStore` (e.g. with `LiveSupportBroker` and `AgentRuntime`) actually correct?**
  _`SQLiteConversationStore` has 9 INFERRED edges - model-reasoned connections that need verification._