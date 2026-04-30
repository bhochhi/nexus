# F-005: Live Agent Connection & Queue Routing

## Description
When a member needs to speak with a human representative, the LiveAgent collects necessary information to route them to the correct contact center queue (Banking, Insurance, or Advice). The agent uses conversational AI to determine which queue is appropriate based on the member's stated need, then establishes a real-time connection.

## Business Value
Intelligent queue routing reduces misdirected calls and queue transfers. Instead of pressing buttons on a phone tree, the member explains their need naturally and gets routed to the right team the first time. This reduces average handle time and improves member satisfaction scores.

## User Story
As a **member**, I want to explain what I need help with and be automatically routed to the right team, so that I don't waste time being transferred between departments.

## Acceptance Criteria
- [ ] LiveAgent asks the member what they want to discuss with a live representative
- [ ] LiveAgent uses LLM to classify the member's response into a queue: Banking, Insurance, or Advice
- [ ] If the queue cannot be determined, LiveAgent asks a clarifying follow-up question
- [ ] Once the queue is identified, LiveAgent connects to the contact center via WebSocket
- [ ] Member is informed of the connection status: "Connecting you to our Banking team..."
- [ ] If the WebSocket connection fails, member is informed and offered to retry or go back
- [ ] On connection failure, the sub-agent MUST log the raw error using error color code and set its `AgentResult` status to `error`.
- [ ] If no MSR is available in the queue, member is informed they are waiting

## Scenarios

### Happy Path — Clear Queue Match
1. Orchestrator delegates to LiveAgent with summary: "Member wants to speak to someone about insurance"
2. LiveAgent: already knows the topic from summary → "I'll connect you to our Insurance team"
3. WebSocket connects to insurance queue

### Needs Clarification
1. Orchestrator delegates with summary: "Member wants to speak to someone"
2. LiveAgent: "What would you like to discuss with our team?"
3. Member: "I have questions about my retirement portfolio"
4. LiveAgent LLM classifies: → Advice queue
5. "Connecting you to our Investment Advice team..."

### Connection Failure
1. LiveAgent attempts WebSocket connection → fails
2. Sub-agent logs raw error locally with error color code, sets `AgentResult.status = "error"`, and yields back to orchestrator.
3. Sub-agent returns: "I'm having trouble connecting to our team right now. Would you like me to try again, or is there something else I can help with?"

## Out of Scope
- Automatic retry mechanism for WebSocket connection. For v1, an immediate failure with a friendly message is acceptable.

## Dependencies
- F-001: Member Greeting & Session Management
- F-003: Skill-Based Routing & Delegation

## Notes
- Available queues for v1: Banking, Insurance, Advice
- The LiveAgent should attempt to infer the queue from the orchestrator's delegation summary before asking the member again
