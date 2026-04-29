# Blueprint: Main Agent — Graph Node Functions

## Purpose
Defines the individual node functions for the Main Agent's LangGraph. Each node is a function that takes graph state and returns state updates. Nodes handle LLM interaction, delegation execution, tool response processing, and final response assembly.

## Implements Features
- F-001: Member Greeting & Session Management
- F-003: Skill-Based Routing & Delegation
- F-004: Graceful Capability Decline
- F-007: Debug Transparency Panel (reasoning extraction)

## Node Functions

### `process_node(state) -> dict`

The core LLM interaction node. Calls the LLM with the system prompt, conversation history, and tools. The LLM either responds with text or requests a tool call.

```python
def process_node(state: MainAgentState) -> dict:
    """Call LLM with tools. Returns text response or tool call request.

    Input state:
        - messages: conversation history
        - system_prompt: assembled prompt with persona + instructions + context
        - tools: list of available tools

    Output state updates:
        - response: LLM's text response (if direct response)
        - reasoning: extracted reasoning from <reasoning> tags
        - tool_call: tool call dict (if LLM requested a tool)
    """
```

**Behavior:**
1. Call `llm.invoke_with_tools(messages, system_prompt, tools)`
2. Extract reasoning from `<reasoning>` tags in the response
3. If LLM returned a tool call → set `tool_call` in state
4. If LLM returned text → set `response` in state
5. Return state updates

**Reasoning Extraction:**
```python
import re

def extract_reasoning(text: str) -> tuple[str, str]:
    """Extract <reasoning>...</reasoning> content and clean response text.

    Returns: (reasoning_text, cleaned_response)
    """
    match = re.search(r"<reasoning>(.*?)</reasoning>", text, re.DOTALL)
    if match:
        reasoning = match.group(1).strip()
        clean = re.sub(r"<reasoning>.*?</reasoning>", "", text, flags=re.DOTALL).strip()
        return reasoning, clean
    return "", text
```

### `delegate_node(state) -> dict`

Executes the delegation when the LLM calls `delegate_to_agent`. Generates a conversation summary, instantiates the target sub-agent, invokes it, and captures the result.

```python
def delegate_node(state: MainAgentState) -> dict:
    """Execute delegation to a sub-agent.

    Input state:
        - tool_call: {"name": "delegate_to_agent", "arguments": {...}}
        - messages: conversation history (for summary generation)

    Output state updates:
        - delegation_result: sub-agent's response text
        - reasoning: updated with delegation details
        - tool_call: cleared (set to None)
    """
```

**Behavior:**
1. Extract `agent_name`, `skill`, `reason` from `tool_call.arguments`
2. Generate a conversation summary via LLM:
   - Prompt: "Summarize this conversation in 2-3 sentences for handoff to {agent_name}."
3. Set `delegation_summary` on the target agent's state in session
4. Update `session.current_agent` to target agent
5. Instantiate the target agent (via agent registry or dynamic import)
6. Call `target_agent.invoke(user_input)` with the original member message
7. Capture the sub-agent's `AgentResult`
8. Set `delegation_summary` on main_agent's state with the return summary
9. Update `session.current_agent` back to `main_agent`
10. Return delegation result

**Agent Instantiation:**
For v1, use a simple registry pattern:

```python
AGENT_REGISTRY = {
    "live_agent": lambda llm, session: LiveAgent(llm, session),
}
```

Future: dynamic import from `agents/{name}/agent.py`.

### `tool_response_node(state) -> dict`

Handles non-delegation tool calls (e.g., `show_capabilities`). Executes the tool and feeds the result back as a tool response message.

```python
def tool_response_node(state: MainAgentState) -> dict:
    """Execute a non-delegation tool and feed result back to LLM.

    Input state:
        - tool_call: {"name": "show_capabilities", "arguments": {...}}

    Output state updates:
        - messages: appended with tool result message
        - tool_call: cleared (set to None)
    """
```

**Behavior:**
1. Execute the tool function with provided arguments
2. Append tool result as a message with `role: "tool"` to messages
3. Clear `tool_call` so the graph loops back to `process`
4. The LLM gets the tool result and generates a natural language response

### `respond_node(state) -> dict`

Final node that assembles the response for the app layer. Handles both direct responses and delegation wrap-up.

```python
def respond_node(state: MainAgentState) -> dict:
    """Assemble final response.

    Input state:
        - response: direct LLM response text (if no delegation)
        - delegation_result: sub-agent response (if delegation occurred)

    Output state updates:
        - response: final response text for the member
    """
```

**Behavior:**
1. If `delegation_result` is set, use it as the response
2. Otherwise, use the LLM's direct text response
3. Return the final response

## Graceful Decline Handling

Graceful decline (F-004) is NOT a separate node — it's handled naturally by the LLM in the `process` node:

1. The system prompt includes instructions for decline behavior (from `instruction.md`)
2. The available tools only include agents that exist
3. When no skill matches, the LLM follows its instructions to acknowledge, explain, and list alternatives
4. The LLM responds with text (no tool call) → routes to `respond` directly

This keeps the graph simple while leveraging the LLM's natural language ability for empathetic decline.

## Acceptance Criteria

- [ ] `process_node` calls LLM with tools and returns response or tool_call
- [ ] `process_node` extracts `<reasoning>` tags from LLM response
- [ ] `delegate_node` generates conversation summary via LLM
- [ ] `delegate_node` sets delegation_summary on target agent's session state
- [ ] `delegate_node` instantiates and invokes the target sub-agent
- [ ] `delegate_node` captures sub-agent response and return summary
- [ ] `delegate_node` updates session.current_agent during delegation
- [ ] `tool_response_node` executes tool and feeds result back to process
- [ ] `tool_response_node` clears tool_call state after execution
- [ ] `respond_node` handles both direct responses and delegation results
- [ ] Graceful decline is handled by LLM reasoning, not a separate node
- [ ] All nodes are pure functions that take state and return state updates
- [ ] Reasoning is always populated for the debug panel

## Dependencies
- `core.llm` (LLMClient)
- `core.session` (SessionState, AgentState)
- `core.types` (Message, AgentResult, DelegationRequest, DelegationResponse)
- `main_agent/tools.py` (tool functions)
- `main_agent/state.py` (MainAgentState)
