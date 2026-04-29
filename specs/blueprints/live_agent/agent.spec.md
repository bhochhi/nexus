# Blueprint: Live Agent

## Purpose
Defines the `LiveAgent` orchestrator component which bridges the virtual AI session to a real human MSR. It relies on the LLM to clarify the required queue (Banking, Insurance, Advice) and uses a tool to establish a synchronous blocking WebSocket loop connecting the CLI REPL directly to the contact center WebSocket server.

## Implements Features
- F-005: Live Agent Connection & Queue Routing
- F-006: Live Chat Bridge (Member ↔ MSR)

## Interface Contract

### `LiveAgent` (extends `BaseAgent`)
- Input: `user_input` (string)
- Output: `AgentResult`
- Behavior: 
  1. Adds user message to session history.
  2. Queries LLM with tools.
  3. If LLM decides to connect, invokes `connect_to_queue` tool.
  4. Manages terminal stream during the connection.
  5. Upon exiting the live bridge, updates `session.current_agent` to return control to the main orchestrator.

## Data Models
No specific new data models. Uses `Message` and `AgentResult` from `core.types`.

## Acceptance Criteria
- [x] Initializes with `live_agent` name and discovers tools natively.
- [x] Overrides `invoke` to process input and execute tools.
- [x] Returns control to `main_agent` automatically once the live chat session finishes.

## Dependencies
- `core.base_agent.BaseAgent`
- `core.llm.LLMClient`
- `websockets.sync.client`
