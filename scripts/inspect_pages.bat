@echo off
set WORKING_DIR=C:\Users\rsilva\code\espatula
set PYTHON_EXE=C:\Users\rsilva\scoop\apps\mambaforge\current\envs\espatula\python.exe
set SCRIPT_PATH=.\scripts\scrape.py

cd /d %WORKING_DIR%
git pull
%PYTHON_EXE% %SCRIPT_PATH% --scraper ml --search
%PYTHON_EXE% %SCRIPT_PATH% --scraper amazon --search
%PYTHON_EXE% %SCRIPT_PATH% --scraper magalu --search
%PYTHON_EXE% %SCRIPT_PATH% --scraper carrefour --search
%PYTHON_EXE% %SCRIPT_PATH% --scraper americanas --search
%PYTHON_EXE% %SCRIPT_PATH% --scraper casasbahia --search
%PYTHON_EXE% %SCRIPT_PATH% --scraper ml
%PYTHON_EXE% %SCRIPT_PATH% --scraper amazon 
%PYTHON_EXE% %SCRIPT_PATH% --scraper magalu
%PYTHON_EXE% %SCRIPT_PATH% --scraper carrefour
%PYTHON_EXE% %SCRIPT_PATH% --scraper americanas
%PYTHON_EXE% %SCRIPT_PATH% --scraper casasbahia --no-screenshot
