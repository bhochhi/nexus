# Blueprint: Agent Scaffolding Script

## Purpose
CLI script that creates a new agent module from standardized templates. Ensures every agent follows the same file structure, is automatically discoverable, and can be created in under 30 seconds.

## Implements Features
- F-008: Agent Scaffolding

## Interface Contract

### `scripts/create_agent.py` — CLI Entry Point

**Usage:**
```bash
python scripts/create_agent.py <agent_name> [--display-name "..."] [--description "..."]
```

**Arguments:**
| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `agent_name` | Yes | — | Snake_case name (e.g., `billing_agent`). Must be a valid Python identifier. |
| `--display-name` | No | Title-cased agent_name (e.g., `"Billing Agent"`) | Human-readable name for the agent manifest |
| `--description` | No | `"A specialized agent for {display_name} tasks."` | Description for the agent manifest |

**Behavior:**
1. Validate `agent_name` is a valid Python identifier (snake_case, no dashes)
2. Check if `agents/{agent_name}/` already exists → error if so
3. Create `agents/{agent_name}/` directory
4. Read each template from `agents/_template/`, substitute variables, write output
5. Print summary of created files
6. Exit 0 on success, exit 1 on error

**Variable Substitution:**
Templates use `{{variable}}` placeholders:
| Variable | Description | Example |
|----------|-------------|---------|
| `{{agent_name}}` | Snake_case name | `billing_agent` |
| `{{display_name}}` | Human-readable name | `Billing Agent` |
| `{{description}}` | Agent description | `Handles billing inquiries...` |
| `{{class_name}}` | PascalCase class name | `BillingAgentAgent` → `BillingAgent` |
| `{{version}}` | Default version | `1.0.0` |

**Class Name Derivation:**
- Convert `agent_name` to PascalCase
- If name ends with `_agent`, the class is just `BillingAgent` (not `BillingAgentAgent`)
- If name doesn't end with `_agent`, append `Agent`: `billing` → `BillingAgent`
- Examples: `live_agent` → `LiveAgent`, `balance_inquiry` → `BalanceInquiryAgent`

## Template Files

All templates live in `agents/_template/` with `.template` extension.

### `agent.md.template`
```markdown
---
name: {{agent_name}}
display_name: "{{display_name}}"
description: "{{description}}"
skills:
  - name: placeholder_skill
    description: "TODO: Define this agent's primary skill"
version: "{{version}}"
status: active
---

# {{display_name}}

{{description}}
```

### `persona.md.template`
```markdown
You are **{{display_name}}**, a specialized assistant within the Nexus financial services platform.

**Tone:** Professional, helpful, and focused on your area of expertise.

**Style:**
- Be clear and concise
- Use the member's context when available
- Offer to connect to a live agent when unsure

**Boundaries:**
- Stay within your area of expertise
- Never give specific financial advice
- Escalate to a live agent when appropriate
```

### `instruction.md.template`
```markdown
You are the {{display_name}} agent for the Nexus platform.

**Core Rules:**

1. **Focus:** Handle requests related to your specialty. If a request is outside your scope, explain and suggest returning to the main assistant.

2. **Reasoning:** For every member message, think about what they need. Always include your reasoning inside `<reasoning>` tags.

3. **Context:** If you received a delegation summary, use it to understand what the member has already discussed.

4. **Handoff:** When your task is complete, signal that control should return to the orchestrator.
```

### `agent.py.template`
```python
"""
{{display_name}} — Nexus Agent.

{{description}}

Implements: blueprints/{{agent_name}}/
"""
import logging
from typing import List

from core.base_agent import BaseAgent
from core.llm import LLMClient
from core.session import SessionState

logger = logging.getLogger(__name__)


class {{class_name}}(BaseAgent):
    """{{display_name}} agent."""

    def __init__(self, llm_client: LLMClient, session: SessionState):
        super().__init__("{{agent_name}}", llm_client, session)

    def build_graph(self):
        """{{display_name}} graph — minimal for now.

        TODO: Replace with LangGraph StateGraph when implementing.
        """
        return None

    def get_tools(self) -> List:
        """{{display_name}} tools.

        TODO: Add @tool-decorated functions.
        """
        return []
```

### `graph.py.template`
```python
"""
{{display_name}} — LangGraph StateGraph definition.

Implements: blueprints/{{agent_name}}/graph.spec.md
"""
from langgraph.graph import END, START, StateGraph

from .state import {{class_name}}State


def build_graph():
    """Build the {{display_name}} state graph.

    Graph: START → process → END
    """
    graph = StateGraph({{class_name}}State)

    graph.add_node("process", process_node)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)

    return graph.compile()


def process_node(state: {{class_name}}State) -> dict:
    """Process member input.

    TODO: Implement agent-specific logic.
    """
    return {"response": "", "reasoning": ""}
```

### `nodes.py.template`
```python
"""
{{display_name}} — Graph node functions.

Each node is a pure function that takes state and returns state updates.

Implements: blueprints/{{agent_name}}/nodes.spec.md
"""


def process(state: dict) -> dict:
    """Main processing node.

    TODO: Implement agent-specific processing logic.
    """
    return state
```

### `tools.py.template`
```python
"""
{{display_name}} — Tool definitions.

Tools are @tool-decorated functions whose schemas are auto-generated
from type hints and docstrings.

Implements: blueprints/{{agent_name}}/tools.spec.md
"""

# TODO: Add @tool-decorated functions for this agent.
# Example:
#
# from langchain_core.tools import tool
#
# @tool
# def example_tool(param: str) -> str:
#     """Description of what this tool does.
#
#     Args:
#         param: Description of the parameter.
#     """
#     return "result"

TOOLS: list = []
```

### `state.py.template`
```python
"""
{{display_name}} — Agent-specific LangGraph state schema.

Extends the base AgentGraphState with fields specific to this agent.
"""
from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class {{class_name}}State(TypedDict):
    """State schema for the {{display_name}} graph."""

    messages: List[Dict[str, Any]]      # Conversation messages
    system_prompt: str                   # Assembled system prompt
    tools: List                          # Available tools
    response: str                        # Final response text
    reasoning: str                       # LLM reasoning for debug
    # TODO: Add agent-specific state fields below
```

### `__init__.py.template`
```python
"""{{display_name}} agent module."""
from .agent import {{class_name}}
```

## Output Format

On success:
```
✅ Agent 'billing_agent' created at agents/billing_agent/

Files created:
  agents/billing_agent/agent.md
  agents/billing_agent/persona.md
  agents/billing_agent/instruction.md
  agents/billing_agent/agent.py
  agents/billing_agent/graph.py
  agents/billing_agent/nodes.py
  agents/billing_agent/tools.py
  agents/billing_agent/state.py
  agents/billing_agent/__init__.py

Next steps:
  1. Edit agent.md to define your agent's skills
  2. Implement your graph in graph.py
  3. Add tools in tools.py
  4. Run the app — your agent will be auto-discovered
```

On error (agent exists):
```
❌ Error: Agent 'live_agent' already exists at agents/live_agent/
```

On error (invalid name):
```
❌ Error: Agent name 'my-agent' is not a valid Python identifier. Use snake_case (e.g., 'my_agent').
```

## Acceptance Criteria

- [ ] Script creates `agents/{agent_name}/` directory with all 9 files
- [ ] All template variables are substituted correctly
- [ ] `agent.md` has valid YAML frontmatter with name, display_name, description, skills, version, status
- [ ] `agent.py` extends `BaseAgent` with correct class name
- [ ] `graph.py` has a minimal LangGraph (START → process → END)
- [ ] `tools.py` has an empty TOOLS list
- [ ] `state.py` has a TypedDict state class
- [ ] `__init__.py` exports the agent class
- [ ] Script refuses to overwrite existing agent directory
- [ ] Script validates agent_name is a valid Python identifier
- [ ] Script accepts optional --display-name and --description flags
- [ ] Default display_name is derived from agent_name (title case, underscores → spaces)
- [ ] Default description is generated from display_name
- [ ] Class name is correctly derived (PascalCase, handles `_agent` suffix)
- [ ] Newly created agent is discovered by `core.discovery.discover_agents()` on next startup
- [ ] Script prints summary of created files and next steps

## Examples

```bash
# Basic usage
python scripts/create_agent.py billing_agent

# With all options
python scripts/create_agent.py billing_agent \
  --display-name "Billing Agent" \
  --description "Handles billing inquiries, payment setup, and payment updates"

# Error case — already exists
python scripts/create_agent.py main_agent
# ❌ Error: Agent 'main_agent' already exists at agents/main_agent/

# Error case — invalid name
python scripts/create_agent.py my-agent
# ❌ Error: Agent name 'my-agent' is not a valid Python identifier.
```

## Dependencies
- F-002: Agent Discovery (created agents must be discoverable)
- `core.discovery.discover_agents()` — the created `agent.md` must conform to discovery's YAML parsing
