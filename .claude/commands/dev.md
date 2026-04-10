Implement the following feature based on the specs and architecture design.

## Task

$ARGUMENTS

## Instructions

1. Read the relevant Gherkin specs in `specs/features/` — these are the contract
2. Read any architecture design notes for this feature
3. Implement in Python 3.11+ with type hints throughout

### Implementation Checklist

- [ ] Read existing code in the affected files before modifying
- [ ] Follow existing patterns (factory, registry, protocol, partial)
- [ ] Write the implementation code
- [ ] Write unit tests in `tests/unit/`
- [ ] Write integration tests in `tests/integration/` if the feature touches the graph
- [ ] Run `make test` — all tests must pass
- [ ] Run `make lint` — no lint errors

### Key Patterns to Follow

**Graph node signature:**
```python
def node_name(state: AgentState, *, llm: BaseLLM, registry: ToolRegistry) -> dict:
    return {"field": "value"}  # partial state update
```

**Tool implementation:**
```python
class MyTool:
    name = "my_tool"
    description = "What this tool does"
    parameters = {"type": "object", "properties": {...}, "required": [...]}

    def execute(self, args: dict) -> dict:
        return {"status": "success", "data": ...}
```

**Registering tools:**
```python
def register_domain_tools(registry: ToolRegistry) -> None:
    registry.register(MyTool())
```

### Rules

- Mock external APIs — return realistic data structures
- Never hardcode AWS credentials
- YAML for intents/instructions, `.txt` for prompt templates
- Specs are source of truth — if code breaks a spec, fix the code
