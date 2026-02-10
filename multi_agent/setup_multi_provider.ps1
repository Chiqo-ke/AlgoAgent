# Multi-Provider LLM Setup Script
# Uses .venv from Documents folder

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Multi-Provider LLM Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Configuration
$venvPath = "C:\Users\nyaga\Documents\.venv"
$pythonExe = "$venvPath\Scripts\python.exe"
$pipExe = "$venvPath\Scripts\pip.exe"
$projectRoot = "C:\Users\nyaga\Documents\AlgoAgent\multi_agent"

# Step 1: Verify Python Environment
Write-Host "Step 1: Verifying Python environment..." -ForegroundColor Yellow

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "Please create it first with: python -m venv C:\Users\nyaga\Documents\.venv" -ForegroundColor Red
    exit 1
}

Write-Host "  Found Python: $pythonExe" -ForegroundColor Green

# Get Python version
$pythonVersion = & $pythonExe --version
Write-Host "  Version: $pythonVersion" -ForegroundColor Green

# Step 2: Install Required Packages
Write-Host "`nStep 2: Installing required packages..." -ForegroundColor Yellow

$packages = @(
    "anthropic",
    "google-generativeai",
    "openai>=1.0.0",
    "requests>=2.31.0",
    "redis>=4.5.0",
    "python-dotenv>=1.0.0"
)

foreach ($pkg in $packages) {
    Write-Host "  Installing $pkg..." -ForegroundColor Cyan
    & $pipExe install $pkg --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    OK" -ForegroundColor Green
    } else {
        Write-Host "    WARNING: Failed to install $pkg" -ForegroundColor Yellow
    }
}

# Step 3: Check Redis
Write-Host "`nStep 3: Checking Redis server..." -ForegroundColor Yellow

try {
    $redisContainer = docker ps --filter "name=redis-llm" --format "{{.Names}}"
    if ($redisContainer -eq "redis-llm") {
        Write-Host "  Redis container 'redis-llm' is running" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Redis container not found" -ForegroundColor Yellow
        Write-Host "  Starting Redis container..." -ForegroundColor Cyan
        
        docker run -d --name redis-llm -p 6379:6379 redis:latest
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    Redis started successfully" -ForegroundColor Green
        } else {
            Write-Host "    ERROR: Failed to start Redis" -ForegroundColor Red
            Write-Host "    You may need to start it manually" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  WARNING: Docker not available or Redis check failed" -ForegroundColor Yellow
    Write-Host "  Ensure Redis is running on localhost:6379" -ForegroundColor Yellow
}

# Step 4: Validate Configuration Files
Write-Host "`nStep 4: Validating configuration files..." -ForegroundColor Yellow

$envPath = "$projectRoot\.env"
$keysPath = "$projectRoot\keys.json"

if (Test-Path $envPath) {
    Write-Host "  Found .env file" -ForegroundColor Green
    
    # Check for OpenCode API key
    $envContent = Get-Content $envPath -Raw
    if ($envContent -match "API_KEY_opencode") {
        Write-Host "    OpenCode API key configured" -ForegroundColor Green
    } else {
        Write-Host "    WARNING: No OpenCode API key found in .env" -ForegroundColor Yellow
        Write-Host "    Add: API_KEY_opencode-claude-01=opencode_YOUR_KEY_HERE" -ForegroundColor Cyan
    }
} else {
    Write-Host "  ERROR: .env file not found" -ForegroundColor Red
}

if (Test-Path $keysPath) {
    Write-Host "  Found keys.json file" -ForegroundColor Green
} else {
    Write-Host "  ERROR: keys.json file not found" -ForegroundColor Red
}

# Step 5: Run Tests (Optional)
Write-Host "`nStep 5: Run tests? (y/n): " -ForegroundColor Yellow -NoNewline
$runTests = Read-Host

if ($runTests -eq "y" -or $runTests -eq "Y") {
    Write-Host "`nRunning provider tests..." -ForegroundColor Cyan
    
    Set-Location $projectRoot
    & $pythonExe test_multi_provider.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nTests passed!" -ForegroundColor Green
    } else {
        Write-Host "`nTests failed or incomplete" -ForegroundColor Yellow
        Write-Host "This is expected if API keys are not configured yet" -ForegroundColor Cyan
    }
} else {
    Write-Host "  Skipping tests" -ForegroundColor Gray
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Get OpenCode API key from: https://opencode.ai" -ForegroundColor Cyan
Write-Host "  2. Add to .env: API_KEY_opencode-claude-01=opencode_YOUR_KEY_HERE" -ForegroundColor Cyan
Write-Host "  3. Update keys.json with your provider configurations" -ForegroundColor Cyan
Write-Host "  4. Test with: " -NoNewline -ForegroundColor Cyan
Write-Host "$pythonExe test_multi_provider.py" -ForegroundColor White
Write-Host "  5. Run your workflow: " -NoNewline -ForegroundColor Cyan
Write-Host "$pythonExe cli.py" -ForegroundColor White

Write-Host "`nDone!`n" -ForegroundColor Green
