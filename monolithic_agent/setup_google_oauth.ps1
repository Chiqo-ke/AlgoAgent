# Google OAuth Setup Script for AlgoAgent
# Run this script after configuring your Google OAuth credentials

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   AlgoAgent - Google OAuth Setup Script" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-Not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  Please edit the .env file and add your Google OAuth credentials:" -ForegroundColor Yellow
    Write-Host "   - GOOGLE_OAUTH_CLIENT_ID" -ForegroundColor Yellow
    Write-Host "   - GOOGLE_OAUTH_CLIENT_SECRET" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 0
}

# Check if Google OAuth credentials are set
$envContent = Get-Content ".env" -Raw
if ($envContent -match "GOOGLE_OAUTH_CLIENT_ID=your-google-client-id" -or 
    $envContent -notmatch "GOOGLE_OAUTH_CLIENT_ID=.+") {
    Write-Host "⚠️  Google OAuth credentials not configured in .env" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please update your .env file with:" -ForegroundColor Yellow
    Write-Host "   GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com" -ForegroundColor Yellow
    Write-Host "   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Get credentials from: https://console.cloud.google.com/apis/credentials" -ForegroundColor Cyan
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 0
    }
}

Write-Host "Step 1: Installing required packages..." -ForegroundColor Cyan
pip install django-allauth requests

Write-Host ""
Write-Host "Step 2: Running database migrations..." -ForegroundColor Cyan
python manage.py migrate

Write-Host ""
Write-Host "Step 3: Setting up Django Site..." -ForegroundColor Cyan

# Create a Python script to set up the site
$siteSetup = @"
from django.contrib.sites.models import Site
import sys

try:
    site = Site.objects.get_or_create(id=1)[0]
    site.domain = 'localhost:8000'
    site.name = 'AlgoAgent'
    site.save()
    print('✓ Site configured successfully')
    sys.exit(0)
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"@

$siteSetup | python manage.py shell

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   Google OAuth Setup Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Make sure your Google Cloud Console is configured:" -ForegroundColor White
Write-Host "   - Authorized JavaScript origins: http://localhost:5173" -ForegroundColor Gray
Write-Host "   - Authorized redirect URIs: http://localhost:5173/auth/callback" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the Django server:" -ForegroundColor White
Write-Host "   python manage.py runserver" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the frontend (in Algo directory):" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test by visiting: http://localhost:5173/login" -ForegroundColor White
Write-Host ""
Write-Host "📖 For detailed setup instructions, see GOOGLE_OAUTH_SETUP.md" -ForegroundColor Cyan
Write-Host ""
