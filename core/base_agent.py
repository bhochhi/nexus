"""
Nexus — Abstract base agent.

All agents extend BaseAgent. Provides: spec file loading (persona.md,
instruction.md), system prompt assembly, LangGraph pattern, and the
invoke interface.

Implements: blueprints/core/base_agent.spec.md
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from langchain_core.tools import tool
from core.llm import LLMClient
from core.session import SessionState
from core.types import AgentResult, Message

logger = logging.getLogger(__name__)


from pydantic import BaseModel, Field

class YieldControlArgs(BaseModel):
    final_message: str = Field(description="The final message or answer to provide to the user before yielding control.")
    status: str = Field(description="The status of the handoff: 'complete' for successful fulfillment, or 'error' for unrecoverable errors.")

@tool("yield_control", args_schema=YieldControlArgs)
def yield_control(final_message: str, status: str) -> str:
    """Yields control of the conversation back to the main orchestrator agent. Call this ONLY when your specific task is completely finished."""
    return f"Control yielded with status: {status}"


class BaseAgent(ABC):
    """Abstract base class for all Nexus agents."""

    def __init__(self, agent_name: str, llm_client: LLMClient, session: SessionState):
        self.agent_name = agent_name
        self.llm = llm_client
        self.session = session

        # Determine agent module directory
        self.module_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "agents",
            agent_name,
        )

        # Load spec files
        self.persona = self._load_md("persona.md")
        self.instructions = self._load_md("instruction.md")

        # Initialize tools and graph
        self.tools = list(self.get_tools())
        if self.agent_name != "main_agent":
            self.tools.append(yield_control)
        self.graph = self.build_graph()

    def _load_md(self, filename: str) -> str:
        """Read a markdown file from the agent's module directory."""
        filepath = os.path.join(self.module_dir, filename)
        try:
            with open(filepath, "r") as f:
                return f.read()
        except (IOError, OSError):
            logger.debug(f"Optional file not found: {filepath}")
            return ""

    def get_system_prompt(self, additional_context: str = "") -> str:
        """Combine persona + instructions + context into a single system prompt."""
        parts = []

        if self.persona:
            parts.append(f"## Persona\n{self.persona}")
        if self.instructions:
            parts.append(f"## Instructions\n{self.instructions}")
        if additional_context:
            parts.append(f"## Context\n{additional_context}")
            
        if self.agent_name != "main_agent":
            parts.append(
                "## Supervisor Handoff (CRITICAL RULE)\n"
                "You are a specialized sub-agent. Your ONLY job is to perform the specific task you were delegated for, and then IMMEDIATELY return control.\n"
                "1. If you need clarification to complete the task (e.g., 'which account?'), you may respond with a normal text message.\n"
                "2. If you have successfully executed the task, answered the user's question, OR if the user asks a question outside your specific domain, your task is COMPLETE.\n"
                "3. When your task is COMPLETE, you MUST NOT ask 'Is there anything else I can help with?' or offer further assistance. You MUST immediately call the `yield_control` tool.\n"
                "4. You MUST provide the `status` argument to `yield_control`: use 'complete' for successful fulfillment, or 'error' if you encountered an unrecoverable error.\n"
                "5. DO NOT mention the 'main assistant', 'main orchestrator', or 'returning control' to the user. Provide your final answer smoothly.\n"
                "Failure to call `yield_control` when the task is done will break the system."
            )

        return "\n\n".join(parts)

    @abstractmethod
    def build_graph(self):
        """Each agent defines its own LangGraph StateGraph."""
        ...

    @abstractmethod
    def get_tools(self) -> List:
        """Each agent returns its list of tools."""
        ...

    def invoke(self, user_input: str) -> AgentResult:
        """Process user input and return a result.

        1. Add user message to this agent's conversation history
        2. Build system prompt with delegation context
        3. Call LLM
        4. Add assistant response to history
        5. Return AgentResult
        """
        # Add user message to this agent's history
        user_msg = Message(role="user", content=user_input, agent=self.agent_name)
        self.session.add_message(self.agent_name, user_msg)

        # Build system prompt with delegation context
        delegation_context = self._get_delegation_context()
        system_prompt = self.get_system_prompt(delegation_context)

        # Get conversation messages for this agent
        messages = self._get_conversation_messages()

        delegation_occurred = False
        response_text = ""
        final_reasoning = ""

        # Call LLM
        if self.tools:
            max_iterations = 5
            for _ in range(max_iterations):
                response = self.llm.invoke_with_tools(messages, system_prompt, self.tools)
                
                if response.tool_call:
                    tool_name = response.tool_call.name
                    tool_args = response.tool_call.arguments
                    tool_use_id = response.tool_call.tool_use_id
                    
                    if tool_name == "yield_control":
                        self.session.current_agent = "main_agent"
                        delegation_occurred = True
                        
                        # Extract the message from the tool arguments
                        response_text = tool_args.get("final_message", response.text)
                        final_reasoning = response.reasoning
                        
                        # Extract the status
                        handoff_status = tool_args.get("status", "complete")
                        
                        tool_call_msg = Message(
                            role="assistant",
                            content=response_text,
                            agent=self.agent_name,
                            metadata={"tool_calls": [response.tool_call]}
                        )
                        self.session.add_message(self.agent_name, tool_call_msg)
                        
                        tool_result_msg = Message(
                            role="tool",
                            content=f"Control yielded with status: {handoff_status}",
                            agent=self.agent_name,
                            metadata={"tool_use_id": tool_use_id}
                        )
                        self.session.add_message(self.agent_name, tool_result_msg)
                        
                        return AgentResult(
                            response=response_text,
                            active_agent=self.agent_name,
                            llm_reasoning=final_reasoning,
                            state_snapshot={"current_agent": self.session.current_agent, "context": self.session.context},
                            delegation_occurred=delegation_occurred,
                            status=handoff_status
                        )
                    
                    logger.info(f"[{self.agent_name}] executing tool: {tool_name}")
                    tool_func = next((t for t in self.tools if t.name == tool_name), None)
                    if tool_func:
                        try:
                            tool_result = tool_func.invoke(tool_args)
                        except Exception as e:
                            tool_result = f"Error executing tool: {e}"
                    else:
                        tool_result = f"Unknown tool: {tool_name}"
                        
                    tool_call_msg = Message(
                        role="assistant",
                        content=response.text,
                        agent=self.agent_name,
                        metadata={"tool_calls": [response.tool_call]}
                    )
                    self.session.add_message(self.agent_name, tool_call_msg)
                    
                    tool_result_msg = Message(
                        role="tool",
                        content=str(tool_result),
                        agent=self.agent_name,
                        metadata={"tool_use_id": tool_use_id}
                    )
                    self.session.add_message(self.agent_name, tool_result_msg)
                    continue
                else:
                    response_text = response.text
                    final_reasoning = response.reasoning
                    
                    assistant_msg = Message(
                        role="assistant",
                        content=response_text,
                        agent=self.agent_name,
                        metadata={"reasoning": final_reasoning},
                    )
                    self.session.add_message(self.agent_name, assistant_msg)
                    break
        else:
            response = self.llm.invoke(messages, system_prompt)
            response_text = response.text
            final_reasoning = response.reasoning
            
            assistant_msg = Message(
                role="assistant",
                content=response_text,
                agent=self.agent_name,
                metadata={"reasoning": final_reasoning},
            )
            self.session.add_message(self.agent_name, assistant_msg)

        # Build state snapshot for debug panel
        state_snapshot = {
            "current_agent": self.session.current_agent,
            "context": self.session.context,
        }

        return AgentResult(
            response=response_text,
            active_agent=self.agent_name,
            llm_reasoning=final_reasoning,
            state_snapshot=state_snapshot,
            delegation_occurred=delegation_occurred,
        )

    def _get_conversation_messages(self) -> List[Message]:
        """Retrieve this agent's conversation history from session."""
        agent_state = self.session.get_agent_state(self.agent_name)
        return agent_state.conversation_history

    def _get_delegation_context(self) -> str:
        """Get delegation summary context if present."""
        agent_state = self.session.get_agent_state(self.agent_name)
        if agent_state.delegation_summary:
            return f"Previous agent summary: {agent_state.delegation_summary}"
        return ""
