# PowerShell startup script for AlgoCLI
# Run this to start the CLI application

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "  " -NoNewline
Write-Host "🌟 AlgoCLI - Multi-Agent Workflow Manager 🌟" -ForegroundColor Magenta
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if in AlgoCLI directory
if (-not (Test-Path "app.py")) {
    Write-Host "❌ Error: Please run this script from the AlgoCLI directory" -ForegroundColor Red
    exit 1
}

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8 or higher" -ForegroundColor Red
    exit 1
}

# Check if requirements are installed
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow

$requirementsInstalled = $true
$packages = @("textual", "rich", "httpx", "pydantic", "python-dotenv")

foreach ($package in $packages) {
    try {
        python -c "import $($package.Replace('-', '_'))" 2>$null
        Write-Host "  ✓ $package" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ $package (missing)" -ForegroundColor Red
        $requirementsInstalled = $false
    }
}

if (-not $requirementsInstalled) {
    Write-Host ""
    Write-Host "Installing missing dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Check .env file
Write-Host ""
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "✓ .env file created" -ForegroundColor Green
    } else {
        Write-Host "⚠ No .env file found (using defaults)" -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ .env file exists" -ForegroundColor Green
}

# Check if API server is running
Write-Host ""
Write-Host "Checking API server..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing 2>$null
    Write-Host "✓ API server is running" -ForegroundColor Green
} catch {
    Write-Host "⚠ API server not responding (http://localhost:8000)" -ForegroundColor Yellow
    Write-Host "  You may need to start the multi-agent API server:" -ForegroundColor Yellow
    Write-Host "  cd ..\AlgoAgent" -ForegroundColor Cyan
    Write-Host "  python -m uvicorn multi_agent.api_server:app --host 0.0.0.0 --port 8000" -ForegroundColor Cyan
}

# Start the application
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "  Starting AlgoCLI..." -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

python run.py
