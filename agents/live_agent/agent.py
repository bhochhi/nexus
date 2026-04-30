"""
Live Agent Support — Nexus Agent.

Connects members to live human agents in Banking, Insurance, or Investment Advice queues via real-time chat.
"""
import json
import logging
import select
import sys
import threading
import time
from typing import List

from langchain_core.tools import tool
from websockets.sync.client import connect

from core.base_agent import BaseAgent
from core.llm import LLMClient
from core.session import SessionState
from core.types import AgentResult, Message

logger = logging.getLogger(__name__)


class LiveAgent(BaseAgent):
    """Live Agent Support agent."""

    def __init__(self, llm_client: LLMClient, session: SessionState):
        super().__init__("live_agent", llm_client, session)

    def build_graph(self):
        """No complex LangGraph needed for LiveAgent; handled in `invoke` directly."""
        return None

    def get_tools(self) -> List:
        return [
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
        ]

    def invoke(self, user_input: str) -> AgentResult:
        # Add user message
        user_msg = Message(role="user", content=user_input, agent=self.agent_name)
        self.session.add_message(self.agent_name, user_msg)
        
        messages = self._get_conversation_messages()
        system_prompt = (
            "You are the Live Agent Router. "
            "Ask the user what they need help with to determine the correct queue. "
            "Once you know, call the 'connect_to_queue' tool with one of: 'banking', 'insurance', or 'advice'."
        )
        
        response = self.llm.invoke_with_tools(messages, system_prompt, self.tools)
        
        result_text = response.text
        status = "success"
        error_details = None
        
        if response.tool_call and response.tool_call.name == "connect_to_queue":
            q_name = response.tool_call.arguments.get("queue_name", "banking")
            conn_res = self._connect_to_queue(q_name)
            result_text = conn_res.get("message", "")
            if not conn_res.get("success"):
                status = "error"
                error_details = conn_res.get("error_details")
            
            # Chat is done, hand control back to orchestrator
            self.session.current_agent = "main_agent"
            
        assistant_msg = Message(
            role="assistant", 
            content=result_text, 
            agent=self.agent_name,
            metadata={"reasoning": response.reasoning}
        )
        self.session.add_message(self.agent_name, assistant_msg)
        
        return AgentResult(
            response=result_text,
            active_agent=self.agent_name,
            llm_reasoning=response.reasoning,
            state_snapshot={"current_agent": self.session.current_agent},
            delegation_occurred=False,
            status=status,
            error_details=error_details
        )

    def _connect_to_queue(self, queue_name: str) -> dict:
        """Connect the user to a live agent queue via WebSocket."""
        uri = "ws://localhost:8765"
        print(f"\n\033[93m[System]\033[0m: Connecting you to the {queue_name} queue. Please wait...")
        
        try:
            with connect(uri) as ws:
                ws.send(json.dumps({
                    "type": "register",
                    "role": "member",
                    "queue": queue_name,
                    "member_id": self.session.member_id
                }))
                
                stop_event = threading.Event()
                
                def ws_listener():
                    try:
                        for message in ws:
                            data = json.loads(message)
                            msg_type = data.get("type")
                            if msg_type == "system":
                                print(f"\n\033[93m[System]\033[0m: {data.get('content')}\n\033[92mYou:\033[0m ", end="", flush=True)
                            elif msg_type == "chat":
                                sender = data.get("sender", "Agent")
                                print(f"\n\033[94m[liveAgent:{sender}]\033[0m: {data.get('content')}\n\033[92mYou:\033[0m ", end="", flush=True)
                            elif msg_type == "disconnect":
                                print("\n\033[93m[System]\033[0m: Agent has ended the chat.\n")
                                stop_event.set()
                                break
                    except Exception:
                        stop_event.set()
                        
                t = threading.Thread(target=ws_listener, daemon=True)
                t.start()
                
                last_input_time = time.time()
                while not stop_event.is_set():
                    # Idle timeout check (2 mins)
                    if time.time() - last_input_time > 120:
                        print("\n\033[93m[System]\033[0m: Chat disconnected due to inactivity (2 minutes).")
                        try:
                            ws.send(json.dumps({"type": "disconnect"}))
                        except Exception:
                            pass
                        break
                        
                    # Non-blocking input read for UNIX systems
                    i, o, e = select.select([sys.stdin], [], [], 1.0)
                    if i:
                        line = sys.stdin.readline().strip()
                        if not line:
                            continue
                            
                        last_input_time = time.time()
                        
                        if line == "/end" or line.lower() == "disconnect":
                            try:
                                ws.send(json.dumps({"type": "disconnect"}))
                            except Exception:
                                pass
                            break
                            
                        try:
                            ws.send(json.dumps({
                                "type": "chat",
                                "content": line
                            }))
                            print("\033[92mYou:\033[0m ", end="", flush=True)
                        except Exception:
                            print("\n\033[93m[System]\033[0m: Failed to send message. Connection might be closed.")
                            break
                            
        except Exception as e:
            logger.error(f"\033[91mFailed to connect to websocket: {e}\033[0m")
            return {
                "success": False,
                "message": "I'm having trouble connecting to our team right now. Would you like me to try again, or is there something else I can help with?",
                "error_details": str(e)
            }
            
        return {
            "success": True,
            "message": "Live chat has ended. I am back to assist you. Is there anything else I can help you with?"
        }
