@echo off
setx ESPATULA_BIN "%APPDATA%\Anatel\SCH\bin"
setlocal

set "ESPATULA=%APPDATA%\Anatel\SCH"

if not exist "%ESPATULA%" mkdir "%ESPATULA%"
set CARGO_DIST_FORCE_INSTALL_DIR=%ESPATULA%

powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"

if not exist "%ESPATULA%\bin\uv.exe" (
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
)

endlocal

copy .\config.json .\app\config.json
cd .\app
call "%ESPATULA_BIN%\uv.exe" sync
start "" "%ESPATULA_BIN%\uv.exe" run run.py
timeout /t 5 /nobreak > nul
start "" "http://localhost:8501"
