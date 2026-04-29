# F-004: Graceful Capability Decline

## Description
When a member requests a service that no agent currently supports, the orchestrator acknowledges the request, explains it doesn't have that capability yet, and proactively offers the services it CAN provide. The system should never leave the member in a dead end.

## Business Value
Members should feel heard even when the system can't help directly. Acknowledging the request builds trust ("I understand what you're asking"). Offering alternatives keeps the conversation productive and may still resolve the member's need through an available channel (e.g., connecting to a live agent).

## User Story
As a **member**, I want to be told clearly when a service isn't available yet and see what alternatives exist, so that I'm not left frustrated or confused.

## Acceptance Criteria
- [ ] When no agent skill matches the member's request, the system does NOT say "I don't understand"
- [ ] System acknowledges the specific request: "I understand you'd like to [member's request]"
- [ ] System explains the limitation: "I'm still learning that capability"
- [ ] System lists available services: "Here's what I can help with today: ..."
- [ ] Available services list is dynamically generated from discovered capabilities
- [ ] System invites the member to try an alternative or continue the conversation
- [ ] The interaction feels helpful, not robotic or dismissive

## Scenarios

### Happy Path
1. Member: "I want to open a new savings account"
2. Orchestrator LLM: no matching skill found
3. Response: "I understand you'd like to open a new savings account. I'm still learning that capability. Here's what I can help with today:
   • Live Agent Support — Connect to a human representative for Banking, Insurance, or Advice
   Would any of these help?"

### Member Accepts Alternative
1. Member: "OK, connect me to a banking representative then"
2. Orchestrator: matches `live_agent.connect_to_live_agent` → delegates

### Member Declines
1. Member: "No thanks, that's all"
2. Orchestrator: "No problem! Feel free to reach out anytime. Goodbye!"

## Dependencies
- F-002: Agent Discovery & Capability Awareness

## Notes
- The tone should be empathetic, not corporate. "I'm still learning" is more human than "That feature is not currently supported."
