# Spec: Shared Types

## Purpose
Defines all shared types, enums, data contracts, and message formats used across the Nexus platform. This is the foundation that all other modules import from.

## Data Models

### `Message`
A single conversation turn between member and agent.

```python
@dataclass
class Message:
    role: str           # "user" | "assistant" | "system" | "tool"
    content: str        # The message text
    agent: str          # Which agent produced this message (e.g., "main_agent")
    timestamp: datetime # When the message was created
    metadata: Dict[str, Any]  # Optional extra data (tool calls, reasoning, etc.)
```

### `Skill`
A capability advertised by an agent in its `agent.md`.

```python
@dataclass
class Skill:
    name: str           # e.g., "connect_to_live_agent"
    description: str    # e.g., "Connect member to a human representative"
```

### `AgentCapability`
Full capability manifest for a discovered agent.

```python
@dataclass
class AgentCapability:
    name: str               # e.g., "live_agent"
    display_name: str       # e.g., "Live Agent Support"
    description: str        # What this agent does (from agent.md)
    skills: List[Skill]     # List of skills this agent offers
    version: str            # Semantic version string
    status: str             # "active" | "beta" | "disabled"
    module_path: str        # Filesystem path to the agent module
```

### `DelegationRequest`
Sent from orchestrator to sub-agent when delegating.

```python
@dataclass
class DelegationRequest:
    source_agent: str       # "main_agent"
    target_agent: str       # "live_agent"
    user_input: str         # The member's message that triggered delegation
    summary: str            # LLM-generated summary of conversation so far
    session_id: str         # Current session ID
    context: Dict[str, Any] # Additional context (classified skill, entities)
```

### `DelegationResponse`
Returned from sub-agent to orchestrator.

```python
@dataclass
class DelegationResponse:
    agent_name: str             # "live_agent"
    response: str               # Message to show member
    status: str                 # "complete" | "in_progress" | "needs_input" | "error"
    summary: str                # Summary of what this agent accomplished
    session_updates: Dict[str, Any]  # Changes to write back to session
    return_to_orchestrator: bool     # True = hand control back to main_agent
```

### `LLMResponse`
Returned from the LLM client after an invocation.

```python
@dataclass
class LLMResponse:
    text: str                           # LLM's text response (if any)
    tool_call: Optional[ToolCall]       # Tool call request (if any)
    reasoning: str                      # LLM's reasoning (for debug panel)
    raw_response: Dict[str, Any]        # Full raw response from Bedrock

@dataclass
class ToolCall:
    name: str                   # Tool function name
    arguments: Dict[str, Any]   # Arguments to pass to the tool
    tool_use_id: str            # Unique ID for this tool invocation
```

### `AgentResult`
Returned from any agent invocation to the app.py REPL loop.

```python
@dataclass
class AgentResult:
    response: str               # Message to display to member
    active_agent: str           # Which agent handled this turn
    llm_reasoning: str          # LLM's reasoning for the debug panel
    state_snapshot: Dict[str, Any]  # Current state for the debug panel
    delegation_occurred: bool   # Whether delegation happened this turn
    status: str                 # "success" | "error" | "needs_input" | "in_progress"
    error_details: Optional[str] # Raw error string if status == "error"
```

## Acceptance Criteria

- [ ] All dataclasses are importable from `core.types`
- [ ] All dataclasses use `@dataclass` decorator (not Pydantic for v1)
- [ ] `Message.role` only accepts: "user", "assistant", "system", "tool"
- [ ] `AgentCapability.status` only accepts: "active", "beta", "disabled"
- [ ] `DelegationResponse.status` only accepts: "complete", "in_progress", "needs_input", "error"
- [ ] `AgentResult.status` only accepts: "success", "error", "needs_input", "in_progress"
- [ ] All timestamp fields use `datetime` from stdlib
- [ ] All Dict fields default to empty dict via `field(default_factory=dict)`
- [ ] All Optional fields default to `None`
- [ ] Types module has zero external dependencies (stdlib only + dataclasses)

## Dependencies
- None (stdlib only)
