# Blueprint: Auto-Insurance Agent

## Purpose
Defines the `AutoInsuranceAgent` orchestrator component, which acts as an informational assistant capable of answering general auto insurance FAQs and servicing basic policy needs (checking details, adding/removing drivers).

## Implements Features
- F-007: Auto-Insurance Agent

## Interface Contract

### `AutoInsuranceAgent` (extends `BaseAgent`)
- **Input**: `user_input` (string)
- **Output**: `AgentResult`
- **Behavior**:
  1. Sets its system prompt to act as a helpful auto-insurance expert.
  2. Discovers and binds its specific toolset (policy retrieval, driver addition/removal).
  3. Uses LLM to determine whether to answer an FAQ, trigger a tool, or return an error/summary.
  4. Returns a summary `AgentResult` back to the Main Agent.
  5. Implements the **Supervisor Model Constraint**: It must never route directly to another sub-agent (like `LiveAgent`). All delegation or escalation is strictly handled by returning control to the `MainAgent` with a clear summary.

## Data Models
No specific new data models are required for the agent class itself. It uses `Message` and `AgentResult` from `core.types`. Data models for policy objects will be defined in the tools specification.

## Acceptance Criteria
- [ ] Initializes with `auto_insurance_agent` name and discovers its native tools.
- [ ] Overrides `invoke` to process input and execute tools cleanly.
- [ ] Refuses out-of-scope requests (e.g., generating new quotes, starting claims) and politely explains its limitations.
- [ ] Always yields control back to `main_agent` returning an `AgentResult` containing a summary of what occurred.

## Dependencies
- `core.base_agent.BaseAgent`
- `core.llm.LLMClient`
