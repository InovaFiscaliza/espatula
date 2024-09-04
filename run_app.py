# import os
# import sys
# from pathlib import Path

# import streamlit.web.cli as stcli


# def resolve_path(path: str) -> str:
#     base_path = getattr(sys, "_MEIPASS", os.getcwd())
#     return str(Path(base_path) / path)


# if __name__ == "__main__":
#     sys.argv = [
#         "streamlit",
#         "run",
#         resolve_path("app.py"),
#         "--global.developmentMode=false",
#         "--server.headless=true",
#     ]
#     sys.exit(stcli.main())


from streamlit.web import cli

# This import path depends on your Streamlit version
if __name__ == "__main__":
    cli._main_run_clExplicit("app.py", args="streamlit run")
    # We will CREATE this function inside our Streamlit framework
