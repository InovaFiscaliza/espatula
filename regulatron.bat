@echo off
if not exist "%USERPROFILE%\.cargo\bin\uv.exe" (
    powershell -c "irm https://astral.sh/uv/0.4.4/install.ps1 | iex"
)
cd .\app
call %USERPROFILE%\.cargo\bin\uv.exe run run.py
start "" "http://localhost:8502"
