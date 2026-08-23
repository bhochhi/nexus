# Codex build prompt: Agentic Member Assistant POC

Build a small, runnable proof of concept for a financial-services member assistant. The goal is to demonstrate a single agent orchestrator that routes member requests to different skill types while safely managing state, interruptions, and mock integrations.

## Technology and scope

- Use Python and LangGraph for the conversation state and flow.
- Use OpenAI as the configurable default LLM provider for the demo, but implement a provider-neutral model interface so Amazon Bedrock can be added later without changing skills, prompts, graph nodes, or business policy.
- Keep the implementation modular, readable, and easy to extend.
- Use only mock data and mock tool calls. Do not connect to real financial systems or use real member data.
- Provide a simple local command-line chat interface and automated tests for the main scenarios.
- Include a concise README explaining how to run the application, add a skill, and run tests.

## Architecture requirements

1. Create a stable agent runtime that owns shared conversation behavior: intent/goal understanding, skill routing, policy checks, clarification, confirmation, interruption, resumption, response delivery, and live-agent handoff.
2. Use LangGraph for the common stateful conversation flow. Define explicit typed state for messages, active task, paused tasks, pending clarification, selected skill, confirmation status, and outcome.
3. Persist conversation state locally for the POC so a paused task can be inspected and resumed. Use a simple, suitable local persistence mechanism.
4. Do not hard-code individual skills into the orchestration flow. Build a file-based skill catalog with one skill definition per file.
5. Create a catalog discovery service that loads the skill files and detects valid additions or changes while the runtime is running. A newly added valid skill must become routable without restarting the application. If a changed file is invalid, preserve the last valid catalog.
6. Keep the LangGraph graph stable. Route dynamically through a generic skill-execution node using the currently discovered catalog; do not rebuild the graph for every catalog change.
7. Treat all mock tools as replaceable adapters with stable input and output schemas.
8. Keep provider configuration in environment-based settings: provider name, model identifier, and credentials. Do not embed provider-specific client code outside the provider adapter.

## Implement these initial skills

1. **Knowledge skill:** answer a mock banking or insurance FAQ using approved local knowledge content and a consistent response template.
2. **Guided-resolution skill:** handle an account-balance request. Use a mock account tool. The skill configuration controls whether to show all eligible balances up to a threshold or ask the member to select an account.
3. **Deterministic workflow skill:** handle a mock internal transfer. Collect source account, destination account, and amount; validate the request; show a review; require explicit confirmation immediately before submitting the mock transfer.
4. **Human-handoff skill:** create a mock live-agent escalation when the member asks for a person or is marked as frustrated. Return a concise handoff summary containing the active goal and completed steps.
5. **Navigation skill:** implement online-ID recovery as a separately discoverable skill. Its mock tool returns an approved recovery URL. Demonstrate adding this skill file while the application is running and routing to it without restart.

## Required conversation behavior

- Support a member message that contains more than one goal, but execute consequential actions one safe step at a time.
- When a new goal interrupts a pending task, save the current task in durable state, complete the new request, then ask whether the member wants to resume or discard the prior task.
- Skills own business rules and response policy. The orchestrator owns routing, interruption, task priority, pause/resume, confirmations, and handoff transitions.
- Reject or hand off unsupported requests safely; do not invent account data or transaction outcomes.

## Demonstration and tests

Include tests or a scripted demonstration for:

- grounded FAQ response;
- balance clarification or configured multi-account display;
- transfer confirmation and successful mock execution;
- member interruption followed by resume or discard;
- live-agent handoff;
- discovery of the online-ID navigation skill without application restart.

At completion, report the project structure, how to run the demo and tests, and any intentional simplifications made for the POC.
