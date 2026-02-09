# Login first
$loginBody = @{
    username = "algotrader"
    password = "Trading@2024"
} | ConvertTo-Json

Write-Host "Logging in..." -ForegroundColor Cyan
$loginResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" `
    -Method POST `
    -Body $loginBody `
    -ContentType "application/json"

$token = $loginResponse.access

Write-Host "Login successful! Token: $($token.Substring(0, 20))..." -ForegroundColor Green

# Prepare headers
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Execute strategy 115 with real market data
Write-Host "`nTriggering backtest for Strategy 115..." -ForegroundColor Cyan
Write-Host "NOTE: Bot will run using Python from C:\Users\nyaga\Documents\.venv" -ForegroundColor Yellow
$backtestBody = @{
    test_symbol = "AAPL"
    start_date = "2024-01-01"
    end_date = "2024-12-31"
} | ConvertTo-Json

Write-Host "`nBacktest parameters:" -ForegroundColor Yellow
Write-Host "  Symbol: AAPL"
Write-Host "  Period: 2024-01-01 to 2024-12-31"
Write-Host "  Python Environment: C:\Users\nyaga\Documents\.venv\Scripts\python.exe"
Write-Host ""

try {
    $result = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/strategies/strategies/115/execute/" `
        -Method POST `
        -Headers $headers `
        -Body $backtestBody `
        -ContentType "application/json"
    
    Write-Host "Backtest execution initiated!" -ForegroundColor Green
    Write-Host "`nResults:" -ForegroundColor Cyan
    $result | ConvertTo-Json -Depth 10 | Write-Host
    
} catch {
    Write-Host "Error executing backtest:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($_.ErrorDetails) {
        Write-Host $_.ErrorDetails.Message
    }
}
