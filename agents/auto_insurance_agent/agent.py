"""
Auto-Insurance Agent.

Implements: blueprints/auto_insurance_agent/agent.spec.md
"""
import logging
from typing import List

from core.base_agent import BaseAgent
from core.llm import LLMClient
from core.session import SessionState
from core.types import AgentResult, Message

from .tools import TOOLS, get_policy_details, add_driver, remove_driver

logger = logging.getLogger(__name__)


class AutoInsuranceAgent(BaseAgent):
    """Auto Insurance Support agent."""

    def __init__(self, llm_client: LLMClient, session: SessionState):
        super().__init__("auto_insurance_agent", llm_client, session)
        
        # Tool function mapping for execution
        self.tool_map = {
            "get_policy_details": get_policy_details,
            "add_driver": add_driver,
            "remove_driver": remove_driver
        }

    def build_graph(self):
        """Simple agent; doesn't use a complex graph."""
        return None

    def get_tools(self) -> List:
        return TOOLS

    def invoke(self, user_input: str) -> AgentResult:
        """Process user input, handling tool calls internally."""
        # Add user message
        user_msg = Message(role="user", content=user_input, agent=self.agent_name)
        self.session.add_message(self.agent_name, user_msg)
        
        context = f"The current member ID is: {self.session.member_id}"
        system_prompt = self.get_system_prompt(context)
        messages = self._get_conversation_messages()
        
        # Initial LLM call
        response = self.llm.invoke_with_tools(messages, system_prompt, self.tools)
        
        # Handle potential tool call
        if response.tool_call:
            tool_name = response.tool_call.name
            tool_args = response.tool_call.arguments
            tool_use_id = response.tool_call.tool_use_id
            
            logger.info(f"AutoInsuranceAgent executing tool: {tool_name} with args {tool_args}")
            
            # Execute tool
            if tool_name in self.tool_map:
                try:
                    tool_func = self.tool_map[tool_name]
                    # The tool may expect kwargs matching the schema
                    result_str = tool_func.invoke(tool_args)
                except Exception as e:
                    result_str = f"Error executing tool: {e}"
            else:
                result_str = f"Unknown tool: {tool_name}"
                
            # Add tool call to history (as assistant message)
            tool_call_msg = Message(
                role="assistant",
                content="",
                agent=self.agent_name,
                metadata={"tool_calls": [response.tool_call]}
            )
            self.session.add_message(self.agent_name, tool_call_msg)
            
            # Add tool result to history
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
        
        # Add final assistant response to history
        assistant_msg = Message(
            role="assistant",
            content=final_text,
            agent=self.agent_name,
            metadata={"reasoning": response.reasoning}
        )
        self.session.add_message(self.agent_name, assistant_msg)
        
        # Supervisor Model Constraint: Yield control back to main_agent
        self.session.current_agent = "main_agent"
        
        return AgentResult(
            response=final_text,
            active_agent=self.agent_name,
            llm_reasoning=response.reasoning,
            state_snapshot={"current_agent": self.session.current_agent},
            delegation_occurred=True
        )
