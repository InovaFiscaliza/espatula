@echo off
set "REGULATRON=%APPDATA%\Anatel\Regulatron"
set "UV_CACHE_DIR=%REGULATRON%\uv-cache"
set "UV_TOOL_BIN_DIR=%REGULATRON%\uv-tool"
set "UV_PYTHON_INSTALL_DIR=%REGULATRON%\uv-python"
set "PYTHONUTF8=1"
if not exist "%REGULATRON%" (
    mkdir "%REGULATRON%"
)
powershell -Command "robocopy .\app $Env:APPDATA\Anatel\Regulatron /E /XO /NFL /NDL /NJH /NJS /NC /NS /NP" > nul 2>&1
@REM powershell -Command "Remove-Item -Path $Env:APPDATA\Anatel\Regulatron\__pycache__ -Recurse -Force" > nul 2>&1
@REM powershell -Command "Remove-Item -Path $Env:APPDATA\Anatel\Regulatron\espatula\__pycache__ -Recurse -Force" > nul 2>&1


powershell -Command "[Environment]::SetEnvironmentVariable('PYTHONUTF8','1', 'User')" > nul 2>&1
cd %REGULATRON%
call "%REGULATRON%\uv.exe" sync --python 3.12 --frozen
if %ERRORLEVEL% EQU 0 (
    start "" "%REGULATRON%\uv.exe" run  --frozen run.py
    timeout /t 5 /nobreak > nul
    start "" "http://localhost:8501" > nul 2>&1

)

