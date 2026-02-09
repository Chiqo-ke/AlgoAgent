# Multi-Provider LLM Setup Script
# Automates the setup process for the multi-provider system

Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "   Multi-Provider LLM Integration Setup" -ForegroundColor Cyan
Write-Host "=====================================================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"
$VENV_PATH = "C:\Users\nyaga\Documents\.venv"
$PROJECT_PATH = "C:\Users\nyaga\Documents\AlgoAgent\multi_agent"

# Step 1: Check Python environment
Write-Host "[1/5] Checking Python environment..." -ForegroundColor Yellow
if (Test-Path "$VENV_PATH\Scripts\python.exe") {
    Write-Host "  ✓ Found .venv at: $VENV_PATH" -ForegroundColor Green
    $PYTHON = "$VENV_PATH\Scripts\python.exe"
    $PIP = "$VENV_PATH\Scripts\pip.exe"
} else {
    Write-Host "  ✗ .venv not found at: $VENV_PATH" -ForegroundColor Red
    Write-Host "  Please create virtual environment first:" -ForegroundColor Yellow
    Write-Host "    python -m venv $VENV_PATH" -ForegroundColor Gray
    exit 1
}

# Show Python version
$pythonVersion = & $PYTHON --version
Write-Host "  Python version: $pythonVersion" -ForegroundColor Cyan

# Step 2: Install dependencies
Write-Host "`n[2/5] Installing LLM provider packages..." -ForegroundColor Yellow
Write-Host "  Installing: openai, anthropic, google-generativeai, requests, redis" -ForegroundColor Gray

try {
    & $PIP install --quiet --upgrade pip 2>$null
    & $PIP install --quiet openai anthropic google-generativeai requests redis 2>$null
    Write-Host "  ✓ All packages installed successfully" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Some packages may have failed to install" -ForegroundColor Yellow
    Write-Host "  Run manually: pip install openai anthropic google-generativeai requests redis" -ForegroundColor Gray
}

# Step 3: Verify package installation
Write-Host "`n[3/5] Verifying installed packages..." -ForegroundColor Yellow
$packages = @("openai", "anthropic", "google", "requests", "redis")
foreach ($pkg in $packages) {
    $check = & $PIP show $pkg 2>$null
    if ($check) {
        Write-Host "  ✓ $pkg installed" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $pkg NOT installed" -ForegroundColor Red
    }
}

# Step 4: Check Redis
Write-Host "`n[4/5] Checking Redis server..." -ForegroundColor Yellow
$dockerCheck = docker ps 2>$null | Select-String "redis-llm"
if ($dockerCheck) {
    Write-Host "  ✓ Redis container 'redis-llm' is running" -ForegroundColor Green
} else {
    Write-Host "  ✗ Redis container not found" -ForegroundColor Yellow
    Write-Host "  Starting Redis container..." -ForegroundColor Gray
    try {
        docker run -d --name redis-llm -p 6379:6379 redis:latest 2>$null | Out-Null
        Start-Sleep -Seconds 2
        Write-Host "  ✓ Redis started successfully" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Could not start Redis. Please run manually:" -ForegroundColor Yellow
        Write-Host "    docker run -d --name redis-llm -p 6379:6379 redis:latest" -ForegroundColor Gray
    }
}

# Step 5: Check configuration files
Write-Host "`n[5/5] Checking configuration files..." -ForegroundColor Yellow

# Check .env
$envPath = Join-Path $PROJECT_PATH ".env"
if (Test-Path $envPath) {
    Write-Host "  ✓ .env file exists" -ForegroundColor Green
    
    # Check for API keys
    $hasOpenCode = Select-String -Path $envPath -Pattern "API_KEY_opencode" -Quiet
    $hasGitHub = Select-String -Path $envPath -Pattern "API_KEY_github-models" -Quiet
    
    if ($hasOpenCode) {
        Write-Host "    • OpenCode keys configured" -ForegroundColor Cyan
    } else {
        Write-Host "    ⚠ No OpenCode keys found" -ForegroundColor Yellow
    }
    
    if ($hasGitHub) {
        Write-Host "    • GitHub Models keys configured" -ForegroundColor Cyan
    } else {
        Write-Host "    ⚠ No GitHub Models keys found" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ .env file not found" -ForegroundColor Red
}

# Check keys.json
$keysPath = Join-Path $PROJECT_PATH "keys.json"
if (Test-Path $keysPath) {
    Write-Host "  ✓ keys.json file exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ keys.json file not found" -ForegroundColor Red
}

# Summary
Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Cyan
Write-Host "=====================================================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Get API keys from https://opencode.ai" -ForegroundColor White
Write-Host "  2. Add keys to .env file:" -ForegroundColor White
Write-Host "     API_KEY_opencode-claude-01=opencode_YOUR_KEY" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Test your setup:" -ForegroundColor White
Write-Host "     cd $PROJECT_PATH" -ForegroundColor Gray
Write-Host "     $PYTHON test_multi_provider.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Read the guide:" -ForegroundColor White
Write-Host "     MULTI_PROVIDER_SETUP_COMPLETE.md" -ForegroundColor Gray
Write-Host "`n=====================================================================" -ForegroundColor Cyan

# Offer to run tests
Write-Host "`nWould you like to run the test suite now? (Y/N): " -ForegroundColor Yellow -NoNewline
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host "`nRunning tests...`n" -ForegroundColor Cyan
    Set-Location $PROJECT_PATH
    & $PYTHON test_multi_provider.py
} else {
    Write-Host "`nSkipping tests. Run manually when ready:" -ForegroundColor Gray
    Write-Host "  cd $PROJECT_PATH" -ForegroundColor Gray
    Write-Host "  $PYTHON test_multi_provider.py" -ForegroundColor Gray
}

Write-Host "`nDone! 🎉`n" -ForegroundColor Green
