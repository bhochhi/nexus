# Contact Center Implementation Complete

The mock contact center infrastructure is now fully built and integrated into the `live_agent`.

## Components Built

### 1. Contact Center Server (`contact_center/server.py` & `scripts/run_contact_center.py`)
- Built an `asyncio` WebSocket server running on `ws://localhost:8765`.
- Routes connections based on roles (`member` or `msr`) and queues (`banking`, `insurance`, `advice`).
- Automatically matches waiting members with available MSRs and bridges their socket messages back and forth.

### 2. MSR Console (`contact_center/msr_console.py`)
- Created an asynchronous CLI for the human agents to join a queue and chat with members.
- Usage: `python contact_center/msr_console.py --queue banking --name "John"`
- The MSR receives streamed messages from members and can type replies. 
- Typing `/end` correctly terminates the chat and disconnects the session.

### 3. Live Agent Integration (`agents/live_agent/agent.py`)
- Enhanced the `LiveAgent` to use the LLM to determine which queue the member needs (if not already specified).
- Implemented the `connect_to_queue` tool which:
  - Connects synchronously to the WebSocket server using `websockets.sync.client`.
  - Spawns a background listener thread to stream incoming MSR messages to the console while waiting for the member's `input()`.
  - Enforces a **2-minute idle timeout**. If the member does not type anything for 2 minutes, the connection is automatically terminated.
  - Returns a graceful summary back to the `main_agent` when the chat concludes.

## How to Test the Flow

1. Open **Terminal 1** and start the WebSocket server:
   ```bash
   python scripts/run_contact_center.py
   ```

2. Open **Terminal 2** and join the banking queue as an MSR:
   ```bash
   python contact_center/msr_console.py --queue banking --name "Alice"
   ```

3. Open **Terminal 3** (your existing app REPL):
   ```bash
   python app.py
   ```
   * Ask the agent: "I'd like to speak to a human about my bank account."
   * The system will bridge you to Alice in Terminal 2. Chat back and forth!
   * Type `/end` from the MSR console or let the member wait 2 minutes to test disconnects.
