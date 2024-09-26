
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

(Get-Item $destinationFolder -Force).Attributes = [System.IO.FileAttributes]::Hidden

Copy-FilesToDestination -filesToCopy $filesToCopy -destinationFolder $destinationFolder

$filesToCopy = @(
   "Regulatron.bat"
)

$destinationFolder = "D:\OneDrive - ANATEL\Regulatron"

Copy-FilesToDestination -filesToCopy $filesToCopy -destinationFolder $destinationFolder
 
Get-ChildItem -Path $destinationFolder -Recurse | ForEach-Object {
    $_.Attributes = $_.Attributes -bor [System.IO.FileAttributes]::ReadOnly
}
# cd $destinationFolder

# cd ..

# 7z a -sfx Regulatron.sfx Regulatron

# copy /b Regulatron.sfx + 7z.config.txt Regulatron.exe

Write-Host "Created app folder with the required contents"

# $filesToZip = @(
#     "app",
#     "Regulatron.bat"

# )

# Compress-Archive -Path $filesToZip -DestinationPath "D:\OneDrive - ANATEL\AppRegulatron.zip" -Force

# Write-Host "Created release Regulatron.zip file with required contents"


# Remove-Item -Path "app" -Recurse -Force -ErrorAction SilentlyContinue

