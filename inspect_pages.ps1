$WORKING_DIR = "C:\Users\rsilva\code\espatula"
$PYTHON_EXE = "C:\Users\rsilva\scoop\apps\mambaforge\current\envs\espatula\python.exe"
$SCRIPT_PATH = ".\scripts\scrape.py"

Set-Location $WORKING_DIR
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH --scraper mercado_livre --keyword smartphone --no-search --screenshot"  -WindowStyle Hidden 
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH --scraper amazon --keyword smartphone --no-search --screenshot" -WindowStyle Hidden
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH --scraper magalu --keyword smartphone --no-search --screenshot"  -WindowStyle Hidden
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH --scraper carrefour --keyword smartphone --no-search --screenshot" -WindowStyle Hidden
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH --scraper americanas --keyword smartphone --no-search --screenshot"  -WindowStyle Hidden
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH --scraper casasbahia --keyword smartphone --no-search"  -WindowStyle Hidden
