"""
MSR Console - Connects human agents to the Contact Center.
"""
import argparse
import asyncio
import json
import sys
import websockets

async def read_from_ws(ws):
    try:
        async for message in ws:
            data = json.loads(message)
            msg_type = data.get("type")
            if msg_type == "system":
                print(f"\n[SYSTEM] {data['content']}\nYou: ", end="", flush=True)
            elif msg_type == "chat":
                print(f"\n[Member] {data['content']}\nYou: ", end="", flush=True)
            elif msg_type == "disconnect":
                print("\n[SYSTEM] Chat ended by member. Exiting.")
                sys.exit(0)
    except websockets.exceptions.ConnectionClosed:
        print("\n[SYSTEM] Connection to server lost.")
        sys.exit(1)

async def read_from_stdin(ws):
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        line = line.strip()
        if not line:
            continue
        if line == "/end":
            await ws.send(json.dumps({"type": "disconnect"}))
            print("Chat ended. Exiting.")
            sys.exit(0)
            
        await ws.send(json.dumps({
            "type": "chat",
            "content": line
        }))
        print("You: ", end="", flush=True)

async def main():
    parser = argparse.ArgumentParser(description="MSR Console")
    parser.add_argument("--queue", required=True, choices=["banking", "insurance", "advice"])
    parser.add_argument("--name", required=True, help="Agent Name")
    args = parser.parse_args()

    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as ws:
            # Register
            await ws.send(json.dumps({
                "type": "register",
                "role": "msr",
                "queue": args.queue,
                "name": args.name
            }))
            
            # Start tasks
            print(f"Connecting to {args.queue} queue as {args.name}...")
            
            task1 = asyncio.create_task(read_from_ws(ws))
            task2 = asyncio.create_task(read_from_stdin(ws))
            
            await asyncio.gather(task1, task2)
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting.")
