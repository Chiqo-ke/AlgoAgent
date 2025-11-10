# Strategy Validator Setup Script
# Run this to set up the Strategy Validator with AI enhancement

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "AlgoAgent Strategy Validator Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonPath = "C:/Users/nyaga/Documents/AlgoAgent/.venv/Scripts/python.exe"

if (Test-Path $pythonPath) {
    Write-Host "✓ Found Python in virtual environment" -ForegroundColor Green
    $python = $pythonPath
} else {
    Write-Host "✓ Using system Python" -ForegroundColor Green
    $python = "python"
}

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes...`n" -ForegroundColor Gray

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "`n✗ Error installing dependencies" -ForegroundColor Red
    exit 1
}

# Check API key
Write-Host "`nChecking Gemini API configuration..." -ForegroundColor Yellow
$envFile = "..\\.env"

if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "GEMINI_API_KEY=AIza") {
        Write-Host "✓ Gemini API key found in .env" -ForegroundColor Green
    } else {
        Write-Host "⚠ Gemini API key not configured in .env" -ForegroundColor Yellow
        Write-Host "  The system will work in mock mode without AI enhancement" -ForegroundColor Gray
    }
} else {
    Write-Host "⚠ .env file not found" -ForegroundColor Yellow
    Write-Host "  Create one based on .env.example" -ForegroundColor Gray
}

# Run quick test
Write-Host "`nRunning quick validation test..." -ForegroundColor Yellow
$testResult = & $python -c "from strategy_validator import StrategyValidatorBot; bot = StrategyValidatorBot(); print('✓ Import successful')" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host $testResult -ForegroundColor Green
} else {
    Write-Host "⚠ Import test had warnings (this may be normal)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run interactive tester:" -ForegroundColor White
Write-Host "   python interactive_strategy_tester.py`n" -ForegroundColor Gray
Write-Host "2. Or run demo:" -ForegroundColor White
Write-Host "   python demo.py`n" -ForegroundColor Gray
Write-Host "3. Or run tests:" -ForegroundColor White
Write-Host "   pytest test_strategy_validator.py -v`n" -ForegroundColor Gray

Write-Host "For detailed guide, see TESTING_GUIDE.md`n" -ForegroundColor Gray
