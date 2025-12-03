# AlgoAgent Quick Test Reference

## ✓ What's Working

### Database & Storage
- [x] SQLite database operational
- [x] 6 existing strategies stored
- [x] Strategy models accessible
- [x] Cache system working

### Authentication & Security
- [x] JWT token generation
- [x] User login endpoint
- [x] User info retrieval
- [x] Token-based API access

### API & Server
- [x] Django 5.2.7 running
- [x] Daphne ASGI server listening on 127.0.0.1:8000
- [x] Health check endpoint
- [x] Strategy list endpoint
- [x] REST API framework

### Production Components
- [x] StateManager - Initialized
- [x] SafeTools - Initialized
- [x] OutputValidator - Initialized (Strict mode)
- [x] SandboxRunner - Initialized (Direct execution)
- [x] GitPatchManager - Initialized

---

## ⚠ What Needs Attention

### Configuration Issues
- [ ] GEMINI_API_KEY not configured
- [ ] Backtest health endpoint missing (404)
- [ ] Strategy POST endpoint not working (405)
- [ ] Docker not available (fallback to direct execution)

### Python Warnings
- [ ] Python 3.10.11 (upgrade to 3.11+ by October 2026)
- [ ] Google API Core will drop 3.10 support soon

---

## Quick Test Commands

### Start Server
```bash
cd monolithic_agent
python manage.py runserver
# OR with auto-reload for development
python manage.py runserver
```

### Run System Tests
```bash
# Comprehensive component test
python test_system_components.py

# API integration test
python test_api_clean.py
```

### Direct API Testing

**1. Login**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"api_test_user","password":"testpass123"}'
```

**2. Get Token (save for other requests)**
```
TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**3. Check System Health**
```bash
curl -X GET http://127.0.0.1:8000/api/production/strategies/health/
```

**4. Get User Info**
```bash
curl -X GET http://127.0.0.1:8000/api/auth/user/me/ \
  -H "Authorization: Bearer $TOKEN"
```

**5. List Strategies**
```bash
curl -X GET http://127.0.0.1:8000/api/strategies/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## Configuration Checklist

### Required (Blocking)
- [ ] Add GEMINI_API_KEY to `.env`
- [ ] Fix strategy POST endpoint routing
- [ ] Add backtest health endpoint

### Recommended (Before Production)
- [ ] Install Docker
- [ ] Add OpenAI API key
- [ ] Add Anthropic API key
- [ ] Configure logging

### Nice to Have
- [ ] Upgrade to Python 3.11+
- [ ] Enable HTTP/2 in Daphne
- [ ] Set up monitoring

---

## Test Results Summary

| Category | Status | Details |
|----------|--------|---------|
| Database | PASS | SQLite working, 6 strategies |
| Auth | PASS | JWT tokens generated |
| Server | PASS | Daphne listening on 8000 |
| Health | PASS | All components initialized |
| API | PARTIAL | Core endpoints work, some missing |
| LLM | FAIL | No API keys configured |
| Docker | FAIL | Not available (optional) |

---

## How to Fix Issues

### Issue 1: LLM Integration
**Problem:** Strategy validation not working  
**Fix:** Add to `.env`:
```
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_backup_key
ANTHROPIC_API_KEY=your_backup_key
```

### Issue 2: Strategy Creation
**Problem:** POST /api/strategies/ returns 405  
**Fix:** Check `algoagent_api/urls.py` - verify POST method is registered

### Issue 3: Backtest Health
**Problem:** GET /api/backtest/health/ returns 404  
**Fix:** Add health endpoint to backtest API URLs

### Issue 4: Docker
**Problem:** SandboxRunner using unsafe direct execution  
**Fix:** Install Docker Desktop for Windows

---

## Important Ports & URLs

| Service | URL | Status |
|---------|-----|--------|
| Main API | http://127.0.0.1:8000 | Running |
| Admin | http://127.0.0.1:8000/admin | Available |
| API Auth | http://127.0.0.1:8000/api/auth/ | Working |
| Strategies | http://127.0.0.1:8000/api/strategies/ | Working (GET only) |
| Health | http://127.0.0.1:8000/api/production/strategies/health/ | Working |

---

## Key Files

**Configuration:** `.env` and `.env.example`  
**Tests:** `test_system_components.py`, `test_api_clean.py`  
**Report:** `SYSTEM_TEST_REPORT.md`  
**Django:** `monolithic_agent/manage.py`  
**Settings:** `monolithic_agent/algoagent_api/settings.py`  

---

## Next Testing Steps

1. **Configure LLM Keys** - Add GEMINI_API_KEY to .env
2. **Test Strategy Creation** - Create new strategy via API
3. **Test AI Validation** - Use new strategy creation with AI
4. **Test Backtest** - Run backtest on existing strategies
5. **Monitor Logs** - Check for any errors during operations

---

## Support & Debugging

**Check Server Logs:**
```bash
cd monolithic_agent
python manage.py runserver
# Watch output for errors
```

**Check Database:**
```bash
cd monolithic_agent
python manage.py shell
>>> from strategy_api.models import Strategy
>>> Strategy.objects.all().count()
```

**View Configuration:**
```bash
cd monolithic_agent
python manage.py shell
>>> from django.conf import settings
>>> print(settings.DEBUG)
>>> print(settings.DATABASES)
```

---

**Last Updated:** December 2, 2025  
**Test Status:** SYSTEM OPERATIONAL WITH WARNINGS
