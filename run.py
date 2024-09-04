import sys
from pathlib import Path

import streamlit.web.cli as stcli


def resolve_path(path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", Path(__file__).parent)
    return str(Path(base_path) / path)


if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
        "--server.headless=true",
    ]
    sys.exit(stcli.main())
