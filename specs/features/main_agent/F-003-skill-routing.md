# F-003: Skill-Based Routing & Delegation

## Description
When a member expresses a need, the orchestrator (Main Agent) uses the LLM to reason about which sub-agent has the right skill to help. The LLM matches the member's request against discovered skills and delegates to the appropriate agent. On delegation, the orchestrator generates a summary of the conversation so far and hands it to the sub-agent, so the member never has to repeat themselves.

## Business Value
Intelligent routing eliminates menu-tree frustration ("Press 1 for banking, Press 2 for insurance..."). Members simply state their need in natural language, and the system routes them to the right specialist. This reduces handle time and improves member satisfaction.

## User Story
As a **member**, I want to describe what I need in my own words and be connected to the right service, so that I don't have to navigate menus or repeat my request.

## Acceptance Criteria
- [ ] Member's natural language input is analyzed by the LLM to determine intent
- [ ] LLM matches the request against all discovered agent skills
- [ ] When a match is found, control is delegated to the appropriate sub-agent
- [ ] A conversation summary is generated before delegation and passed to the sub-agent
- [ ] The sub-agent receives the summary as context (not the full conversation history)
- [ ] The sub-agent starts with its own fresh conversation history
- [ ] When the sub-agent completes its task, it generates a return summary
- [ ] Control returns to the orchestrator with the return summary
- [ ] The orchestrator can resume the conversation with its own history + return summary
- [ ] The debug panel shows which agent was selected, which skill matched, and why

## Scenarios

### Happy Path — Successful Delegation
1. Member: "I want to talk to someone about my insurance claim"
2. Orchestrator LLM reasons: matches `live_agent.connect_to_live_agent`
3. Orchestrator generates summary: "Member greeted. Wants to speak with live agent about insurance."
4. Control passes to LiveAgent with summary
5. LiveAgent begins its own conversation flow

### Return from Sub-Agent
1. LiveAgent finishes (MSR ended the chat)
2. LiveAgent generates summary: "Connected to insurance queue. MSR handled claim inquiry. Session ended by MSR."
3. Control returns to orchestrator
4. Orchestrator: "Your live agent session has ended. Is there anything else I can help with?"

### Edge Cases
- What if the LLM is uncertain between two agents? → Delegate to the best match; if confidence is very low, ask the member to clarify
- What if the sub-agent encounters an error? → Return control to orchestrator with error status + summary

## Dependencies
- F-001: Member Greeting & Session Management
- F-002: Agent Discovery & Capability Awareness

## Notes
- The LLM's routing decision is made via tool-calling, not manual classification. The discovered skills are presented as tool parameters.
- Each delegation generates exactly two summaries: one going in (from orchestrator), one coming back (from sub-agent).
