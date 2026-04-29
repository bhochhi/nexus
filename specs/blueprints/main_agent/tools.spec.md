# Blueprint: Main Agent — Tools

## Purpose
Defines the tools the Main Agent's LLM can call via function calling. Tools are the mechanism by which the LLM takes action — delegating to sub-agents or listing capabilities. Tool schemas are auto-generated from Python type hints and docstrings.

## Implements Features
- F-003: Skill-Based Routing & Delegation
- F-004: Graceful Capability Decline (via `show_capabilities`)

## Interface Contract

### `delegate_to_agent`

The primary routing tool. The LLM calls this when a member's request matches a sub-agent's skill.

```python
@tool
def delegate_to_agent(agent_name: str, skill: str, reason: str) -> str:
    """Route member to a specialized agent.

    Call this when the member's request matches a sub-agent's capability.
    The system will generate a conversation summary, hand it to the target
    agent, and transfer control.

    Args:
        agent_name: Name of the agent to delegate to (e.g., 'live_agent')
        skill: The specific skill being requested (e.g., 'connect_to_live_agent')
        reason: Brief explanation of why this delegation is appropriate
    """
```

**Behavior:**
1. This tool is NOT directly executed by the LLM — the `delegate` graph node handles the actual delegation
2. The tool exists to give the LLM a structured way to express its routing decision
3. The tool's return value is the delegation result (sub-agent response + summary)

**Dynamic Schema:**
The `agent_name` parameter's description is dynamically enriched with discovered capabilities at startup:

```python
def build_delegate_tool(capabilities: List[AgentCapability]) -> BaseTool:
    """Build the delegate_to_agent tool with dynamic capability descriptions."""
    # Build a description that lists all available agents and their skills
    # so the LLM knows what it can delegate to
    agents_desc = []
    for cap in capabilities:
        if cap.name == "main_agent":
            continue  # Don't delegate to self
        skills = ", ".join(f"{s.name}: {s.description}" for s in cap.skills)
        agents_desc.append(f"- {cap.name} ({cap.display_name}): {skills}")

    available_agents = "\n".join(agents_desc)
    # ... create tool with enriched description
```

### `show_capabilities`

Lists all available skills across all agents in a member-friendly format.

```python
@tool
def show_capabilities() -> str:
    """List all available services across all agents.

    Call this when the member asks what you can do, what services are
    available, or similar capability inquiry questions.
    """
```

**Behavior:**
1. Formats discovered capabilities into a readable list
2. Returns the formatted string, which the LLM incorporates into its response
3. After execution, the graph loops back to `process` so the LLM can generate a natural response incorporating the capabilities

**Output Format:**
```
Available services:
• Live Agent Support — Connect to a human representative
  - connect_to_live_agent: Connect member to a human representative in Banking, Insurance, or Advice queue
```

## Tool Registration

Tools are registered with the graph at build time. The `process` node passes them to the LLM via `invoke_with_tools`:

```python
# In agent.py or graph.py
tools = build_tools(capabilities)
# Tools are passed to the LLM in the process node
response = llm.invoke_with_tools(messages, system_prompt, tools)
```

## Acceptance Criteria

- [ ] `delegate_to_agent` tool has `agent_name`, `skill`, and `reason` parameters
- [ ] `delegate_to_agent` tool description is enriched with discovered capabilities
- [ ] `show_capabilities` tool takes no parameters
- [ ] `show_capabilities` returns formatted capability list
- [ ] Tools use the `@tool` decorator from `langchain_core.tools`
- [ ] Tool schemas are auto-generated from type hints and docstrings
- [ ] Main agent does not include itself in the delegate_to_agent options
- [ ] When no agents are discovered (besides main_agent), delegate_to_agent is not offered
- [ ] Tools are built dynamically at startup using discovered capabilities

## Examples

```python
# LLM decides to delegate
tool_call = ToolCall(
    name="delegate_to_agent",
    arguments={
        "agent_name": "live_agent",
        "skill": "connect_to_live_agent",
        "reason": "Member wants to speak with human about insurance"
    }
)

# LLM decides to show capabilities
tool_call = ToolCall(
    name="show_capabilities",
    arguments={}
)
```

## Dependencies
- `langchain_core.tools` (@tool decorator)
- `core.types` (AgentCapability, Skill)
- `core.discovery` (format_capabilities)
