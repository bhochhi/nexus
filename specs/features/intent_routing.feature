@routing
Feature: Intent Routing
  As the Nexus conversational agent
  I want to correctly route user messages to the right domain
  So that users get accurate, domain-specific responses

  Background:
    Given the conversation agent is initialized
    And all intents are loaded from YAML definitions

  Scenario: Route banking messages to banking domain
    When the user says "What is my balance?"
    Then the intent should be "check_balance"
    And the domain should be "banking"
    And the confidence should be > 0.7

  Scenario: Route insurance messages to insurance domain
    When the user says "I want to file a claim"
    Then the intent should be "file_claim"
    And the domain should be "insurance"
    And the confidence should be > 0.7

  Scenario: Route FAQ messages to faq domain
    When the user says "What are your hours?"
    Then the intent should be "hours_of_operation"
    And the domain should be "faq"

  Scenario: Low confidence triggers escalation
    When the user says "asjdfklasdjf"
    Then the confidence should be < 0.7
    And the domain should be "escalation"
    And the user should be informed about human agent transfer
