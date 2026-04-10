@insurance
Feature: Insurance Claim Filing
  As an insurance policy holder
  I want to file a new claim
  So that I can get reimbursed for an incident

  Background:
    Given the user is authenticated with ID "user-001"
    And a conversation session is active

  Scenario: Successful claim filing
    When the user says "I want to file a claim"
    Then the router should classify intent as "file_claim" with confidence > 0.7
    And the domain should be "insurance"
    And the "file_claim" tool should be called
    And the response should contain a claim ID
    And the response should contain an estimated processing time

  Scenario: Check existing claim status
    When the user says "What is the status of my claim?"
    Then the router should classify intent as "check_claim_status"
    And the "check_claim_status" tool should be called
    And the response should contain the claim status
