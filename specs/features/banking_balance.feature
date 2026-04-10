@banking
Feature: Account Balance Check
  As a banking customer
  I want to check my account balance
  So that I can monitor my finances

  Background:
    Given the user is authenticated with ID "user-001"
    And a conversation session is active

  Scenario: Successful balance check
    When the user says "What is my balance?"
    Then the router should classify intent as "check_balance" with confidence > 0.7
    And the domain should be "banking"
    And the "get_account_balance" tool should be called
    And the response should contain the balance amount
    And the response should not contain raw JSON

  Scenario: Balance check with account type
    When the user says "How much money do I have in savings?"
    Then the router should classify intent as "check_balance"
    And the tool should be called with account_type "savings"
