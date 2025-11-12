# Setup .venv and install core dependencies for multi_agent
# Usage (PowerShell):
#   cd <repo>/multi_agent
#   .\scripts\setup_venv.ps1

param(
    [string]$VenvName = ".venv",
    [string]$Packages = "jsonschema redis pydantic python-dateutil google-generativeai"
)

$cwd = Get-Location
Write-Host "Setting up virtual environment in: $cwd\$VenvName"

# Create venv
python -m venv $VenvName

# Use bundled pip to install packages (avoid relying on Activate execution policy)
$pipPath = Join-Path -Path $cwd -ChildPath "$VenvName\Scripts\pip.exe"
if (-Not (Test-Path $pipPath)) {
    Write-Error "pip not found at $pipPath"
    exit 1
}

Write-Host "Installing packages: $Packages"
& $pipPath install --upgrade pip
& $pipPath install $Packages

Write-Host "Done. To activate the venv in PowerShell run:`n  .\$VenvName\Scripts\Activate.ps1`
Or run commands directly with: .\$VenvName\Scripts\python.exe <script.py>"
