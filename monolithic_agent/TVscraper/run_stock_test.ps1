# Run stock data fetching test with venv environment
# This script activates the Python virtual environment and runs the test

Write-Host "TradingView Stock Data Fetcher" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "This script uses MCP Chrome DevTools to automate TradingView" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
$venvPath = "C:\Users\nyaga\Documents\.venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[ERROR] Virtual environment not found at: $venvPath" -ForegroundColor Red
    Write-Host "Please create the virtual environment first." -ForegroundColor Red
    exit 1
}

# Verify Python
Write-Host "Python Information:" -ForegroundColor Yellow
python --version
Write-Host ""

# Check required packages
Write-Host "Checking required packages..." -ForegroundColor Yellow
$packages = @("pandas", "beautifulsoup4", "requests")
$missingPackages = @()

foreach ($package in $packages) {
    $installed = python -c "import $package" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] $package installed" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $package not found" -ForegroundColor Red
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "Installing missing packages..." -ForegroundColor Yellow
    foreach ($package in $missingPackages) {
        Write-Host "  Installing $package..." -ForegroundColor Cyan
        pip install $package
    }
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Run the test script
Write-Host "Starting stock data fetch..." -ForegroundColor Green
Write-Host ""

python "C:\Users\nyaga\Documents\TVscraper\test_fetch_stocks.py"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Test completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
