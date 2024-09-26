import sys
from pathlib import Path

import streamlit.web.cli as stcli


def resolve_path(path: str) -> str:
    return str(Path(__file__).parent / path)


if __name__ == "__main__":
    default_args = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
        "--server.headless=true",
        "--client.toolbarMode=viewer",
    ]

    # Add any additional CLI arguments passed by the user
    user_args = sys.argv[1:]
    sys.argv = default_args + user_args

    sys.exit(stcli.main())
