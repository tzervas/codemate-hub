# Open the devcontainer folder in VS Code using the 'code' CLI
# Usage: run this from PowerShell where 'code' is installed and on PATH
# For Windows + WSL2 users, ensure 'code' is installed to PATH (Visual Studio Code -> Command Palette -> Shell Command: Install 'code' command in PATH)

$devcontainerFolder = "devcontainer-ubuntu-wsl2"
if (-not (Test-Path $devcontainerFolder)) {
    Write-Error "Devcontainer folder not found: $devcontainerFolder"
    exit 1
}

# Open the devcontainer folder in a new VS Code window
Start-Process code -ArgumentList @('-n', (Resolve-Path $devcontainerFolder))

Write-Host "VS Code should open the devcontainer folder. Use 'Dev Containers: Reopen in Container' from the Command Palette if it doesn't automatically prompt."
