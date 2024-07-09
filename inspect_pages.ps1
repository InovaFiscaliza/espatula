$WORKING_DIR = "C:\Users\rsilva\code\espatula"
$PYTHON_EXE = "D:\Applications\Scoop\apps\miniconda3\current\envs\sb\python.exe"
$SCRIPT_PATH = ".\scripts\scrape.py"

Set-Location $WORKING_DIR
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH mercado_livre --keyword smartphone --no-search --screenshot" -WindowStyle Hidden
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH amazon --keyword smartphone --no-search --screenshot" -WindowStyle Hidden
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH magalu --keyword smartphone --no-search --screenshot" -WindowStyle Hidden
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH carrefour --keyword smartphone --no-search --screenshot" -WindowStyle Hidden
Start-Process -FilePath $PYTHON_EXE -ArgumentList "$SCRIPT_PATH americanas --keyword smartphone --no-search --screenshot" -WindowStyle Hidden
