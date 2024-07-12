@echo off
set WORKING_DIR=C:\Users\rsilva\code\espatula
set PYTHON_EXE=C:\Users\rsilva\scoop\apps\mambaforge\current\envs\espatula\python.exe
set SCRIPT_PATH=.\scripts\scrape.py

cd /d %WORKING_DIR%
start /B "" %PYTHON_EXE% %SCRIPT_PATH% --scraper mercado_livre
start /B "" %PYTHON_EXE% %SCRIPT_PATH% --scraper amazon 
start /B "" %PYTHON_EXE% %SCRIPT_PATH% --scraper magalu
start /B "" %PYTHON_EXE% %SCRIPT_PATH% --scraper carrefour
start /B "" %PYTHON_EXE% %SCRIPT_PATH% --scraper americanas
start /B "" %PYTHON_EXE% %SCRIPT_PATH% --scraper casasbahia --no-screenshot
