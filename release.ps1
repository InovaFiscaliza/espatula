
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

# Copy each item to the destination folder
function Copy-FilesToDestination {
    param (
        [Parameter(Mandatory=$true)]
        [string[]]$filesToCopy,
        [Parameter(Mandatory=$true)]
        [string]$destinationFolder
    )

    foreach ($item in $filesToCopy) {
        $destinationPath = Join-Path -Path $destinationFolder -ChildPath (Split-Path -Path $item -Leaf)
        if (Test-Path -Path $destinationPath) {
            $sourceItem = Get-Item -Path $item
            $destinationItem = Get-Item -Path $destinationPath
            if ($sourceItem.LastWriteTime -gt $destinationItem.LastWriteTime) {
                Copy-Item -Path $item -Destination $destinationFolder -Recurse -Force
            }
        } else {
            Copy-Item -Path $item -Destination $destinationFolder -Recurse -Force
        }
    }
}

$destinationFolder = "D:\OneDrive - ANATEL\Regulatron\app"

# Create the destination folder if it doesn't exist
New-Item -ItemType Directory -Force -Path $destinationFolder

Copy-FilesToDestination -filesToCopy $filesToCopy -destinationFolder $destinationFolder

$filesToCopy = @(
   "Regulatron.bat"
)

$destinationFolder = "D:\OneDrive - ANATEL\Regulatron"

Copy-FilesToDestination -filesToCopy $filesToCopy -destinationFolder $destinationFolder


Write-Host "Created app folder with the required contents"

# $filesToZip = @(
#     "app",
#     "Regulatron.bat"

# )

# Compress-Archive -Path $filesToZip -DestinationPath "D:\OneDrive - ANATEL\AppRegulatron.zip" -Force

# Write-Host "Created release Regulatron.zip file with required contents"


# Remove-Item -Path "app" -Recurse -Force -ErrorAction SilentlyContinue

