Design the system architecture for the following feature or requirement.

## Requirement

$ARGUMENTS

## Instructions

1. Read the relevant Gherkin specs in `specs/features/` for this feature
2. Design within the existing LangGraph StateGraph topology:
   ```
   entry → router → [banking | insurance | faq | escalation] → tool_execute → respond → END
   ```
3. For each new component, specify:
   - **What**: Purpose and responsibility
   - **Where**: File path in the project structure
   - **Interface**: Function signature or class protocol
   - **State changes**: Which `AgentState` fields it reads/writes
   - **Edges**: How it connects to existing nodes

4. Follow these patterns:
   - Factory pattern for LLM providers (`src/nexus/llm/factory.py`)
   - Registry pattern for tools (`src/nexus/tools/registry.py`)
   - Protocol for tool interface (`src/nexus/tools/base.py`)
   - `functools.partial` for dependency injection into graph nodes
   - State-driven: all data flows through `AgentState` TypedDict

5. Consider:
   - Can this be done by adding a tool to an existing domain handler?
   - Does it require a new graph node or just extending an existing one?
   - What new `AgentState` fields are needed (if any)?
   - What are the testability implications?

6. Output a design document that the Dev agent can implement directly
