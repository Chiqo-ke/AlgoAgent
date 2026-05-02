<#
.SYNOPSIS
    Start the MT5 Bridge server for local development on Windows.

.DESCRIPTION
    Activates the shared .venv, installs bridge dependencies if needed,
    then launches mt5_bridge.py which exposes a local HTTP API on :5555.

    Django (settings_local.py) reads MT5_USE_BRIDGE=true from .env.local
    and routes all MT5 calls through http://127.0.0.1:5555 - the same code
    path used in production (Ubuntu + Wine).

.PREREQUISITES
    - MetaTrader5 terminal (terminal64.exe) must already be running and logged in.
    - MT5_LOGIN / MT5_PASSWORD / MT5_SERVER filled in monolithic_agent/.env.local
      (or passed as environment variables before running this script).

.USAGE
    # From any directory:
    .\AlgoAgent\monolithic_agent\start_dev_mt5_bridge.ps1

    # To run in the background (recommended while developing):
    Start-Job -ScriptBlock { & "C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent\start_dev_mt5_bridge.ps1" }
#>

$ErrorActionPreference = "Stop"

# Paths
$WorkspaceRoot  = "C:\Users\nyaga\Documents"
$VenvActivate   = Join-Path $WorkspaceRoot ".venv\Scripts\Activate.ps1"
$BridgeScript   = Join-Path $WorkspaceRoot "AlgoAgent\mt5_bridge\mt5_bridge.py"
$BridgeReqs     = Join-Path $WorkspaceRoot "AlgoAgent\mt5_bridge\requirements.txt"
$EnvLocal       = Join-Path $WorkspaceRoot "AlgoAgent\monolithic_agent\.env.local"

# Fall back to the standalone repo if the submodule hasn't been initialised yet
if (-not (Test-Path $BridgeScript)) {
    $BridgeScript = Join-Path $WorkspaceRoot "mt5-bridge\mt5_bridge.py"
    $BridgeReqs   = Join-Path $WorkspaceRoot "mt5-bridge\requirements.txt"
    Write-Host "[bridge] Submodule not initialised - using standalone repo at mt5-bridge/" -ForegroundColor Yellow
}

if (-not (Test-Path $BridgeScript)) {
    Write-Error "mt5_bridge.py not found. Run: git -C '$WorkspaceRoot\AlgoAgent' submodule update --init"
    exit 1
}

# Activate venv
if (Test-Path $VenvActivate) {
    Write-Host "[bridge] Activating .venv..." -ForegroundColor Cyan
    & $VenvActivate
}
else {
    Write-Warning ".venv not found at $VenvActivate - using system Python."
}

# Install bridge deps (idempotent)
if (Test-Path $BridgeReqs) {
    Write-Host "[bridge] Ensuring bridge dependencies are installed..." -ForegroundColor Cyan
    pip install -r $BridgeReqs --quiet
}

# Load .env.local into this process so mt5_bridge.py can read them
if (Test-Path $EnvLocal) {
    Write-Host "[bridge] Loading .env.local..." -ForegroundColor Cyan
    Get-Content $EnvLocal | ForEach-Object {
        if ($_ -match '^\s*([^#=\s][^=]*?)\s*=\s*(.*?)\s*$') {
            $key   = $Matches[1]
            $value = $Matches[2]
            if ($value -ne '') {
                [System.Environment]::SetEnvironmentVariable($key, $value, 'Process')
            }
        }
    }
}

# Start bridge
Write-Host ""
Write-Host "[bridge] Starting MT5 Bridge on 127.0.0.1:5555 ..." -ForegroundColor Green
Write-Host "[bridge] Script: $BridgeScript" -ForegroundColor DarkGray
Write-Host "[bridge] Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

python $BridgeScript
