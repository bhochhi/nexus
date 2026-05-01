"""
Main Agent — Nexus Orchestrator.

Greets members, discovers capabilities, classifies intent via LLM with tools,
delegates to sub-agents, and handles graceful decline.

Features: F-001 (Greeting), F-003 (Routing), F-004 (Graceful Decline)
Implements: blueprints/main_agent/graph.spec.md, tools.spec.md, nodes.spec.md
"""
import logging
import os
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from core.base_agent import BaseAgent
from core.discovery import format_capabilities
from core.llm import LLMClient
from core.session import SessionState
from core.types import AgentCapability, AgentResult, Message

from .graph import build_main_agent_graph
from .state import MainAgentState
from .tools import build_tools

logger = logging.getLogger(__name__)


class MainAgent(BaseAgent):
    """The orchestrator agent for the Nexus platform.

    Uses a LangGraph StateGraph with tool-calling for intent classification
    and delegation to sub-agents.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        session: SessionState,
        capabilities: List[AgentCapability],
        agent_discovery_service,
    ):
        self.capabilities = capabilities
        self._capabilities_text = format_capabilities(capabilities)
        self.agent_discovery_service = agent_discovery_service

        # Build tools from discovered capabilities
        self._tools_list, self._tools_map = build_tools(capabilities)

        super().__init__("main_agent", llm_client, session)

    def build_graph(self):
        """Build the Main Agent LangGraph.

        Graph: START → process → [route] → delegate/respond → END
        """
        return build_main_agent_graph(
            process_node=self._process_node,
            delegate_node=self._delegate_node,
            respond_node=self._respond_node,
            route_fn=self._route_after_process,
        )

    def get_tools(self) -> List:
        """Return tools for the orchestrator."""
        return self._tools_list

    def invoke(self, user_input: str) -> AgentResult:
        """Process user input through the orchestrator graph."""
        # Route to active sub-agent if delegation is in progress
        if self.session.current_agent != self.agent_name:
            try:
                sub_agent_name = self.session.current_agent
                target_agent = self._create_agent(sub_agent_name)
                result = target_agent.invoke(user_input)
                
                # Enforce handoff: check if sub-agent yielded control
                result_status = getattr(result, "status", "success")
                if result_status in ("complete", "error"):
                    logger.info(f"Sub-agent {sub_agent_name} yielded control with status {result_status}.")
                    
                    # Track failure for anti-looping
                    if result_status == "error":
                        logger.warning(f"Sub-agent {sub_agent_name} returned error status. Blacklisting.")
                        if "failed_delegations" not in self.session.context:
                            self.session.context["failed_delegations"] = {}
                        self.session.context["failed_delegations"][sub_agent_name] = time.time()
                    
                    # Return control to orchestrator
                    self.session.current_agent = self.agent_name
                
                return result
            except Exception as e:
                logger.error(f"Routing to {self.session.current_agent} failed: {e}")
                self.session.current_agent = self.agent_name
                # Fall through to let main_agent handle it if recovery is needed

        # Add user message to this agent's history
        user_msg = Message(role="user", content=user_input, agent=self.agent_name)
        self.session.add_message(self.agent_name, user_msg)

        # Capture session state at start of turn for accurate debug snapshot
        was_new_session = self.session.is_new_session

        # Build context
        context_parts = []
        if self.session.is_new_session:
            context_parts.append(
                "This is a NEW member session. Greet them warmly and list available capabilities."
            )
            self.session.is_new_session = False
        else:
            context_parts.append("This is a RETURNING member in an active session.")

        delegation = self._get_delegation_context()
        if delegation:
            context_parts.append(delegation)

        # Handle blacklisted agents (Anti-Looping)
        timeout_str = os.environ.get("AGENT_BLACKLIST_TIMEOUT_SECONDS", "30")
        try:
            timeout = int(timeout_str)
        except ValueError:
            timeout = 30
            
        failed_delegations = self.session.context.get("failed_delegations", {})
        current_time = time.time()
        blacklisted_agents = [
            agent for agent, timestamp in failed_delegations.items()
            if current_time - timestamp < timeout
        ]
        
        if blacklisted_agents:
            context_parts.append(
                f"CRITICAL: The following agents recently failed and are TEMPORARILY BLACKLISTED: {', '.join(blacklisted_agents)}. "
                "DO NOT delegate to these agents for the current request. Explain the issue to the member and offer an alternative."
            )

        context_parts.append(f"Available capabilities:\n{self._capabilities_text}")

        is_restricted = os.environ.get("RESTRICTED_MAIN_AGENT", "true").lower() == "true"
        if is_restricted:
            context_parts.append(
                "CRITICAL RESTRICTION: You are STRICTLY LIMITED to greetings and delegating to sub-agents.\n"
                "You MUST NOT answer general knowledge or domain-specific questions (like FAQ questions).\n"
                "If a member's request matches ANY discovered capability, you MUST immediately use the `delegate_to_agent` tool.\n"
                "If a request falls outside all capabilities, acknowledge the request, state that you are still learning, and offer to connect them with a live agent."
            )

        system_prompt = self.get_system_prompt("\n\n".join(context_parts))

        # Provide standard session messages instead of converting to bedrock
        session_messages = self._get_conversation_messages()

        # Build initial graph state
        initial_state: MainAgentState = {
            "user_input": user_input,
            "messages": session_messages,
            "system_prompt": system_prompt,
            "tools": self._tools_list,
            "response": "",
            "reasoning": "",
            "tool_call": None,
            "delegation_result": None,
            "delegated_to": None,
            "delegation_occurred": False,
        }

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        # Extract results
        response_text = final_state.get("response", "")
        reasoning = final_state.get("reasoning", "")
        delegation_occurred = final_state.get("delegation_occurred", False)
        delegated_to = final_state.get("delegated_to")

        # Add assistant response to session history
        assistant_msg = Message(
            role="assistant",
            content=response_text,
            agent=self.agent_name,
            metadata={"reasoning": reasoning},
        )
        self.session.add_message(self.agent_name, assistant_msg)

        # Build state snapshot for debug panel
        tool_call = final_state.get("tool_call")
        state_snapshot = {
            "current_agent": self.session.current_agent,
            "context": self.session.context,
            "is_new_session": was_new_session,
        }
        if tool_call:
            state_snapshot["tool_call"] = tool_call
            
        display_agent = delegated_to if delegated_to else self.session.current_agent

        return AgentResult(
            response=response_text,
            active_agent=display_agent,
            llm_reasoning=reasoning,
            state_snapshot=state_snapshot,
            delegation_occurred=delegation_occurred,
        )

    # ── Graph Nodes ─────────────────────────────────────────────────────────

    def _process_node(self, state: MainAgentState) -> dict:
        """LLM call with tools. Handles show_capabilities internally.

        If LLM calls delegate_to_agent → sets tool_call for routing.
        If LLM calls show_capabilities → executes, loops back to LLM.
        If LLM returns text → sets response directly.
        """
        messages = list(state["messages"])  # Copy to avoid mutation
        system_prompt = state["system_prompt"]
        tools = state["tools"]

        max_iterations = 5  # Prevent infinite tool loops
        for _ in range(max_iterations):
            # Call LLM with tools
            response = self.llm.invoke_with_tools(messages, system_prompt, tools)

            if response.tool_call:
                if response.tool_call.name == "delegate_to_agent":
                    # Route to delegate node — don't execute the tool
                    return {
                        "tool_call": {
                            "name": response.tool_call.name,
                            "arguments": response.tool_call.arguments,
                            "tool_use_id": response.tool_call.tool_use_id,
                        },
                        "reasoning": response.reasoning,
                    }
                else:
                    # Execute non-delegation tool (show_capabilities)
                    tool_fn = self._tools_map.get(response.tool_call.name)
                    if tool_fn:
                        tool_result = tool_fn.invoke({})
                    else:
                        tool_result = f"Unknown tool: {response.tool_call.name}"

                    # Add assistant tool_use + user tool_result to messages
                    messages.append(Message(
                        role="assistant",
                        content=response.text,
                        metadata={"tool_calls": [response.tool_call]}
                    ))
                    messages.append(Message(
                        role="tool",
                        content=str(tool_result),
                        metadata={"tool_use_id": response.tool_call.tool_use_id}
                    ))
                    continue  # Loop back to LLM with tool result
            else:
                # Direct text response (greeting, decline, etc.)
                return {
                    "response": response.text,
                    "reasoning": response.reasoning,
                }

        # Safety: if we hit max iterations, return what we have
        return {"response": "I'm having trouble processing that. Can you try again?", "reasoning": "Max tool iterations reached"}

    def _delegate_node(self, state: MainAgentState) -> dict:
        """Execute delegation to a sub-agent.

        1. Generate conversation summary via LLM
        2. Set delegation_summary on target agent's state
        3. Instantiate and invoke the target agent
        4. Return the sub-agent's response
        """
        tool_call = state["tool_call"]
        user_input = state["user_input"]
        agent_name = tool_call["arguments"].get("agent_name", "")
        skill = tool_call["arguments"].get("skill", "")
        reason = tool_call["arguments"].get("reason", "")

        logger.info(f"Delegating to {agent_name} (skill: {skill}, reason: {reason})")

        # Generate a conversation summary for handoff
        summary = self._generate_summary(agent_name, reason)

        # Set delegation summary on target agent's session state
        target_state = self.session.get_agent_state(agent_name)
        target_state.delegation_summary = summary

        # Update session current_agent
        self.session.current_agent = agent_name
        self.session.context["last_delegation"] = {
            "from": self.agent_name,
            "to": agent_name,
            "skill": skill,
            "reason": reason,
        }

        # Instantiate and invoke the target agent
        try:
            target_agent = self._create_agent(agent_name)
            result = target_agent.invoke(user_input)

            # Enforce handoff: check if sub-agent immediately yielded control
            result_status = getattr(result, "status", "success")
            if result_status in ("complete", "error"):
                logger.info(f"Sub-agent {agent_name} immediately yielded control with status {result_status}.")
                
                # Track failure for anti-looping
                if result_status == "error":
                    logger.warning(f"Sub-agent {agent_name} returned error status. Blacklisting temporarily.")
                    if "failed_delegations" not in self.session.context:
                        self.session.context["failed_delegations"] = {}
                    self.session.context["failed_delegations"][agent_name] = time.time()
                
                # Return control to orchestrator immediately
                self.session.current_agent = self.agent_name

            return {
                "delegation_result": result.response,
                "delegation_occurred": True,
                "delegated_to": agent_name,
                "reasoning": f"Delegated to {agent_name}: {reason}. Sub-agent response received. Status: {result_status}",
            }
        except Exception as e:
            logger.error(f"Delegation to {agent_name} failed: {e}")
            self.session.current_agent = self.agent_name
            return {
                "response": (
                    f"I tried to connect you to our {agent_name.replace('_', ' ')} "
                    f"service, but encountered an issue. Is there something else I can help with?"
                ),
                "reasoning": f"Delegation to {agent_name} failed: {e}",
            }

    def _respond_node(self, state: MainAgentState) -> dict:
        """Assemble final response from either direct LLM response or delegation result."""
        delegation_result = state.get("delegation_result")
        if delegation_result:
            return {"response": delegation_result}
        # Direct response is already in state["response"] from process_node
        return {}

    def _route_after_process(self, state: MainAgentState) -> str:
        """Route based on LLM's decision: delegate or respond directly."""
        tool_call = state.get("tool_call")
        if tool_call and tool_call.get("name") == "delegate_to_agent":
            return "delegate"
        return "respond"

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _generate_summary(self, target_agent: str, reason: str) -> str:
        """Generate a conversation summary for delegation handoff."""
        messages = self._get_conversation_messages()
        if not messages:
            return f"Member needs: {reason}"

        # Build a simple summary from recent messages
        recent = messages[-6:]  # Last 3 turns
        turns = []
        for msg in recent:
            role = "Member" if msg.role == "user" else "Agent"
            turns.append(f"{role}: {msg.content[:100]}")

        conversation = "\n".join(turns)
        return (
            f"Conversation summary (handing off to {target_agent}):\n"
            f"{conversation}\n"
            f"Reason for delegation: {reason}"
        )

    def _create_agent(self, agent_name: str):
        """Create a sub-agent instance by name."""
        return self.agent_discovery_service.get_agent(agent_name, self.llm, self.session)
