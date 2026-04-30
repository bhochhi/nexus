# Spec: SessionManager

## Purpose
Manages member sessions with per-agent isolated state. Each session is unique to a member and contains separate conversation histories and state buckets for each agent. The session is the shared communication bus — agents share context through it but never read each other's conversation history directly.

## Interface Contract

### `class SessionManager`

#### `__init__(self)`
- Creates an in-memory session store (dict)
- No external dependencies for v1

#### `get_or_create(self, member_id: str) -> SessionState`
- If a session exists for `member_id`, return it with `is_new_session=False`
- If no session exists, create a new `SessionState` with:
  - `session_id`: new UUID4 string
  - `member_id`: the provided member_id
  - `created_at`: current UTC datetime
  - `is_new_session`: True
  - `current_agent`: "main_agent"
  - `agent_states`: empty dict
  - `context`: empty dict
  - `metadata`: empty dict
- Always update `last_active` to current UTC datetime

#### `update(self, session: SessionState) -> None`
- Persist the updated session state
- Update `last_active` timestamp

#### `get(self, session_id: str) -> Optional[SessionState]`
- Retrieve session by session_id
- Return None if not found

## Data Models

### `AgentState`
Per-agent isolated state bucket.

```python
@dataclass
class AgentState:
    conversation_history: List[Message]  # This agent's own conversation turns
    delegation_summary: Optional[str]    # Summary received when delegated to
    data: Dict[str, Any]                 # Agent-specific working data
    results: List[AgentResult]           # Complete history of AgentResult objects
```

### `SessionState`
The shared session object.

```python
@dataclass
class SessionState:
    session_id: str
    member_id: str
    created_at: datetime
    last_active: datetime
    is_new_session: bool
    current_agent: str
    agent_states: Dict[str, AgentState]
    context: Dict[str, Any]
    metadata: Dict[str, Any]
```

### Helper Methods on SessionState

#### `get_agent_state(self, agent_name: str) -> AgentState`
- Return the AgentState for the given agent name
- If it doesn't exist, create a new empty AgentState, store it, and return it
- This ensures agents always get a valid state bucket

#### `add_message(self, agent_name: str, message: Message) -> None`
- Append a message to the specified agent's conversation_history
- Creates the agent state if it doesn't exist

#### `set_delegation_summary(self, agent_name: str, summary: str) -> None`
- Set the delegation_summary on the specified agent's state
- Creates the agent state if it doesn't exist

## Acceptance Criteria

- [ ] New member gets a session with `is_new_session=True`
- [ ] Same `member_id` on second call returns same session with `is_new_session=False`
- [ ] `session_id` is a valid UUID4 string
- [ ] `current_agent` defaults to "main_agent" on new sessions
- [ ] `agent_states` is empty dict on new sessions
- [ ] `get_agent_state` auto-creates AgentState if not found
- [ ] `add_message` appends to the correct agent's history
- [ ] `set_delegation_summary` sets summary on the correct agent's state
- [ ] `last_active` is updated on every `get_or_create` and `update` call
- [ ] Sessions are stored in-memory (dict keyed by member_id)
- [ ] `get` by session_id returns None when not found
- [ ] Multiple sessions for different member_ids are independent

## Examples

```python
mgr = SessionManager()

# New member
s1 = mgr.get_or_create("M123")
assert s1.is_new_session == True
assert s1.current_agent == "main_agent"
assert s1.agent_states == {}

# Returning member
s2 = mgr.get_or_create("M123")
assert s2.is_new_session == False
assert s1.session_id == s2.session_id

# Agent state isolation
s1.add_message("main_agent", Message(role="user", content="hello", ...))
s1.add_message("live_agent", Message(role="user", content="connect me", ...))
assert len(s1.get_agent_state("main_agent").conversation_history) == 1
assert len(s1.get_agent_state("live_agent").conversation_history) == 1

# Delegation summary
s1.set_delegation_summary("live_agent", "Member wants to speak about banking.")
assert s1.get_agent_state("live_agent").delegation_summary == "Member wants to speak about banking."
```

## Dependencies
- `core.types` (Message, AgentState, SessionState)
