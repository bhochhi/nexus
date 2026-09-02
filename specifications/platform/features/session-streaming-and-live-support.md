---
apiVersion: nexus.platform/v1
kind: PlatformFeature
metadata: {id: PF-SESSION-STREAMING-LIVE-SUPPORT, name: session-streaming-and-live-support, status: approved, version: 1.0.0, owner: Agentic Conversation Platform}
enforces: [INV-STATE-002, INV-RESPONSE-001, INV-OBS-002]
---
# Session streaming and live support
## Purpose
Deliver replayable conversation events and governed transfer to a human channel with minimized context.
## Required behavior
- Stream typed events in order and replay missed events after reconnect.
- Expire inactive member sessions without treating protocol keepalive as member activity.
- Transfer only a concise reason, relevant progress, and permitted context.
- Let a waiting member cancel and return to the virtual experience.
## Acceptance criteria
- **AC-PF-SESSION-001 — Replay continuity:** A reconnect resumes from the last acknowledged event without duplicating an executed action.
- **AC-PF-SESSION-002 — Terminal expiry:** Session expiry is explicit and closes the member channel while retaining required audit history.
- **AC-PF-HANDOFF-001 — Minimized transfer:** Human support receives only the governed summary and routing fields.
- **AC-PF-HANDOFF-002 — Safe cancellation:** Cancelling a pending handoff returns control without losing eligible resumable work.
## Examples
A member requests human assistance, receives a queue status, cancels while waiting, and continues in the virtual channel.
## Edge cases
- Multiple clients share a session; the handoff channel disconnects; expiry races with a streamed result.
## Verification
- `tests/test_streaming.py`, `tests/test_ui_client.py`, `tests/test_live_support.py`.
