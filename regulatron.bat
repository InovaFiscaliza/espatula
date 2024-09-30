@echo off
set "REGULATRON=%APPDATA%\Anatel\Regulatron"
set "UV_CACHE_DIR=%REGULATRON%\uv-cache"
set "UV_TOOL_BIN_DIR=%REGULATRON%\uv-tool"
set "UV_PYTHON_INSTALL_DIR=%REGULATRON%\uv-python"
set "PYTHONUTF8=1"
if not exist "%REGULATRON%" (
    mkdir "%REGULATRON%"
)
xcopy /s /e /y .\app "%APPDATA%\Anatel\Regulatron\" > nul 2>&1
if errorlevel 1 (
    echo Ocorreu um erro ao copiar o app para o diretório de trabalho do Regulatron
    pause
    exit /b 1
)
@REM powershell -Command "Remove-Item -Path $Env:APPDATA\Anatel\Regulatron\__pycache__ -Recurse -Force" > nul 2>&1
@REM powershell -Command "Remove-Item -Path $Env:APPDATA\Anatel\Regulatron\espatula\__pycache__ -Recurse -Force" > nul 2>&1


powershell -Command "[Environment]::SetEnvironmentVariable('PYTHONUTF8','1', 'User')" > nul 2>&1

pushd "%REGULATRON%"

call "%REGULATRON%\uv.exe" sync --python 3.12 --frozen
if errorlevel 1 (
    echo Ocorreu um erro ao sincronizar o ambiente virtual. Por favor, verifique sua conexão com a internet e tente novamente.
    pause
    exit /b 1
)

start "" "%REGULATRON%\uv.exe" run  --frozen run.py
if errorlevel 1 (
    echo Ocorreu um erro ao iniciar o aplicativo Regulatron. Por favor, verifique se todos os arquivos necessários estão presentes e tente novamente.
    pause
    exit /b 1
)

timeout /t 5 /nobreak > nul

start "" "http://localhost:8501" > nul 2>&1
if errorlevel 1 (
    echo Ocorreu um erro ao abrir o navegador. Por favor, verifique se você tem um navegador padrão configurado e se o aplicativo Regulatron está em execução.
    pause
    exit /b 1
)
