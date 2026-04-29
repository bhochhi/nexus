# F-001: Member Greeting & Session Management

## Description
When a member connects to Nexus, the system recognizes whether they are new or returning and greets them appropriately. Each member has a unique, persistent session that tracks their conversation state across multiple interactions and agent handoffs.

## Business Value
First impressions shape member trust. A personalized greeting ("Welcome back!") signals that the system remembers the member, while a fresh welcome for new members sets expectations about what services are available. Session persistence ensures members don't have to repeat themselves.

## User Story
As a **member**, I want to be greeted when I connect and have my conversation remembered across turns, so that I feel recognized and don't have to repeat context.

## Acceptance Criteria
- [ ] New member receives a welcome greeting listing available services
- [ ] Returning member (same member_id) receives a "welcome back" greeting
- [ ] Each member has a unique session identified by member_id
- [ ] Session persists across multiple conversation turns
- [ ] Member can start a session by providing a member_id (CLI argument for v1)
- [ ] Default member_id is used when none is provided
- [ ] Session tracks which agent is currently handling the member
- [ ] Each agent maintains its own isolated conversation history
- [ ] When control passes between agents, a summary of the prior conversation is generated and handed off

## Scenarios

### Happy Path — New Member
1. Member starts the app with `python app.py --member-id M123`
2. System creates a new session for M123
3. Main Agent greets: "Welcome to Nexus! I'm here to help with banking, insurance, and investment services. Here's what I can do today: ..."
4. Member responds with their need

### Happy Path — Returning Member
1. Member starts the app with `python app.py --member-id M123` (same ID as before)
2. System finds existing session for M123
3. Main Agent greets: "Welcome back! How can I help you today?"

### Edge Cases
- What if member_id is not provided? → Use default "member_default"
- What if session data is corrupted? → Create a fresh session, log warning

## Dependencies
- None (this is the foundation)

## Notes
- v1 sessions are in-memory (lost on app restart). Future: persist to database.
- The greeting message should include dynamically discovered capabilities (depends on F-002).
