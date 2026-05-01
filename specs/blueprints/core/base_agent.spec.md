# Spec: BaseAgent

## Purpose
Abstract base class that all agents extend. Provides the common structure: loading spec files (persona.md, instruction.md), building a LangGraph StateGraph, constructing system prompts, and defining the invocation interface. Ensures every agent follows the same pattern regardless of complexity.

## Interface Contract

### `class BaseAgent(ABC)`

#### `__init__(self, agent_name: str, llm_client: LLMClient, session: SessionState)`
- Store agent_name, llm_client, and session reference
- Determine the agent's module directory from `agents/{agent_name}/`
- Load `persona.md` from the agent's directory (store as string)
- Load `instruction.md` from the agent's directory (store as string)
- Call `self.build_graph()` to initialize the agent's LangGraph
- Call `self.get_tools()` to initialize the agent's tool list

#### `_load_md(self, filename: str) -> str`
- Read a markdown file from the agent's module directory
- Return the file contents as a string
- If file doesn't exist, return empty string and log warning

#### `get_system_prompt(self, additional_context: str = "") -> str`
- Combine persona + instruction + additional_context into a single system prompt
- Format:
  ```
  ## Persona
  {persona.md contents}

  ## Instructions
  {instruction.md contents}

  ## Context
  {additional_context}
  ```
- Skip empty sections

#### `@abstractmethod build_graph(self) -> StateGraph`
- Each agent must define its own LangGraph StateGraph
- Returns a compiled graph ready for invocation

#### `@abstractmethod get_tools(self) -> List`
- Each agent must return its list of `@tool`-decorated functions
- The orchestrator's tools are built dynamically from discovered capabilities
- Simple agents may return an empty list

#### `invoke(self, user_input: str) -> AgentResult`
- Main entry point for processing a member's message
- Add user message to this agent's conversation history
- Build system prompt (persona + instructions + delegation summary if present)
- Enter an iterative tool-calling loop (max 5 turns):
  - Execute LLM with current state and tools
  - If LLM calls `yield_control(final_message, status)`:
    - Extract `final_message` and `status` (which must be `"complete"` or `"error"`).
    - If `status="error"`, the system returns the error state to the orchestrator to trigger anti-looping or graceful degradation.
    - Set `current_agent="main_agent"`, mark `delegation_occurred=True`, and break the loop.
  - If LLM calls other tools: execute the tool natively, append tool result to history, and continue the loop.
  - If LLM responds with plain text: add assistant response to history and break the loop.
- Return `AgentResult` with response, active_agent, reasoning, state snapshot, and delegation status.

#### `_get_conversation_messages(self) -> List[Message]`
- Retrieve this agent's conversation history from session
- Uses `session.get_agent_state(self.agent_name).conversation_history`

#### `_get_delegation_context(self) -> str`
- Check if this agent has a delegation_summary in its state
- If yes, format it as context: "Previous agent summary: {summary}"
- If no, return empty string

## LangGraph Pattern

Every agent's graph follows this minimal pattern:

```python
# Simple agent (e.g., FAQ agent)
class SimpleAgent(BaseAgent):
    def build_graph(self):
        graph = StateGraph(AgentGraphState)
        graph.add_node("process", self.process_node)
        graph.add_edge(START, "process")
        graph.add_edge("process", END)
        return graph.compile()

# Complex agent (e.g., orchestrator)
class MainAgent(BaseAgent):
    def build_graph(self):
        graph = StateGraph(AgentGraphState)
        graph.add_node("check_session", self.check_session)
        graph.add_node("greet", self.greet)
        graph.add_node("process", self.process)
        graph.add_node("delegate", self.delegate)
        graph.add_edge(START, "check_session")
        graph.add_conditional_edges("check_session", self.route_session)
        ...
        return graph.compile()
```

### `AgentGraphState` (base TypedDict for LangGraph)

```python
class AgentGraphState(TypedDict):
    messages: List[Message]         # Conversation messages for this graph run
    system_prompt: str              # Assembled system prompt
    tools: List                     # Tools available to this agent
    response: str                   # Final response text
    reasoning: str                  # LLM reasoning for debug
    tool_call: Optional[ToolCall]   # Pending tool call (if any)
```

Each agent can extend this with agent-specific fields in its own `state.py`.

## Acceptance Criteria

- [ ] BaseAgent is abstract — cannot be instantiated directly
- [ ] `build_graph` and `get_tools` are abstract methods
- [ ] `__init__` loads persona.md and instruction.md from agent's directory
- [ ] Missing persona.md or instruction.md doesn't crash (returns empty string)
- [ ] `get_system_prompt` combines persona + instructions + context
- [ ] `get_system_prompt` skips empty sections
- [ ] `invoke` adds user message to agent's own conversation history (not another agent's)
- [ ] `invoke` adds assistant response to agent's own conversation history
- [ ] `invoke` returns `AgentResult` with response, active_agent, reasoning, state_snapshot
- [ ] `_get_delegation_context` returns summary when present, empty string when not
- [ ] Agent's conversation history is isolated — never touches other agents' histories
- [ ] All agents use LangGraph StateGraph pattern (even simple ones)

## Examples

```python
# A concrete agent extending BaseAgent
class GreeterAgent(BaseAgent):
    def build_graph(self):
        graph = StateGraph(AgentGraphState)
        graph.add_node("greet", self.greet_node)
        graph.add_edge(START, "greet")
        graph.add_edge("greet", END)
        return graph.compile()

    def get_tools(self):
        return []

    def greet_node(self, state):
        response = self.llm.invoke(
            state["messages"],
            self.get_system_prompt()
        )
        return {"response": response.text, "reasoning": response.reasoning}

# Usage
agent = GreeterAgent("greeter", llm_client, session)
result = agent.invoke("Hello!")
assert result.response != ""
assert result.active_agent == "greeter"
```

## Dependencies
- `langgraph` (StateGraph, START, END)
- `core.types` (Message, AgentResult, AgentGraphState)
- `core.session` (SessionState)
- `core.llm` (LLMClient)
