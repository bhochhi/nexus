# F-007: Debug Transparency Panel

## Description
Every turn of the conversation displays a debug panel below the agent's response showing the active agent, the LLM's tool call (if any), and a snapshot of the current session state. This transparency is critical for v1 development, learning, and troubleshooting.

## Business Value
Observability accelerates development. Being able to see exactly WHY the system made a routing decision, WHAT tool it called, and WHAT the current state looks like eliminates guesswork during testing and debugging. This also builds confidence in the system's reasoning.

## User Story
As a **developer**, I want to see the LLM's reasoning and current state after every conversation turn, so that I can understand, debug, and improve the system's behavior.

## Acceptance Criteria
- [ ] Every turn displays the agent's response followed by a debug panel
- [ ] Debug panel shows: active agent name (and delegation direction if applicable)
- [ ] Debug panel shows: tool call name and arguments (if LLM called a tool)
- [ ] Debug panel shows: current session state snapshot (current_agent, context)
- [ ] Debug panel is visually distinct from the conversation (box-drawn border)
- [ ] Debug panel can be toggled on/off (e.g., `--debug` flag) — on by default for v1
- [ ] Basic Python logging captures all LLM calls, tool executions, and state changes
- [ ] Log level is configurable (DEBUG/INFO/WARNING)

## Scenarios

### Example Output
```
You: I want to talk to someone about my insurance

Nexus: I'll connect you with our live agent support.

┌─ Debug ──────────────────────────────────────────┐
│ Agent:     main_agent → live_agent (delegating)  │
│ Tool Call: delegate_to_agent(                    │
│              agent="live_agent",                  │
│              skill="connect_to_live_agent",       │
│              reason="Member wants to speak        │
│                      with human about insurance") │
│ State:     {current_agent: "live_agent",          │
│             context: {topic: "insurance"}}         │
└──────────────────────────────────────────────────┘
```

### No Tool Call (Direct Response)
```
You: Hello!

Nexus: Welcome to Nexus! Here's what I can help with today: ...

┌─ Debug ──────────────────────────────────────────┐
│ Agent:     main_agent                            │
│ Tool Call: none (direct response)                │
│ State:     {current_agent: "main_agent",          │
│             context: {}}                           │
└──────────────────────────────────────────────────┘
```

## Dependencies
- F-001: Member Greeting & Session Management

## Notes
- v1: debug panel is always shown. Future: web UI with collapsible debug sections.
- Logging uses Python's built-in `logging` module. Future: structured logging with `structlog`.
