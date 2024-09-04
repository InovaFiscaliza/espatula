powershell -c "irm https://astral.sh/uv/0.4.4/install.ps1 | iex"
Add-Content -Path $PROFILE -Value '(& uv generate-shell-completion powershell) | Out-String | Invoke-Expression'
uv run .\espatula\run.py