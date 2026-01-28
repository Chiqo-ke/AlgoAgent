# Deployment Checklist - Ownership-Based Access Control

## Pre-Deployment Verification

### ✅ Code Changes
- [x] Custom permission classes created (`permissions.py`)
- [x] Strategy API ViewSets updated with authentication
- [x] Backtest API ViewSets updated with authentication
- [x] All imports added correctly
- [x] No syntax errors in code

### 📝 Documentation
- [x] Implementation guide created
- [x] Test script created
- [x] Summary document created
- [x] Deployment checklist created

---

## Deployment Steps

### Step 1: Backup Current System
```bash
cd AlgoAgent/monolithic_agent

# Backup database
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

# Commit current state to git (if using git)
git add .
git commit -m "Backup before ownership access control implementation"
```

### Step 2: Verify Database Schema
```bash
# Check that ownership fields exist (they should already be there)
python manage.py makemigrations
# Expected output: "No changes detected"

# If migrations are created, review them carefully before applying
python manage.py migrate
```

### Step 3: Test Locally

#### 3a. Start the Server
```bash
cd AlgoAgent/monolithic_agent
python manage.py runserver
```

#### 3b. Run Automated Tests
In a new terminal:
```bash
cd AlgoAgent/monolithic_agent
python test_ownership_access_control.py
```

Expected output should show:
- ✅ All isolation tests passing
- 🚫 Cross-user access correctly blocked
- ✅ Own data access working

#### 3c. Manual Browser Testing
1. Open browser to http://localhost:8000/admin
2. Create 2 test users via Django admin or API
3. Login as User 1, create strategies
4. Login as User 2, create strategies
5. Verify each user sees only their own data

### Step 4: Frontend Integration Testing

#### Update Frontend API Calls
Ensure all API calls include authentication:
```javascript
// Example: Update your API service
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth interceptor
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add error interceptor for 401
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login or refresh token
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

#### Test Frontend Functionality
- [ ] User registration works
- [ ] User login works and stores token
- [ ] Strategy list shows only user's strategies
- [ ] Strategy creation works
- [ ] Strategy update works
- [ ] Strategy deletion works
- [ ] Backtest creation works
- [ ] Backtest results show only user's data
- [ ] Logout clears token and redirects to login

### Step 5: Production Deployment

#### Before Deploying
- [ ] All tests passing
- [ ] Frontend updated and tested
- [ ] Database backup completed
- [ ] Rollback plan documented

#### Deployment
```bash
# On production server
cd /path/to/AlgoAgent/monolithic_agent

# Pull latest changes
git pull origin main

# No migrations needed (fields already exist)
# But check anyway:
python manage.py migrate

# Restart server (method depends on your setup)
# If using systemd:
sudo systemctl restart algoagent

# If using gunicorn directly:
pkill gunicorn
gunicorn monolithic_agent.wsgi:application --bind 0.0.0.0:8000
```

#### Post-Deployment Verification
```bash
# Test health endpoint
curl http://your-server.com/api/health/

# Test authentication required
curl http://your-server.com/api/strategies/
# Should return 401 Unauthorized

# Test with auth token
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://your-server.com/api/strategies/
# Should return user's strategies
```

---

## Rollback Procedure

If issues occur, you can roll back:

### Quick Rollback (Restore Previous Code)
```bash
# Restore from git
git reset --hard HEAD~1  # Go back 1 commit
# OR
git checkout <previous-commit-hash>

# Restart server
sudo systemctl restart algoagent
```

### Database Rollback (if migrations were run)
```bash
# Restore database backup
cp db.sqlite3.backup_YYYYMMDD_HHMMSS db.sqlite3

# Restart server
sudo systemctl restart algoagent
```

---

## Monitoring After Deployment

### Check for Common Issues

#### Issue 1: 401 Errors
**Symptom:** All API requests return 401 Unauthorized

**Solution:**
- Verify frontend is sending Authorization header
- Check JWT token is valid and not expired
- Verify CORS settings allow Authorization header

#### Issue 2: Empty Strategy Lists
**Symptom:** Users see no strategies even though they created some

**Solution:**
- Check that `created_by` field was properly set on existing strategies
- Run data migration if needed:
```python
# In Django shell (python manage.py shell)
from django.contrib.auth.models import User
from strategy_api.models import Strategy

# Assign orphaned strategies to a default user
default_user = User.objects.first()  # Or specific user
Strategy.objects.filter(created_by__isnull=True).update(created_by=default_user)
```

#### Issue 3: 403 Forbidden Errors
**Symptom:** Users get 403 when accessing their own data

**Solution:**
- Check permission classes are correct
- Verify user is authenticated
- Check object ownership (created_by field)

#### Issue 4: Frontend Breaks
**Symptom:** Frontend stops working after deployment

**Solution:**
- Verify all API endpoints have been updated with auth headers
- Check error handling for 401/403 responses
- Review browser console for errors

---

## Post-Deployment Tasks

### 1. Data Cleanup (if needed)
If you have existing data without ownership:
```python
# Django shell
from django.contrib.auth.models import User
from strategy_api.models import Strategy, StrategyTemplate
from backtest_api.models import BacktestConfig, BacktestRun

# Option A: Assign all to a specific user
admin_user = User.objects.get(username='admin')
Strategy.objects.filter(created_by__isnull=True).update(created_by=admin_user)
StrategyTemplate.objects.filter(created_by__isnull=True).update(created_by=admin_user)
BacktestConfig.objects.filter(created_by__isnull=True).update(created_by=admin_user)
BacktestRun.objects.filter(created_by__isnull=True).update(created_by=admin_user)

# Option B: Delete orphaned data
Strategy.objects.filter(created_by__isnull=True).delete()
# etc.
```

### 2. Update API Documentation
- [ ] Update API docs to show authentication required
- [ ] Add examples with Authorization header
- [ ] Document 401/403 error responses

### 3. Notify Users
If this is a multi-user production system:
- [ ] Notify users about authentication requirement
- [ ] Provide migration guide if needed
- [ ] Update user documentation

---

## Success Criteria

Deployment is successful if:

✅ **Security**
- Users can only see their own strategies
- Users cannot access other users' strategies
- Users cannot modify other users' data
- Unauthenticated requests are rejected

✅ **Functionality**
- User registration works
- User login works
- Strategy CRUD operations work for own data
- Backtest CRUD operations work for own data
- Frontend operates normally with auth

✅ **Performance**
- No significant performance degradation
- API response times acceptable
- Database queries optimized with indexes

✅ **Stability**
- No server errors in logs
- No database integrity issues
- No data loss

---

## Support & Troubleshooting

### Logs to Check
```bash
# Django logs (if configured)
tail -f /var/log/algoagent/django.log

# System logs
journalctl -u algoagent -f

# Nginx logs (if using nginx)
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

### Common Log Patterns

**Good Signs:**
```
POST /api/auth/login/ HTTP/1.1" 200
GET /api/strategies/ HTTP/1.1" 200
```

**Warning Signs:**
```
GET /api/strategies/ HTTP/1.1" 401  # Missing auth
GET /api/strategies/123/ HTTP/1.1" 404  # Cross-user access attempt
POST /api/strategies/ HTTP/1.1" 403  # Permission denied
```

---

## Checklist Summary

### Pre-Deployment
- [ ] Code review completed
- [ ] Local testing passed
- [ ] Frontend updated
- [ ] Database backed up
- [ ] Rollback plan ready

### Deployment
- [ ] Code deployed
- [ ] Server restarted
- [ ] Health check passed
- [ ] Authentication verified

### Post-Deployment
- [ ] User testing completed
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Data integrity verified
- [ ] Users notified (if applicable)

---

## 🎉 Deployment Complete!

Once all checkboxes are ticked, your ownership-based access control is successfully deployed and operational.

**Remember:** Monitor the system for the first 24-48 hours after deployment to catch any edge cases or issues.
