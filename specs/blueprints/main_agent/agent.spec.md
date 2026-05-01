# Blueprint: Main Agent Entry Point

## Purpose
Defines the `MainAgent` entry point which extends `BaseAgent`. This component is responsible for orchestrating the overall session flow, injecting the `RESTRICTED_MAIN_AGENT` constraints, and managing the anti-looping circuit breaker for failed sub-agent delegations.

## Implements Features
- F-001: Member Greeting & Session Management
- F-003: Skill-Based Routing & Delegation
- Anti-Looping Circuit Breaker
- Restricted Orchestrator Pattern

## Interface Contract

### `class MainAgent(BaseAgent)`

#### `__init__(self, llm_client, session, capabilities, agent_discovery_service)`
- Initializes the orchestrator with discovered capabilities.
- Dynamically builds its tools from `capabilities` using `build_tools(capabilities)`.

#### `invoke(self, user_input: str) -> AgentResult`
- **Sub-Agent Routing**: If `session.current_agent != self.agent_name`, delegates the `user_input` directly to the active sub-agent.
- **Handoff Enforcement**: Inspects the `AgentResult` from sub-agents. If `result.status` is `"complete"` or `"error"`, the Main Agent explicitly reclaims control (`session.current_agent = self.agent_name`).
- **Anti-Looping Circuit Breaker**: 
  - If a sub-agent returns `status="error"`, logs the failure in `session.context["failed_delegations"][sub_agent_name]` with a timestamp.
  - Checks `failed_delegations` on every turn. Agents failing within `AGENT_BLACKLIST_TIMEOUT_SECONDS` (default: 30) are added to a temporary blacklist and injected into the system prompt to prevent the LLM from attempting re-delegation.
- **Restricted Main Agent Constraints**: 
  - Checks the `RESTRICTED_MAIN_AGENT` environment variable (default: `true`).
  - When true, injects strict prompt constraints forcing the LLM to only perform greetings and delegations, strictly preventing it from answering domain-specific queries.

#### `get_tools(self) -> List`
- Returns the dynamically built tools (e.g., `delegate_to_agent`, `show_capabilities`).

## System Prompt Construction
The system prompt dynamically aggregates:
1. `persona.md` and `instruction.md`
2. Discovered capabilities
3. Session state indicators (new session vs. returning)
4. Temporary blacklisted agents (if any)
5. `RESTRICTED_MAIN_AGENT` constraints

## Dependencies
- `core.base_agent` (BaseAgent)
- `main_agent.graph` (build_main_agent_graph)
- `main_agent.tools` (build_tools)
- `core.session` (SessionState)
