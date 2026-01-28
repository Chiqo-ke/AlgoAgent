# Local Development Configuration - Quick Start

## 🚀 Quick Start (2 Commands)

### Start Backend (Local Mode)
```powershell
cd C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
.\start_local_server.ps1
```

### Start Frontend (Local Mode)
```powershell
cd C:\Users\nyaga\Documents\Algo
.\start_local_dev.ps1
```

That's it! Your local development environment is running.

---

## 📁 Files Created

### Backend Files
- ✅ `algoagent_api/settings_local.py` - Local development Django settings
- ✅ `.env.local` - Local environment variables for backend
- ✅ `start_local_server.ps1` - Quick start script for local backend
- ✅ `LOCAL_DEVELOPMENT_GUIDE.md` - Comprehensive guide

### Frontend Files
- ✅ `.env.local` - Local environment variables (API: localhost:8000)
- ✅ `.env.production` - Production environment variables
- ✅ `start_local_dev.ps1` - Quick start script for local frontend
- ✅ Updated `package.json` - Added dev:local and build:prod scripts

---

## 🔧 Configuration Summary

### Local Development
| Component | Configuration | Value |
|-----------|--------------|-------|
| **Backend** | Settings | `settings_local.py` |
| | Database | SQLite (db.sqlite3) |
| | Port | 8000 |
| | Debug | Enabled |
| | CORS | Allow All |
| **Frontend** | Environment | `.env.local` |
| | API URL | http://localhost:8000/api |
| | Port | 8080 |
| | Mode | Development |

### Production (Unchanged)
| Component | Configuration | Value |
|-----------|--------------|-------|
| **Backend** | Settings | `settings_production.py` |
| | Database | PostgreSQL |
| | Port | 8000 |
| | Debug | Disabled |
| | CORS | Specific Origins |
| **Frontend** | Environment | `.env.production` |
| | API URL | https://api.algoai.biz/api |
| | Port | N/A (built) |
| | Mode | Production |

---

## 🎯 Key Features

### Backend Local Settings
✅ **No Production Impact**
- Separate `settings_local.py` file
- Uses SQLite instead of PostgreSQL
- In-memory cache/channels (no Redis needed)
- CORS allows all origins
- Debug mode enabled
- Console email backend

✅ **Production Settings Unchanged**
- `settings_production.py` remains intact
- PostgreSQL configuration preserved
- Redis configuration preserved
- Security settings unchanged

### Frontend Environment Files
✅ **Environment-Based Configuration**
- `.env.local` for development (localhost API)
- `.env.production` for production builds
- Vite automatically uses correct file based on mode

---

## 📝 NPM Scripts

```json
"dev"         → Start dev server (uses .env.local by default)
"dev:local"   → Start dev server explicitly in local mode
"dev:prod"    → Start dev server in production mode (testing)
"build"       → Build for production (uses .env.production)
"build:prod"  → Build for production explicitly
"build:dev"   → Build for development
```

---

## 🔄 How to Switch Environments

### Backend

**Local Development:**
```powershell
# Option 1: Use script (recommended)
.\start_local_server.ps1

# Option 2: Set env variable
$env:DJANGO_SETTINGS_MODULE = "algoagent_api.settings_local"
python manage.py runserver

# Option 3: Command line argument
python manage.py runserver --settings=algoagent_api.settings_local
```

**Production Testing:**
```powershell
$env:DJANGO_SETTINGS_MODULE = "algoagent_api.settings_production"
python manage.py runserver
```

### Frontend

**Local Development:**
```powershell
npm run dev          # Uses .env.local automatically
npm run dev:local    # Explicit local mode
```

**Production Build:**
```powershell
npm run build        # Uses .env.production
npm run build:prod   # Explicit production build
```

---

## 🛠️ Common Tasks

### First Time Setup

```powershell
# Backend
cd AlgoAgent\monolithic_agent
python -m venv .venv  # If not already created
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate --settings=algoagent_api.settings_local
python manage.py createsuperuser --settings=algoagent_api.settings_local

# Frontend
cd Algo
npm install
# Edit .env.local if needed
```

### Daily Development

```powershell
# Start both servers
# Terminal 1:
cd AlgoAgent\monolithic_agent
.\start_local_server.ps1

# Terminal 2:
cd Algo
.\start_local_dev.ps1
```

### Reset Local Database

```powershell
cd AlgoAgent\monolithic_agent
Remove-Item db.sqlite3
python manage.py migrate --settings=algoagent_api.settings_local
python manage.py createsuperuser --settings=algoagent_api.settings_local
```

---

## 🔍 Verification

After starting both servers, verify:

1. **Backend Running:**
   - Visit: http://localhost:8000/admin
   - Check console shows: "LOCAL DEVELOPMENT SETTINGS LOADED"
   - Database: SQLite

2. **Frontend Running:**
   - Visit: http://localhost:8080
   - Check browser network tab: API calls go to `localhost:8000`
   - Environment: Development mode

3. **API Connection:**
   - Frontend can reach backend at `http://localhost:8000/api`
   - No CORS errors in browser console

---

## ⚠️ Important Notes

### What NOT to Do
- ❌ Don't modify `settings_production.py` for local development
- ❌ Don't commit `.env.local` to git (it's in .gitignore)
- ❌ Don't use production API keys in local environment
- ❌ Don't run production builds in development

### What TO Do
- ✅ Use `settings_local.py` for all local development
- ✅ Keep production settings separate and unchanged
- ✅ Use `.env.local` for local environment variables
- ✅ Test with local settings before deploying
- ✅ Use version control branches for features

---

## 📚 Additional Resources

- **Detailed Guide:** `LOCAL_DEVELOPMENT_GUIDE.md`
- **Ownership Access Control:** `OWNERSHIP_ACCESS_CONTROL_GUIDE.md`
- **Implementation Summary:** `IMPLEMENTATION_SUMMARY.md`
- **Deployment Checklist:** `DEPLOYMENT_CHECKLIST.md`

---

## 🆘 Troubleshooting

### Backend won't start
```powershell
# Check settings module
echo $env:DJANGO_SETTINGS_MODULE  # Should show settings_local

# Run migrations
python manage.py migrate --settings=algoagent_api.settings_local

# Check for errors
python manage.py check --settings=algoagent_api.settings_local
```

### Frontend can't connect to backend
```powershell
# Check .env.local has correct API URL
cat .env.local  # Should show http://localhost:8000/api

# Restart Vite dev server
# Press Ctrl+C, then run again:
npm run dev
```

### CORS errors
- Local settings already allow all CORS
- Make sure backend is using `settings_local.py`
- Clear browser cache
- Restart both servers

---

## ✨ Summary

You now have:
- ✅ Separate local development configuration
- ✅ Production configuration unchanged
- ✅ Easy-to-use startup scripts
- ✅ Environment-based frontend configuration
- ✅ No Redis/PostgreSQL required for local dev
- ✅ Full development environment ready

**Start coding with confidence!** 🚀
