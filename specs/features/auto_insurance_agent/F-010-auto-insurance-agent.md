# F-010: Auto-Insurance Agent

## Description
The Auto-Insurance Agent is a specialized virtual assistant within the Nexus platform designed to handle auto insurance-related queries. In its initial iteration, the agent serves as an informational resource that can answer general Auto Insurance FAQs. Additionally, it can retrieve specific policy details for an authenticated member (deductibles, premiums, expiry dates, current drivers) and perform basic policy servicing tasks, specifically adding and removing drivers from the policy.

## Business Value
- **Call Deflection:** Reduces the burden on human Member Service Representatives (MSRs) by autonomously handling routine policy inquiries and driver updates.
- **24/7 Availability:** Provides members with instant, round-the-clock access to their policy details and basic servicing capabilities.

## User Story
- As a Member, I want to ask general questions about auto insurance so that I can better understand how it works.
- As a Member, I want to check my auto policy details (premium, deductible, drivers, expiry) so that I know what coverage I currently have.
- As a Member, I want to be able to add or remove a driver from my active auto policy without waiting for a human agent.

## Acceptance Criteria
- [ ] The agent accurately answers general auto insurance FAQs.
- [ ] The agent can retrieve and clearly present the user's active policy details, specifically: deductibles, premiums, expiry dates, and the list of current drivers.
- [ ] The agent can successfully execute a request to add a new driver to the policy.
- [ ] The agent can successfully execute a request to remove an existing driver from the policy.
- [ ] The agent refuses to perform tasks outside its scope (e.g., generating new quotes, starting claims) and politely explains its limitations.
- [ ] Upon completing its task, or if it encounters an error/unsupported request, the agent always hands control back to the `Main Agent` with a clear summary of what occurred.

## Scenarios

### Happy Path: Policy Lookup & Driver Update
1. User asks the Main Agent, "Who is currently driving on my auto policy?"
2. Main Agent routes the request to the Auto-Insurance Agent.
3. Auto-Insurance Agent uses a tool (passing the `member_id`) to fetch the mock policy details.
4. Auto-Insurance Agent replies with the list of current drivers.
5. User says, "Please add John Doe as a driver."
6. Auto-Insurance Agent uses the driver update tool to add John Doe in-memory.
7. Auto-Insurance Agent confirms the addition.
8. Auto-Insurance Agent hands control back to the Main Agent with a summary: "Provided current drivers to user, then successfully added John Doe to the policy."

### Edge Cases
- **Missing Member ID:** What happens if the agent needs to look up a policy but the `member_id` is not available in the session state? (Agent should ask Main Agent for clarification or fallback).
- **Removing Only Driver:** What happens if the user tries to remove the primary/only driver on the policy? (Tool should reject the change).
- **Out of Scope Request:** User asks to file a claim. Agent informs them it cannot do that and returns to the Main Agent so the Main Agent can route them to the Live Agent if needed.

## Dependencies
- Requires the Core Nexus framework and `Main Agent` router (F-001, Phase 1 Core Infrastructure).

## Notes & Implementation Constraints
- **Routing Constraint:** Strict **Supervisor Model**. The Auto-Insurance Agent must *never* route directly to another sub-agent or the `LiveAgent`. It must always return its execution summary back to the `Main Agent`.
- **Mock Data Constraint:** For this phase, all data retrieval and updates should be mocked via tool calling. 
  - Create a tool that takes `member_id` and returns a mock JSON payload containing policy details (deductibles, premiums, expiry, drivers).
  - Driver additions and removals should be handled by an in-memory update to this mock data payload during the active session.

## Out of Scope (Phase 2+)
The following features are explicitly out of scope for Phase 1 and must not be built into the initial technical blueprint:
- **PII/Security Handling:** Secure collection and masking of highly sensitive data (SSN, VIN, Driver's License numbers).
- **Quote Generation:** Creating or binding new policies.
- **Claims Initiation:** First Notice of Loss (FNOL) processing.
- **Document Generation:** Generating and sending physical/digital proof of insurance or ID cards.
- **Compliance "Advice":** The agent must remain strictly informational and not advise members on what coverage limits they "should" buy.
