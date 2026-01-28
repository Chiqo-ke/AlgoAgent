# Start AlgoAgent Backend Server - Local Development Mode
# ========================================================
# This script starts the Django development server with local settings

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  🚀 Starting AlgoAgent Backend - LOCAL DEVELOPMENT MODE" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Set environment variable for local development settings
$env:DJANGO_SETTINGS_MODULE = "algoagent_api.settings_local"

Write-Host ""
Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   Settings Module: $env:DJANGO_SETTINGS_MODULE" -ForegroundColor Green
Write-Host "   Database: SQLite (db.sqlite3)" -ForegroundColor Green
Write-Host "   Debug Mode: Enabled" -ForegroundColor Green
Write-Host "   CORS: Allow All Origins" -ForegroundColor Green
Write-Host ""

# Check if virtual environment is activated
if ($env:VIRTUAL_ENV) {
    Write-Host "✅ Virtual environment active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: No virtual environment detected" -ForegroundColor Yellow
    Write-Host "   Attempting to activate .venv..." -ForegroundColor Yellow
    
    # Try to activate virtual environment
    $venv_paths = @(
        "C:\Users\nyaga\Documents\.venv\Scripts\Activate.ps1",
        ".\.venv\Scripts\Activate.ps1",
        "..\.venv\Scripts\Activate.ps1"
    )
    
    foreach ($venv_path in $venv_paths) {
        if (Test-Path $venv_path) {
            Write-Host "   Found virtual environment at: $venv_path" -ForegroundColor Green
            & $venv_path
            break
        }
    }
}

Write-Host ""
Write-Host "🔍 Running migrations (if needed)..." -ForegroundColor Cyan
python manage.py migrate --settings=algoagent_api.settings_local

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  🌐 Starting Django Development Server" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "   Local:   http://localhost:8000" -ForegroundColor Green
Write-Host "   Network: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host ""
Write-Host "   API:     http://localhost:8000/api" -ForegroundColor Yellow
Write-Host "   Admin:   http://localhost:8000/admin" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Start the development server
python manage.py runserver --settings=algoagent_api.settings_local 0.0.0.0:8000
