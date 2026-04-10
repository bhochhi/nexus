from dataclasses import dataclass, field


@dataclass
class Session:
    """Conversation session state."""

    user_id: str
    session_id: str
    history: list[dict] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    last_intent: str = ""

    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def format_history(self, max_turns: int = 10) -> str:
        """Format recent history as a string for prompt injection."""
        recent = self.history[-max_turns * 2 :]
        if not recent:
            return "(no prior conversation)"
        lines = []
        for msg in recent:
            prefix = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{prefix}: {msg['content']}")
        return "\n".join(lines)
