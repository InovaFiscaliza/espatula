
# Create app.zip file
$filesToZip = @(
    "espatula",
    "images",
    "app.py",
    "config.py",
    "LICENSE",
    "packages.txt",
    "pyproject.toml",
    "README.md",
    "run.py",
    "uv.lock",
    "uv.exe"
)

Compress-Archive -Path $filesToZip -DestinationPath "app.zip" -Force

Write-Host "Created app.zip file with required contents"

$filesToZip = @(
    "app.zip",
    "config.json",
    "Regulatron.bat"

)

Compress-Archive -Path $filesToZip -DestinationPath "..\Regulatron.zip" -Force

Write-Host "Created release Regulatron.zip file with required contents"
