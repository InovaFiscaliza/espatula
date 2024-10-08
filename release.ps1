
# Create app.zip file
$filesToCopy = @(
    "espatula",
    "images",
    "app.py",
    "callbacks.py",
    "config.py",
    "data_processing.py",
    "LICENSE",
    "pyproject.toml",
    "README.md",
    "run.py",
    "ui.py"
    "uv.lock",
    "D:\Applications\Scoop\apps\uv\current\uv.exe"
)


# Remove __pycache__ folder from espatula
Remove-Item -Path ".\espatula\__pycache__" -Recurse -Force



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

# (Get-Item $destinationFolder -Force).Attributes = [System.IO.FileAttributes]::Hidden

Copy-FilesToDestination -filesToCopy $filesToCopy -destinationFolder $destinationFolder

$filesToCopy = @(
   "Regulatron.bat"
)

$destinationFolder = "D:\OneDrive - ANATEL\Regulatron"

Copy-FilesToDestination -filesToCopy $filesToCopy -destinationFolder $destinationFolder

Write-Host "Created app folder with the required contents"

# Compact the destination folder as a zip
$zipPath = "D:\OneDrive - ANATEL\Regulatron\Regulatron.zip"

Compress-Archive -Path "$destinationFolder\*" -DestinationPath $zipPath -Force

Write-Host "Created zip file: $zipPath"



