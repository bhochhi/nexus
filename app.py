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
from core.llm import LLMClient
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
    """Display the debug transparency panel (F-007)."""
    W = 55  # panel inner width
    print()
    print("┌─ Debug " + "─" * (W - 8) + "┐")

    # Agent line (show delegation if it occurred)
    agent_display = result.active_agent
    if result.delegation_occurred:
        tc = result.state_snapshot.get("tool_call", {})
        target = tc.get("arguments", {}).get("agent_name", "?")
        agent_display = f"{result.active_agent} → {target} (delegated)"
    print(f"│ Agent:     {agent_display:<{W - 13}}│")

    # Tool call (if any)
    tc = result.state_snapshot.get("tool_call")
    if tc:
        call_str = f"{tc['name']}("
        args = tc.get("arguments", {})
        arg_parts = [f'{k}="{v}"' for k, v in args.items()]
        call_str += ", ".join(arg_parts) + ")"
        if len(call_str) > W - 13:
            call_str = call_str[: W - 16] + "..."
        print(f"│ Tool:      {call_str:<{W - 13}}│")
    else:
        print(f"│ Tool:      {'(direct response)':<{W - 13}}│")

    # Reasoning
    if result.llm_reasoning:
        reason_lines = result.llm_reasoning[:120].split("\n")
        for i, line in enumerate(reason_lines[:3]):
            label = "Reasoning:" if i == 0 else "          "
            text = line[: W - 14]
            print(f"│ {label} {text:<{W - 14}}│")
    else:
        print(f"│ Reasoning: {'(none)':<{W - 14}}│")

    # State snapshot
    state_str = str(result.state_snapshot)
    if len(state_str) > W - 13:
        state_str = state_str[: W - 16] + "..."
    print(f"│ State:     {state_str:<{W - 13}}│")
    print("└" + "─" * W + "┘")
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
        llm_client = LLMClient(model_id=Config.LLM_MODEL_ID, region=Config.LLM_REGION)
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
        print(f"\nNexus: {result.response}")
        if args.debug:
            print_debug_panel(result)

    # REPL loop
    print("(Type 'quit' or 'exit' to end)\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("\nNexus: Goodbye! Feel free to reach out anytime. 👋")
            break

        result = main_agent.invoke(user_input)
        print(f"\nNexus: {result.response}")

        if args.debug:
            print_debug_panel(result)

        # Update session
        session_mgr.update(session)


if __name__ == "__main__":
    main()
