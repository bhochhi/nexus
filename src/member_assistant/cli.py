"""Member-only WebSocket chat client."""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional, Sequence
from urllib.parse import quote
import uuid

from member_assistant.config import Settings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Member chat client for the Agentic Member Assistant"
    )
    parser.add_argument(
        "--session",
        help="durable session identifier; omitted creates a new session",
    )
    parser.add_argument(
        "--url",
        help="WebSocket server base URL (defaults to MEMBER_ASSISTANT_SERVER_URL)",
    )
    parser.add_argument(
        "--after-event-id",
        help="replay only events after this durable event ID",
    )
    return parser


def _color(text: str, code: str, enabled: bool) -> str:
    return "\033[{}m{}\033[0m".format(code, text) if enabled else text


def _model_line(metadata: Dict[str, Any]) -> str:
    parts = [
        "provider={}".format(metadata.get("provider", "unknown")),
        "model={}".format(metadata.get("model", "unknown")),
    ]
    if metadata.get("api_endpoint"):
        parts.append("endpoint={}".format(metadata["api_endpoint"]))
    if metadata.get("reasoning_effort"):
        parts.append("reasoning={}".format(metadata["reasoning_effort"]))
    if metadata.get("aws_region"):
        parts.append("region={}".format(metadata["aws_region"]))
    parts.append(
        "fallback={}".format(
            "USED" if metadata.get("fallback_used") else "not used"
        )
    )
    return " | ".join(parts)


def _render_event(
    event: Dict[str, Any], *, color_enabled: bool, replay: bool = False
) -> bool:
    event_type = event.get("type")
    if event_type in {
        "assistant.message",
        "assistant.request_input",
        "assistant.request_confirmation",
        "handoff.offered",
    }:
        prefix = "history>" if replay else "assistant>"
        print(
            _color(prefix, "2;37" if replay else "1;32", color_enabled)
            + " "
            + str(event.get("content", ""))
        )
    elif event_type == "turn.accepted" and not replay:
        print(_color("assistant is working…", "2;36", color_enabled))
    elif event_type == "turn.completed":
        if not replay:
            print(
                _color(
                    "model(last call)> " + _model_line(event.get("metadata", {})),
                    "2;37",
                    color_enabled,
                )
            )
        return True
    elif event_type == "turn.failed":
        if not replay:
            print(
                _color("error>", "1;31", color_enabled)
                + " "
                + str(event.get("content", "The turn failed safely."))
            )
        return True
    elif event_type == "protocol.error":
        print(
            _color("error>", "1;31", color_enabled)
            + " "
            + str(event.get("error", "WebSocket protocol error"))
        )
        return bool(event.get("final", False))
    return False


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    settings = Settings.from_env()
    session_id = args.session or "session_{}".format(uuid.uuid4().hex)
    base_url = (args.url or settings.websocket_url).rstrip("/")
    socket_url = "{}/v1/sessions/{}/stream".format(
        base_url, quote(session_id, safe="")
    )
    if args.after_event_id:
        socket_url += "?after_event_id={}".format(
            quote(args.after_event_id, safe="")
        )
    color_enabled = sys.stdout.isatty() and "NO_COLOR" not in os.environ

    try:
        from websockets.exceptions import ConnectionClosed
        from websockets.sync.client import connect
    except ImportError:
        print(
            "error> WebSocket client dependency is missing; reinstall the project.",
            file=sys.stderr,
        )
        return 2

    print(_color("Agentic Member Assistant", "1;36", color_enabled))
    print("Session: {}".format(session_id))
    print("Server: {}".format(base_url))
    print("Member conversation only. Press Ctrl-D or Ctrl-C to exit.")
    try:
        with connect(socket_url) as websocket:
            while True:
                event = json.loads(websocket.recv())
                if event.get("type") == "session.ready":
                    print(
                        _color(
                            "Connected (catalog revision {}).".format(
                                event.get("catalog_revision")
                            ),
                            "32",
                            color_enabled,
                        )
                    )
                    break
                _render_event(event, color_enabled=color_enabled, replay=True)

            while True:
                try:
                    prompt = "\033[1;34mmember> " if color_enabled else "member> "
                    message = input(prompt).strip()
                    if color_enabled:
                        print("\033[0m", end="", flush=True)
                except (EOFError, KeyboardInterrupt):
                    if color_enabled:
                        print("\033[0m", end="", flush=True)
                    print()
                    break
                if not message:
                    continue
                websocket.send(
                    json.dumps(
                        {
                            "type": "member.message",
                            "message_id": "msg_{}".format(uuid.uuid4().hex),
                            "content": message,
                        }
                    )
                )
                while True:
                    event = json.loads(websocket.recv())
                    if _render_event(event, color_enabled=color_enabled):
                        break
    except (ConnectionClosed, OSError) as exc:
        print(
            _color("error>", "1;31", color_enabled)
            + " Could not use {}: {}".format(socket_url, exc),
            file=sys.stderr,
        )
        print("Start the service with: member-assistant-server", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
