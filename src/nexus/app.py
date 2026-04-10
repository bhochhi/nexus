"""Nexus conversational agent CLI entry point."""

import logging
import uuid

from nexus.config import settings
from nexus.graph.agent import build_graph
from nexus.llm.factory import LLMFactory
from nexus.memory.store import InMemoryStore
from nexus.tools.banking import register_banking_tools
from nexus.tools.faq import register_faq_tools
from nexus.tools.insurance import register_insurance_tools
from nexus.tools.registry import ToolRegistry


def create_agent():
    """Create and return a compiled conversational agent graph."""
    llm = LLMFactory.create()
    store = InMemoryStore()

    registry = ToolRegistry()
    register_banking_tools(registry)
    register_insurance_tools(registry)
    register_faq_tools(registry)

    return build_graph(llm=llm, store=store, registry=registry), store


def main():
    logging.basicConfig(level=getattr(logging, settings.log_level))

    print("Nexus Financial Assistant")
    print("Type 'quit' to exit.\n")

    agent, store = create_agent()
    session_id = str(uuid.uuid4())
    user_id = "user-001"

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        result = agent.invoke(
            {
                "user_message": user_input,
                "user_id": user_id,
                "session_id": session_id,
            }
        )

        print(f"Nexus: {result.get('response_text', 'I apologize, something went wrong.')}\n")


if __name__ == "__main__":
    main()
