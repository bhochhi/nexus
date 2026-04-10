Analyze the following feature request and produce structured Acceptance Criteria.

## Feature Request

$ARGUMENTS

## Instructions

1. Read the feature request above
2. Reference existing intents in `src/nexus/intents/*.yaml` and domain rules in `src/nexus/instructions/*.yaml`
3. Output ACs in this format:

```
AC-{N}: Given [precondition], the system should [behavior] so that [outcome]
```

4. Prioritize by business value (core banking/insurance operations first)
5. Include ACs for: routing, tool execution, response formatting, error handling, and edge cases
6. After writing ACs, pass them to the Spec Writer by running `/project:spec-write` with the ACs as input
