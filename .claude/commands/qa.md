Validate the implementation against specs and report any gaps.

## Scope

$ARGUMENTS

## Instructions

1. Run `make test` and verify all tests pass
2. Run `make lint` and verify no lint errors
3. Check the relevant Gherkin specs in `specs/features/`
4. Validate each scenario is covered by at least one test:

### Validation Checklist

- [ ] **Unit tests pass**: `make test` exits 0
- [ ] **Lint clean**: `make lint` exits 0
- [ ] **Routing coverage**: Every intent in `src/nexus/intents/*.yaml` has a routing test
- [ ] **Tool coverage**: Every registered tool has an execution test
- [ ] **Session**: Multi-turn conversation preserves history correctly
- [ ] **Escalation**: Low-confidence inputs trigger the escalation path
- [ ] **Error handling**: Invalid input / tool errors are handled gracefully
- [ ] **Spec compliance**: All scenarios in `specs/features/*.feature` are satisfied

### Error Scenarios to Verify

- Invalid JSON from the router LLM response
- Unknown tool name in the registry
- Empty user message
- Missing user_id / session_id

### Output

Report as a checklist with PASS/FAIL status and any recommended follow-up actions.
