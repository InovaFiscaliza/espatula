@echo off
set "REGULATRON=%APPDATA%\Anatel\Regulatron"
set "UV_CACHE_DIR=%REGULATRON%\uv-cache"
set "UV_TOOL_BIN_DIR=%REGULATRON%\uv-tool"
set "UV_PYTHON_INSTALL_DIR=%REGULATRON%\uv-python"
if not exist "%REGULATRON%" (
    mkdir "%REGULATRON%"
)
@REM ) else (
@REM     rd /s /q "%REGULATRON%"
@REM     mkdir "%REGULATRON%"
@REM )

powershell -Command "Expand-Archive -Path .\app.zip -DestinationPath  $Env:REGULATRON -Force"
powershell -Command "[Environment]::SetEnvironmentVariable('PYTHONUTF8','1', 'User')"
copy .\config.json %REGULATRON%\config.json
cd %REGULATRON%
call "%REGULATRON%\uv.exe" sync --locked --no-progress
start "" "%REGULATRON%\uv.exe" run run.py --locked
timeout /t 5 /nobreak > nul
start "" "http://localhost:8501"

