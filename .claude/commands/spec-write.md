Convert the following Acceptance Criteria into Gherkin specifications.

## Input

$ARGUMENTS

## Instructions

1. Write `.feature` files in `specs/features/` using Given/When/Then format
2. Each scenario should map to a single intent or conversation flow
3. Include `Background` sections for common setup (user authenticated, session active)
4. Tag scenarios appropriately: `@banking`, `@insurance`, `@faq`, `@escalation`, `@error-recovery`
5. Reference sample utterances from `src/nexus/intents/*.yaml`
6. Reference domain rules from `src/nexus/instructions/*.yaml`
7. Use descriptive filenames: `banking_balance.feature`, `insurance_claim.feature`, etc.

## Spec Format

```gherkin
@domain-tag
Feature: Feature Name
  As a [user role]
  I want to [action]
  So that [benefit]

  Background:
    Given the user is authenticated with ID "user-001"
    And a conversation session is active

  Scenario: Descriptive scenario name
    When the user says "sample utterance"
    Then the router should classify intent as "intent_name" with confidence > 0.7
    And the domain should be "domain_name"
    And the "tool_name" tool should be called
    And the response should contain [expected content]
```

Specs are the **source of truth**. Code must satisfy them.
