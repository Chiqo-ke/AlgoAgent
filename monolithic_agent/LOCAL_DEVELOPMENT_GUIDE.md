# Local Development Setup Guide

## Overview

This guide explains how to run the AlgoAgent backend in local development mode without affecting production configurations.

---

## Quick Start

### Option 1: Using PowerShell Script (Recommended)

```powershell
cd C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
.\start_local_server.ps1
```

### Option 2: Manual Start

```powershell
# Set environment variable
$env:DJANGO_SETTINGS_MODULE = "algoagent_api.settings_local"

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

### Option 3: Command Line Argument

```powershell
python manage.py runserver --settings=algoagent_api.settings_local
```

---

## Configuration Files

### Backend Configuration

| File | Purpose | Used For |
|------|---------|----------|
| `algoagent_api/settings.py` | Base settings | Default (mixed dev/prod) |
| `algoagent_api/settings_local.py` | **Local development** | **Local work** ✅ |
| `algoagent_api/settings_production.py` | Production deployment | VPS/Production |
| `.env.local` | Local environment variables | Local secrets/config |

### Frontend Configuration

| File | Purpose | Used For |
|------|---------|----------|
| `.env.example` | Template/documentation | Reference |
| `.env.local` | **Local development** | **Local work** ✅ |
| `.env.production` | Production build | Deployed frontend |

---

## Local Development Settings

### What's Different in Local Mode?

#### Backend (`settings_local.py`)

✅ **Enabled:**
- Debug mode (`DEBUG = True`)
- SQLite database (no PostgreSQL needed)
- In-memory channels (no Redis needed)
- Local memory cache (no Redis needed)
- CORS allow all origins
- Console email backend
- Detailed logging
- No HTTPS requirements

❌ **Disabled:**
- SSL redirects
- Secure cookies
- HSTS headers
- Database connection pooling
- Redis connections

#### Frontend (`.env.local`)

✅ **Configured:**
- API URL: `http://localhost:8000/api`
- Debug mode enabled
- Development environment
- Local Google OAuth (optional)

---

## Step-by-Step Setup

### 1. Backend Setup

```powershell
# Navigate to backend directory
cd C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent

# Activate virtual environment
& C:\Users\nyaga\Documents\.venv\Scripts\Activate.ps1

# Copy local environment template (if not exists)
# Edit .env.local and add your local API keys
notepad .env.local

# Run migrations with local settings
python manage.py migrate --settings=algoagent_api.settings_local

# Create superuser (if needed)
python manage.py createsuperuser --settings=algoagent_api.settings_local

# Start local development server
.\start_local_server.ps1
# OR
python manage.py runserver --settings=algoagent_api.settings_local
```

### 2. Frontend Setup

```powershell
# Navigate to frontend directory
cd C:\Users\nyaga\Documents\Algo

# Edit .env.local if needed
notepad .env.local

# Install dependencies (if not already done)
npm install

# Start local development server
.\start_local_dev.ps1
# OR
npm run dev
```

---

## Environment Variables

### Backend (.env.local)

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=algoagent_api.settings_local
DEBUG=True

# API Keys (add your local keys)
GOOGLE_OAUTH_CLIENT_ID=your_local_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_local_client_secret

# Other local settings
LOCAL_DEVELOPMENT=True
```

### Frontend (.env.local)

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api

# Environment
VITE_ENV=development
VITE_DEBUG=true

# Features
VITE_ENABLE_MOCK_DATA=false
VITE_LOG_LEVEL=debug
```

---

## Common Development Commands

### Backend

```powershell
# Set local settings environment variable
$env:DJANGO_SETTINGS_MODULE = "algoagent_api.settings_local"

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell

# Collect static files (rarely needed in dev)
python manage.py collectstatic --noinput

# Run tests
python manage.py test

# Check for issues
python manage.py check
```

### Frontend

```powershell
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Type check
npm run type-check
```

---

## Accessing the Application

### Backend URLs (Local)

- **API Root:** http://localhost:8000/api
- **Admin Panel:** http://localhost:8000/admin
- **API Documentation:** http://localhost:8000/api/docs (if configured)
- **Strategies:** http://localhost:8000/api/strategies/
- **Backtests:** http://localhost:8000/api/backtests/

### Frontend URLs (Local)

- **Main App:** http://localhost:8080
- **Vite Dev Server:** http://localhost:8080

---

## Switching Between Environments

### Switch to Local Development

```powershell
# Backend
$env:DJANGO_SETTINGS_MODULE = "algoagent_api.settings_local"
python manage.py runserver

# Frontend
# Vite automatically uses .env.local in development mode
npm run dev
```

### Switch to Production Settings (Testing)

```powershell
# Backend
$env:DJANGO_SETTINGS_MODULE = "algoagent_api.settings_production"
python manage.py runserver

# Frontend
npm run build  # Uses .env.production
npm run preview
```

---

## Database Management

### Local Development Database

The local development environment uses **SQLite** (`db.sqlite3`). This is separate from production PostgreSQL.

**Reset Local Database:**

```powershell
# Backup current database (optional)
Copy-Item db.sqlite3 db.sqlite3.backup

# Delete database
Remove-Item db.sqlite3

# Delete migrations (if you want to start fresh)
# Be careful with this!
Remove-Item */migrations/0*.py

# Recreate migrations and database
python manage.py makemigrations --settings=algoagent_api.settings_local
python manage.py migrate --settings=algoagent_api.settings_local
python manage.py createsuperuser --settings=algoagent_api.settings_local
```

**Copy Production Data to Local (if needed):**

```powershell
# This requires production database access
# Dump from production (PostgreSQL)
pg_dump -h production-host -U algoagent -d algoagent > production_dump.sql

# Load into local SQLite (requires conversion tool)
# OR use Django fixtures:

# On production
python manage.py dumpdata --settings=algoagent_api.settings_production > data.json

# On local
python manage.py loaddata data.json --settings=algoagent_api.settings_local
```

---

## Troubleshooting

### Issue: "Can't connect to database"

**Solution:** Make sure you're using local settings:
```powershell
$env:DJANGO_SETTINGS_MODULE = "algoagent_api.settings_local"
```

### Issue: "CORS errors in frontend"

**Solution:** Local settings already allow all CORS origins. If still having issues:
1. Check frontend is calling `http://localhost:8000/api`
2. Restart backend server
3. Clear browser cache

### Issue: "Import errors or module not found"

**Solution:**
```powershell
# Make sure virtual environment is activated
& C:\Users\nyaga\Documents\.venv\Scripts\Activate.ps1

# Install/update requirements
pip install -r requirements.txt
```

### Issue: "Frontend can't find environment variables"

**Solution:**
1. Make sure `.env.local` exists in `Algo` folder
2. Restart Vite dev server
3. Environment variables must start with `VITE_`

### Issue: "Migrations out of sync"

**Solution:**
```powershell
# Run migrations with local settings
python manage.py migrate --settings=algoagent_api.settings_local

# If issues persist, check which migrations are applied
python manage.py showmigrations --settings=algoagent_api.settings_local
```

---

## Best Practices

### 1. Never Mix Configurations

- ✅ Use local settings for local development
- ✅ Use production settings for VPS deployment
- ❌ Don't modify production settings for local testing

### 2. Keep Secrets Separate

- ✅ Use `.env.local` for local secrets
- ✅ Add `.env.local` to `.gitignore`
- ❌ Never commit real API keys to git

### 3. Test Before Deploying

```powershell
# Test with production settings locally
$env:DJANGO_SETTINGS_MODULE = "algoagent_api.settings_production"
python manage.py check --deploy
```

### 4. Use Version Control

```powershell
# Before making changes
git checkout -b feature/my-feature

# After testing locally
git add .
git commit -m "Add new feature"

# Merge to main after testing
git checkout main
git merge feature/my-feature
```

---

## Configuration Summary

### Local Development ✅

- **Backend:** `settings_local.py` with SQLite
- **Frontend:** `.env.local` with localhost API
- **Database:** SQLite (file-based)
- **Cache:** Local memory
- **Channels:** In-memory
- **CORS:** Allow all
- **Debug:** Enabled

### Production 🚀

- **Backend:** `settings_production.py` with PostgreSQL
- **Frontend:** `.env.production` with production API
- **Database:** PostgreSQL
- **Cache:** Redis
- **Channels:** Redis
- **CORS:** Specific origins only
- **Debug:** Disabled
- **Security:** Full SSL/HTTPS

---

## Quick Reference

### Start Local Development

```powershell
# Terminal 1 - Backend
cd C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
.\start_local_server.ps1

# Terminal 2 - Frontend
cd C:\Users\nyaga\Documents\Algo
.\start_local_dev.ps1
```

### Access Points

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000/api
- Admin: http://localhost:8000/admin

---

## Next Steps

1. ✅ Configure `.env.local` files with your local settings
2. ✅ Start backend with local settings
3. ✅ Start frontend with local environment
4. ✅ Test the ownership access control implementation
5. ✅ Develop new features in local environment
6. ✅ Deploy to production when ready

---

## Support

If you encounter issues not covered here:

1. Check Django logs in console
2. Check browser console for frontend errors
3. Verify environment variables are set correctly
4. Ensure virtual environment is activated
5. Check that both servers are running

**Happy Developing! 🚀**
