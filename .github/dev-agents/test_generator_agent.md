# Test Generator Agent

## Goal
Generate conversation-level test cases that validate the Nexus chatbot end-to-end.

## Output
- `tests/conversation_tests.yaml` – intent-level test scenarios
- `tests/load_tests.yaml` – concurrency and throughput tests

## Test Format
```yaml
tests:
  - input: "<user utterance>"
    expected_intent: <intent_name>
    expected_skill: <skill_name>   # optional
    context: {}                    # optional session context
```

## Rules
- Cover at least one test per intent (30+ total)
- Include edge cases: ambiguous input, missing slots, escalation triggers
- Tests must be deterministic and not rely on live AWS services
