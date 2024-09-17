
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
    "D:\Applications\Scoop\apps\uv\current\uv.exe"
)

$destinationFolder = "D:\OneDrive - ANATEL\AppRegulatron"

# Create the destination folder if it doesn't exist
New-Item -ItemType Directory -Force -Path $destinationFolder

# Copy each item to the destination folder
foreach ($item in $filesToCopy) {
    Copy-Item -Path $item -Destination $destinationFolder -Recurse -Force -PassThru | Where-Object {$_.LastWriteTime -gt (Get-Item (Join-Path -Path $destinationFolder -ChildPath $_.Name)).LastWriteTime}
}
Write-Host "Created app folder with the required contents"

# $filesToZip = @(
#     "app",
#     "Regulatron.bat"

# )

# Compress-Archive -Path $filesToZip -DestinationPath "D:\OneDrive - ANATEL\AppRegulatron.zip" -Force

# Write-Host "Created release Regulatron.zip file with required contents"


# Remove-Item -Path "app" -Recurse -Force -ErrorAction SilentlyContinue

