"""Installed entry points for the two Streamlit demo applications."""

import os
from pathlib import Path
import sys
from typing import Optional


def _launch(filename: str, default_port: str) -> Optional[int]:
    from streamlit.web.cli import main

    app_path = Path(__file__).with_name(filename)
    port = os.getenv("STREAMLIT_SERVER_PORT", default_port)
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        port,
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    return main()


def member_main() -> Optional[int]:
    return _launch("member_ui.py", "8501")


def msr_main() -> Optional[int]:
    return _launch("msr_ui.py", "8502")
