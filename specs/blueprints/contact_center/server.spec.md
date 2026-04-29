# Blueprint: Contact Center WebSocket Server

## Purpose
A mock contact center built with `asyncio` and `websockets` to facilitate real-time chat between Members (routed by `LiveAgent`) and human Member Service Representatives (MSRs).

## Implements Features
- F-006: Live Chat Bridge (Member ↔ MSR)

## Interface Contract

### `contact_center/server.py`
- Input: WebSocket connections on `ws://localhost:8765`
- Output: Broadcasts payload mappings between paired MSR and Member websockets.
- Behavior: 
  - Maintains queues for `banking`, `insurance`, and `advice`.
  - Maintains `waiting_members` lists for each queue.
  - Matches connecting MSRs to waiting Members.

### `contact_center/msr_console.py`
- Input: `sys.stdin` for typing messages and WebSocket incoming messages.
- Output: Displays messages to the terminal.
- Behavior:
  - Registers the user with a specific queue.
  - Exits gracefully on `/end`.

## Data Models
### WebSocket Payload Protocol
```python
{
    "type": "register",   # 'register', 'chat', 'system', 'disconnect'
    "role": "msr",        # 'member', 'msr'
    "queue": "banking",   
    "name": "Alice"       # Only for MSR
}
```

## Acceptance Criteria
- [x] Initializes an `asyncio` loop running the WebSocket server.
- [x] Handles ungraceful socket disconnections using `websockets.exceptions.ConnectionClosed`.
- [x] Connects MSR CLI properly and relays messages cleanly in both directions.

## Dependencies
- `websockets`
- `asyncio`
