# Start Django Server with WebSocket Support
# Uses Daphne ASGI server for Django Channels

Write-Host "🚀 Starting AlgoAgent Server with WebSocket support..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Cyan
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️  Virtual environment not found!" -ForegroundColor Yellow
    Write-Host "   Run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Check if daphne is installed
$daphneInstalled = & python -c "try:`n    import daphne`n    print('1')`nexcept:`n    print('0')" 2>$null

if ($daphneInstalled -ne "1") {
    Write-Host "📥 Installing Daphne..." -ForegroundColor Cyan
    pip install daphne
}

Write-Host ""
Write-Host "✨ Starting server on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "🔌 WebSocket endpoint: ws://127.0.0.1:8000/ws/backtest/stream/" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start Daphne ASGI server with 4 worker processes for concurrent request handling
daphne -b 0.0.0.0 -p 8000 --workers 4 algoagent_api.asgi:application
