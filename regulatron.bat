@echo off
set "REGULATRON=%APPDATA%\Anatel\Regulatron"
set "UV_CACHE_DIR=%REGULATRON%\uv-cache"
set "UV_TOOL_BIN_DIR=%REGULATRON%\uv-tool"
set "UV_PYTHON_INSTALL_DIR=%REGULATRON%\uv-python"
set "PYTHONUTF8=1"
if not exist "%REGULATRON%" (
    mkdir "%REGULATRON%"
)
@REM ) else (
@REM     rd /s /q "%REGULATRON%"
@REM     mkdir "%REGULATRON%"
@REM )

powershell -Command "robocopy .\app $Env:REGULATRON /E /XO"
powershell -Command "[Environment]::SetEnvironmentVariable('PYTHONUTF8','1', 'User')"
powershell -Command "robocopy .\config.json $Env:REGULATRON%\config.json /XO"
cd %REGULATRON%
call "%REGULATRON%\uv.exe" sync --locked --no-progress
start "" "%REGULATRON%\uv.exe" run run.py --locked
timeout /t 5 /nobreak > nul
start "" "http://localhost:8501"

