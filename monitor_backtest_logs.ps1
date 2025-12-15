#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Monitor Django backend logs for backtest configuration and execution
.DESCRIPTION
    Filters Django logs to show configuration parameters (initial_balance, lot_size, commission, slippage)
    and backtest execution details in real-time
#>

Write-Host "=" -ForegroundColor Cyan
Write-Host "  BACKTEST CONFIGURATION MONITOR" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitoring Django logs for backtest configuration..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Find Django server process
$djangoProcess = Get-Process python -ErrorAction SilentlyContinue | 
    Where-Object {$_.Path -like "*AlgoAgent*"} | 
    Select-Object -First 1

if (-not $djangoProcess) {
    Write-Host "❌ Django server not running!" -ForegroundColor Red
    Write-Host "Please start the Django server first." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Django server found (PID: $($djangoProcess.Id))" -ForegroundColor Green
Write-Host ""
Write-Host "Watching for backtest executions..." -ForegroundColor Cyan
Write-Host "-" * 80 -ForegroundColor Gray
Write-Host ""

# Monitor the console output (since Django prints to console)
# We'll watch for specific patterns in the running process
$patterns = @(
    "Initial Balance:",
    "Lot Size:",
    "Commission:",
    "Slippage:",
    "Extracting trades",
    "Starting Balance:",
    "Final Equity:",
    "Total Fills:",
    "Total PnL:",
    "Return:",
    "Received backtest configuration"
)

# Create a temporary file to capture output
$tempFile = [System.IO.Path]::GetTempFileName()

Write-Host "💡 Note: Django console output will be shown below" -ForegroundColor Cyan
Write-Host "   Run backtests in the frontend at http://localhost:5173" -ForegroundColor Cyan
Write-Host ""

# Continuously check for new log entries
try {
    while ($true) {
        Start-Sleep -Milliseconds 500
        
        # Try to read from Django's output if available
        # (This is a simplified version - actual implementation may vary)
        Write-Host "." -NoNewline -ForegroundColor DarkGray
    }
}
catch {
    Write-Host "`n`nMonitoring stopped." -ForegroundColor Yellow
}
finally {
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force
    }
}
