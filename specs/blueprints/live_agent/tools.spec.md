# Blueprint: Live Agent Tools

## Purpose
Defines the tools available to the `LiveAgent` LLM for queue routing and real-time contact center bridging.

## Implements Features
- F-005: Live Agent Connection & Queue Routing
- F-006: Live Chat Bridge (Member ↔ MSR)

## Interface Contract

### `connect_to_queue`
- Input: `queue_name` (string: banking, insurance, advice)
- Output: `dict` containing `success` (boolean), `message` (string: summary or fallback message), and optionally `error_details` (string).
- Behavior:
  - Connects to `ws://localhost:8765`.
  - Sends a registration message: `{"type": "register", "role": "member", "queue": queue_name, "member_id": self.session.member_id}`.
  - Spawns a daemon thread to read incoming messages from the WebSocket and print to `sys.stdout`.
  - Enters a synchronous loop utilizing `select.select` on `sys.stdin` to read member inputs non-blockingly.
  - Enforces a 120-second idle timeout.
  - Terminates gracefully if the member types `disconnect` or `/end`.
  - If the connection fails, logs the raw error to the console in red and returns an error dictionary.
  - Disconnects the socket and returns a summary message on success.

## Data Models
```python
# Tool Schema Definition (OpenAI Native or bare Bedrock converted by core/llm.py)
{
    "name": "connect_to_queue",
    "description": "Connect the user to a live agent queue (banking, insurance, advice).",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "queue_name": {
                    "type": "string",
                    "description": "The queue to connect to (banking, insurance, advice)"
                }
            },
            "required": ["queue_name"]
        }
    }
}
```

## Acceptance Criteria
- [x] Accepts exactly one required argument: `queue_name`.
- [x] Connects to the local WebSocket server successfully.
- [x] Manages concurrent reading/writing via daemon threads and `select` module.
- [x] Times out automatically after 2 minutes of member inactivity.

## Dependencies
- `websockets.sync.client.connect`
- `select` module
- `threading` module
