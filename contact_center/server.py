"""
Contact Center WebSocket Server.
Hub that connects Members (from app.py) to MSRs (from msr_console.py).
"""
import asyncio
import json
import logging
import websockets
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("contact_center")

# State
queues: Dict[str, List[websockets.WebSocketServerProtocol]] = {
    "banking": [],
    "insurance": [],
    "advice": []
}

waiting_members: Dict[str, List[Dict]] = {
    "banking": [],
    "insurance": [],
    "advice": []
}

# Map of active chats: ws -> ws
active_chats: Dict[websockets.WebSocketServerProtocol, websockets.WebSocketServerProtocol] = {}

async def register(ws, data):
    role = data.get("role")
    queue = data.get("queue")
    name = data.get("name", "Unknown")
    
    if queue not in queues:
        await ws.send(json.dumps({"type": "error", "message": f"Unknown queue {queue}"}))
        return

    if role == "msr":
        queues[queue].append(ws)
        ws.msr_name = name
        ws.queue = queue
        logger.info(f"MSR {name} joined {queue} queue.")
        await ws.send(json.dumps({"type": "system", "content": f"Registered to {queue} queue. Waiting for members..."}))
        await match_member(queue)
        
    elif role == "member":
        member_id = data.get("member_id", "Unknown")
        ws.member_id = member_id
        ws.queue = queue
        logger.info(f"Member {member_id} joined {queue} queue.")
        waiting_members[queue].append({"ws": ws, "member_id": member_id})
        await ws.send(json.dumps({"type": "system", "content": f"Joined {queue} queue. Waiting for an available agent..."}))
        await match_member(queue)

async def match_member(queue):
    if queues[queue] and waiting_members[queue]:
        msr_ws = queues[queue].pop(0)
        member_data = waiting_members[queue].pop(0)
        member_ws = member_data["ws"]
        
        active_chats[msr_ws] = member_ws
        active_chats[member_ws] = msr_ws
        
        await msr_ws.send(json.dumps({"type": "system", "content": f"Connected to Member {member_ws.member_id}!"}))
        await member_ws.send(json.dumps({"type": "system", "content": f"Connected to Agent {msr_ws.msr_name}!"}))
        logger.info(f"Matched MSR {msr_ws.msr_name} with Member {member_ws.member_id}")

async def handle_disconnect(ws):
    if hasattr(ws, "queue"):
        queue = ws.queue
        if ws in queues[queue]:
            queues[queue].remove(ws)
        
        # Remove from waiting members if present
        waiting_members[queue] = [m for m in waiting_members[queue] if m["ws"] != ws]
        
    if ws in active_chats:
        partner_ws = active_chats[ws]
        del active_chats[ws]
        if partner_ws in active_chats:
            del active_chats[partner_ws]
            
            # Notify partner
            try:
                await partner_ws.send(json.dumps({"type": "system", "content": "The other party has disconnected."}))
                await partner_ws.send(json.dumps({"type": "disconnect"}))
            except websockets.exceptions.ConnectionClosed:
                pass

async def handler(ws, path=""):
    try:
        async for message in ws:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "register":
                await register(ws, data)
            elif msg_type == "chat":
                if ws in active_chats:
                    partner_ws = active_chats[ws]
                    content = data.get("content", "")
                    sender_name = getattr(ws, "msr_name", getattr(ws, "member_id", "Unknown"))
                    await partner_ws.send(json.dumps({
                        "type": "chat",
                        "sender": sender_name,
                        "content": content
                    }))
            elif msg_type == "disconnect":
                await handle_disconnect(ws)
                await ws.close()
                break
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await handle_disconnect(ws)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        logger.info("WebSocket Contact Center started on ws://localhost:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
