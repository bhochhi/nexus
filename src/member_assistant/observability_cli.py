"""Manage and diagnose the local Langfuse Docker Compose stack."""

import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from typing import Optional, Sequence
import urllib.error
import urllib.request

from member_assistant.config import PROJECT_ROOT, Settings


COMPOSE_FILE = PROJECT_ROOT / "observability" / "docker-compose.langfuse.yml"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Langfuse controls")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("up", help="start the local Langfuse stack")
    subparsers.add_parser("down", help="stop containers and preserve trace volumes")
    subparsers.add_parser("status", help="show container status")
    logs = subparsers.add_parser("logs", help="show Langfuse container logs")
    logs.add_argument("--follow", action="store_true")
    logs.add_argument("--tail", default="100")
    subparsers.add_parser("doctor", help="verify health and project-key authentication")
    subparsers.add_parser("url", help="print the local Langfuse URL and demo login")
    return parser


def _compose(arguments: Sequence[str]) -> int:
    command = ["docker", "compose", "-f", str(COMPOSE_FILE), *arguments]
    try:
        return subprocess.run(command, cwd=str(PROJECT_ROOT), check=False).returncode
    except FileNotFoundError:
        print("Docker is not installed or is not on PATH.", file=sys.stderr)
        return 2


def _request(url: str, authorization: Optional[str] = None) -> dict:
    headers = {"Authorization": authorization} if authorization else {}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"body": body}
        return {"status": response.status, "response": parsed}


def _doctor(settings: Settings) -> int:
    base_url = settings.langfuse_base_url.rstrip("/")
    try:
        health = _request(base_url + "/api/public/health?failIfDatabaseUnavailable=true")
        credentials = "{}:{}".format(
            settings.langfuse_public_key or "", settings.langfuse_secret_key or ""
        )
        auth = "Basic " + base64.b64encode(credentials.encode("utf-8")).decode("ascii")
        project = _request(base_url + "/api/public/projects", auth)
        observations = _request(base_url + "/api/public/v2/observations?limit=1", auth)
    except (urllib.error.URLError, TimeoutError) as exc:
        print("Langfuse check failed: {}".format(exc), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "health": health,
                "project_auth": project,
                "latest_observation": observations,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    settings = Settings.from_env()
    if args.command == "up":
        code = _compose(["up", "-d"])
        if code == 0:
            print("Langfuse is starting at {}.".format(settings.langfuse_base_url))
            print("Run 'member-assistant-observability doctor' when containers are ready.")
        return code
    if args.command == "down":
        return _compose(["down"])
    if args.command == "status":
        return _compose(["ps"])
    if args.command == "logs":
        command = ["logs", "--tail", str(args.tail)]
        if args.follow:
            command.append("--follow")
        return _compose(command)
    if args.command == "doctor":
        return _doctor(settings)
    if args.command == "url":
        print(settings.langfuse_base_url)
        print("Local demo login: demo@member-assistant.local / local-observability-demo")
        return 0
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
