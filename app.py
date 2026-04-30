"""
Nexus — Application Entry Point.

CLI REPL for member conversations. Accepts member_id as argument.
Displays response + debug panel per turn.

Features: F-001 (Greeting), F-007 (Debug Panel)

Usage:
    python app.py --member-id M12345
    python app.py  (uses default member_id)
"""
import argparse
import logging
import sys

from agents.main_agent.agent import MainAgent
from config import Config
from core.discovery import discover_agents
from core.llm import get_llm_client
from core.session import SessionManager
from core.types import AgentResult


def setup_logging(level: str = "INFO"):
    """Configure basic logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def print_debug_panel(result: AgentResult):
    """Display the debug transparency panel without character limits."""
    print()
    print("\033[93m--- Debug ---\033[0m")

    # Agent line (show delegation if it occurred)
    agent_display = result.active_agent
    if result.delegation_occurred:
        tc = result.state_snapshot.get("tool_call", {})
        target = tc.get("arguments", {}).get("agent_name", "?")
        agent_display = f"{result.active_agent} -> {target} (delegated)"
    print(f"\033[93mAgent:     {agent_display}\033[0m")

    # Tool call (if any)
    tc = result.state_snapshot.get("tool_call")
    if tc:
        call_str = f"{tc['name']}("
        args = tc.get("arguments", {})
        arg_parts = [f'{k}="{v}"' for k, v in args.items()]
        call_str += ", ".join(arg_parts) + ")"
        print(f"\033[93mTool:      {call_str}\033[0m")
    else:
        print(f"\033[93mTool:      (direct response)\033[0m")

    # Reasoning
    if result.llm_reasoning:
        print(f"\033[93mReasoning: {result.llm_reasoning}\033[0m")
    else:
        print(f"\033[93mReasoning: (none)\033[0m")

    # Status
    print(f"\033[93mStatus:    {result.status}\033[0m")
    if result.status == "error" and result.error_details:
        print(f"\033[91mError:     {result.error_details}\033[0m")

    # State snapshot
    print(f"\033[93mState:     {result.state_snapshot}\033[0m")
    print("\033[93m-------------\033[0m")
    print()


def main():
    parser = argparse.ArgumentParser(description="Nexus — AI Assistant for Financial Services")
    parser.add_argument("--member-id", default=Config.DEFAULT_MEMBER_ID, help="Member ID for the session")
    parser.add_argument("--debug", action="store_true", default=Config.DEBUG, help="Show debug panel")
    parser.add_argument("--log-level", default=Config.LOG_LEVEL, help="Log level (DEBUG/INFO/WARNING)")
    args = parser.parse_args()

    setup_logging(args.log_level)
    logger = logging.getLogger("nexus")

    # Initialize
    print("\n🔷 Nexus — Financial Services AI Assistant")
    print("=" * 50)

    try:
        llm_client = get_llm_client(Config)
    except RuntimeError as e:
        print(f"\n❌ {e}")
        sys.exit(1)

    capabilities = discover_agents(Config.AGENTS_DIR)
    logger.info(f"Discovered {len(capabilities)} agent(s)")

    session_mgr = SessionManager()
    session = session_mgr.get_or_create(args.member_id)
    logger.info(f"Session: {session.session_id} (member: {args.member_id})")

    # Create main agent
    main_agent = MainAgent(llm_client, session, capabilities)

    # Initial greeting for new session
    if session.is_new_session:
        result = main_agent.invoke("hello")
        agent_name = result.active_agent
        session.get_agent_state(agent_name).results.append(result)
        print(f"\n\033[94m[{agent_name}]\033[0m: {result.response}")
        if args.debug:
            print_debug_panel(result)

    # REPL loop
    print("(Type 'quit' or 'exit' to end)\n")
    while True:
        try:
            user_input = input(f"\033[92mYou:\033[0m ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("\n\033[93m[System]\033[0m: Goodbye! Feel free to reach out anytime. 👋")
            break

        result = main_agent.invoke(user_input)
        agent_name = result.active_agent
        session.get_agent_state(agent_name).results.append(result)
        print(f"\n\033[94m[{agent_name}]\033[0m: {result.response}")

        if args.debug:
            print_debug_panel(result)
            
        # If control was handed back to the orchestrator this turn, announce it
        if result.delegation_occurred and session.current_agent == "main_agent" and agent_name != "main_agent":
            print(f"\n\033[94m[main_agent]\033[0m: Welcome back! What else can I help you with today?")

        # Update session
        session_mgr.update(session)


if __name__ == "__main__":
    main()
