"""
Billing Agent — Nexus Agent.

Handles member billing inquiries, retrieves payment details, schedules payments, and answers standard FAQs

Implements: blueprints/billing_agent/
"""
import logging
from typing import List

from core.base_agent import BaseAgent
from core.llm import LLMClient
from core.session import SessionState
from core.types import AgentResult, Message

from .tools import TOOLS, get_billing_summary, schedule_payment

logger = logging.getLogger(__name__)


class BillingAgent(BaseAgent):
    """Billing Agent agent."""

    def __init__(self, llm_client: LLMClient, session: SessionState):
        super().__init__("billing_agent", llm_client, session)
        
        self.tool_map = {
            "get_billing_summary": get_billing_summary,
            "schedule_payment": schedule_payment
        }

    def build_graph(self):
        """Billing Agent graph — minimal for now."""
        return None

    def get_tools(self) -> List:
        """Billing Agent tools."""
        return TOOLS

    def invoke(self, user_input: str) -> AgentResult:
        """Process user input, handling tool calls internally."""
        user_msg = Message(role="user", content=user_input, agent=self.agent_name)
        self.session.add_message(self.agent_name, user_msg)
        
        # We assume member_id is available in session context, but mock it if not present
        member_id = "12345" # Hardcoded for POC based on mock service
        context = f"The current member ID is: {member_id}"
        
        system_prompt = self.get_system_prompt(context)
        messages = self._get_conversation_messages()
        
        # Initial LLM call
        response = self.llm.invoke_with_tools(messages, system_prompt, self.tools)
        
        # Handle potential tool call
        if response.tool_call:
            tool_name = response.tool_call.name
            tool_args = response.tool_call.arguments
            tool_use_id = response.tool_call.tool_use_id
            
            logger.info(f"BillingAgent executing tool: {tool_name} with args {tool_args}")
            
            if tool_name in self.tool_map:
                try:
                    tool_func = self.tool_map[tool_name]
                    result_str = tool_func.invoke(tool_args)
                except Exception as e:
                    result_str = f"Error executing tool: {e}"
            else:
                result_str = f"Unknown tool: {tool_name}"
                
            tool_call_msg = Message(
                role="assistant",
                content="",
                agent=self.agent_name,
                metadata={"tool_calls": [response.tool_call]}
            )
            self.session.add_message(self.agent_name, tool_call_msg)
            
            tool_result_msg = Message(
                role="tool",
                content=result_str,
                agent=self.agent_name,
                metadata={"tool_use_id": tool_use_id}
            )
            self.session.add_message(self.agent_name, tool_result_msg)
            
            # Second LLM call to synthesize the result
            messages = self._get_conversation_messages()
            response = self.llm.invoke_with_tools(messages, system_prompt, self.tools)
            
        final_text = response.text
        
        assistant_msg = Message(
            role="assistant",
            content=final_text,
            agent=self.agent_name,
            metadata={"reasoning": response.reasoning}
        )
        self.session.add_message(self.agent_name, assistant_msg)
        
        # Yield control back to main_agent if task is complete
        if "[HANDOFF]" in final_text:
             final_text = final_text.replace("[HANDOFF]", "").strip()
             self.session.current_agent = "main_agent"
             delegation = True
        elif "return" in final_text.lower() or "help with anything else" in final_text.lower() or "main assistant" in final_text.lower():
             self.session.current_agent = "main_agent"
             delegation = True
        else:
             delegation = False
        
        return AgentResult(
            response=final_text,
            active_agent=self.agent_name,
            llm_reasoning=response.reasoning,
            state_snapshot={"current_agent": self.session.current_agent},
            delegation_occurred=delegation
        )
