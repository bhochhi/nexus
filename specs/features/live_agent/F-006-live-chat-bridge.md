# F-006: Live Chat Bridge (Member ↔ MSR)

## Description
Once the LiveAgent connects a member to a contact center queue, it bridges real-time messages between the member and the MSR (Member Service Representative). Messages typed by the member are relayed to the MSR, and MSR responses are relayed back. The bridge stays active until the session ends.

## Business Value
Seamless real-time chat between member and human agent is the core of the live support experience. The bridge must be transparent — the member should feel like they're chatting directly with the MSR, not through a bot intermediary.

## User Story
As a **member**, I want to chat in real-time with a human representative, so that I can get help with complex issues that the AI can't handle.

## Acceptance Criteria
- [ ] Messages from the member are forwarded to the connected MSR in real-time
- [ ] Messages from the MSR are displayed to the member in real-time
- [ ] The member sees the MSR's name in the response (e.g., "MSR Alice: Hi!")
- [ ] The bridge remains active until one of the termination conditions is met
- [ ] **Termination: Member idle > 2 minutes** → auto-disconnect, notify MSR, return to orchestrator
- [ ] **Termination: MSR signals end** (e.g., `/end` command) → disconnect, return to orchestrator
- [ ] **Termination: Member requests different help** → member must disconnect first, then return to orchestrator for re-routing
- [ ] On any termination, a summary of the live session is generated
- [ ] After termination, control returns to the orchestrator: "Your live session has ended. Is there anything else I can help with?"
- [ ] The contact center WebSocket server runs as a separate process
- [ ] MSR connects to the server via a CLI console app specifying their queue and name

## Scenarios

### Happy Path — Full Chat Session
1. LiveAgent connects member to Banking queue
2. MSR Alice is available → connection established
3. Member: "I see a charge I didn't make" → relayed to Alice
4. Alice: "Let me look into that for you" → relayed to member
5. Alice: `/end` → session terminated
6. Member sees: "Your live session has ended. Is there anything else I can help with?"

### Idle Timeout
1. Member is connected to MSR
2. Member stops responding for 2 minutes
3. System auto-disconnects, notifies MSR: "Member has disconnected (idle timeout)"
4. Control returns to orchestrator

### Disconnecting
1. Member is chatting with Insurance MSR
2. Member types 'disconnect' or MSR types '/end'
3. LiveAgent detects disconnect command → ends current session
4. Returns to orchestrator → orchestrator resumes conversation

## Dependencies
- F-005: Live Agent Connection & Queue Routing

## Notes
- The CLI REPL needs to handle async I/O during the bridge phase (member can type while waiting for MSR messages)
- The contact center is a mock — 3 MSR terminals, one per queue
- Connection topology: `LiveAgent --WebSocket--> WS Server <--WebSocket-- MSR Console`
