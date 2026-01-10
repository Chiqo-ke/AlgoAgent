# Strategy Runner Script
# Usage: .\run_strategy.ps1 <strategy_file.py>

param(
    [Parameter(Mandatory=$false)]
    [string]$StrategyFile
)

$VENV_PYTHON = "C:\Users\nyaga\Documents\AlgoAgent\.venv\Scripts\python.exe"
$MULTI_AGENT_ROOT = "C:\Users\nyaga\Documents\AlgoAgent\multi_agent"

# Set PYTHONPATH to multi_agent directory
$env:PYTHONPATH = $MULTI_AGENT_ROOT

if (-not $StrategyFile) {
    Write-Host "Available strategies:"
    Get-ChildItem "$MULTI_AGENT_ROOT\Backtest\codes" -Filter "*.py" | 
        Where-Object { $_.Name -notlike "__*" } | 
        ForEach-Object { Write-Host "  - $($_.Name)" }
    Write-Host ""
    Write-Host "Usage: .\run_strategy.ps1 <strategy_file.py>"
    exit 0
}

# Check if file exists
$FullPath = Join-Path "$MULTI_AGENT_ROOT\Backtest\codes" $StrategyFile
if (-not (Test-Path $FullPath)) {
    Write-Host "ERROR: Strategy file not found: $FullPath"
    exit 1
}

Write-Host "Running strategy: $StrategyFile"
Write-Host "Python: $VENV_PYTHON"
Write-Host "PYTHONPATH: $env:PYTHONPATH"
Write-Host ("=" * 70)

& $VENV_PYTHON $FullPath

Write-Host ""
Write-Host ("=" * 70)
Write-Host "Strategy execution completed. Exit code: $LASTEXITCODE"
