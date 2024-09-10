
# Create app.zip file
$filesToCopy = @(
    "espatula",
    "images",
    "app.py",
    "config.py",
    "LICENSE",
    "pyproject.toml",
    "README.md",
    "run.py",
    "uv.lock"
    # "uv.exe"
)

$destinationFolder = "app"

# Create the destination folder if it doesn't exist
New-Item -ItemType Directory -Force -Path $destinationFolder

# Copy each item to the destination folder
foreach ($item in $filesToCopy) {
    Copy-Item -Path $item -Destination $destinationFolder -Recurse -Force
}

Write-Host "Created app folder with the required contents"

$filesToZip = @(
    "app",
    "config.json",
    "Regulatron.bat"

)

Compress-Archive -Path $filesToZip -DestinationPath "..\Regulatron.zip" -Force

Write-Host "Created release Regulatron.zip file with required contents"


Remove-Item -Path "app" -Recurse -Force -ErrorAction SilentlyContinue

