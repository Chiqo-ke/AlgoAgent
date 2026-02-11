# Production Issue Troubleshooting Guide

## 🚨 Current Issues
- **503 Service Unavailable**: Backend service not responding
- **504 Gateway Timeout**: Requests timing out (especially strategy generation)
- **CORS Error**: No 'Access-Control-Allow-Origin' header

---

## 📋 Quick Fix Checklist

### On Your VPS (SSH Required)

#### 1. Upload and Run Diagnostic Script
```bash
# Upload the diagnostic script to your VPS
scp C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent\deployment\fix_production_issues.sh root@your-vps-ip:/tmp/

# SSH into VPS
ssh root@your-vps-ip

# Make executable and run
chmod +x /tmp/fix_production_issues.sh
bash /tmp/fix_production_issues.sh
```

This will check all services and identify the exact problem.

#### 2. Check Service Status
```bash
sudo systemctl status algoagent-daphne
```

**If service is failed/inactive:**
```bash
# View error logs
sudo journalctl -u algoagent-daphne -n 100 --no-pager

# Try to restart
sudo systemctl restart algoagent-daphne

# Check status again
sudo systemctl status algoagent-daphne
```

#### 3. Verify Environment File
```bash
# Check if file exists
ls -la /etc/algoagent/.env

# Check CORS configuration (CRITICAL)
sudo grep -E "CORS|CSRF" /etc/algoagent/.env
```

**Required format (must include `https://` scheme):**
```bash
CORS_ALLOWED_ORIGINS=https://algoai.biz,https://www.algoai.biz,https://api.algoai.biz
CSRF_TRUSTED_ORIGINS=https://algoai.biz,https://www.algoai.biz,https://api.algoai.biz
ALLOWED_WEBSOCKET_ORIGINS=algoai.biz,api.algoai.biz,www.algoai.biz
```

**If incorrect, fix it:**
```bash
sudo nano /etc/algoagent/.env
# Update the CORS lines as shown above
# Save: Ctrl+X, Y, Enter

# Restart service
sudo systemctl restart algoagent-daphne
```

#### 4. Fix Nginx Timeouts for AI Operations
```bash
sudo nano /etc/nginx/sites-available/algoagent
```

**Find this section (around line 58-60):**
```nginx
# Timeouts
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

**Change to:**
```nginx
# Timeouts - Increased for AI/LLM operations
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;
```

**Save and reload:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Restart All Services (Clean Restart)
```bash
sudo systemctl restart postgresql
sudo systemctl restart redis-server
sudo systemctl restart algoagent-daphne
sudo systemctl restart nginx

# Verify all are running
sudo systemctl status algoagent-daphne nginx postgresql redis-server
```

#### 6. Test Backend Connectivity
```bash
# Test local connection
curl -I http://127.0.0.1:8000/health/
# Should return: HTTP/1.1 200 OK

# Test external HTTPS
curl -I https://api.algoai.biz/health/
# Should return: HTTP/2 200

# Test CORS headers
curl -H "Origin: https://www.algoai.biz" -v https://api.algoai.biz/api/ 2>&1 | grep -i "access-control"
# Should show: access-control-allow-origin: https://www.algoai.biz
```

---

## 🔍 Common Issues and Solutions

### Issue 1: Daphne Service Won't Start

**Symptoms:**
- `systemctl status algoagent-daphne` shows "failed"
- Port 8000 not listening

**Solution:**
```bash
# Check detailed logs
sudo journalctl -u algoagent-daphne -n 50 --no-pager

# Common causes:
# 1. Missing SECRET_KEY
sudo grep "DJANGO_SECRET_KEY" /etc/algoagent/.env

# 2. Database not accessible
sudo -u postgres psql -d algoagent -c "SELECT 1;"

# 3. Port already in use
sudo lsof -i :8000
# If something else is using port 8000, kill it:
sudo kill -9 <PID>

# 4. Permission issues
sudo chown -R algoagent:algoagent /opt/algoagent
sudo chown -R algoagent:algoagent /var/log/algoagent

# Try starting again
sudo systemctl restart algoagent-daphne
```

### Issue 2: CORS Errors Persist

**Symptoms:**
- Frontend shows: "No 'Access-Control-Allow-Origin' header"
- Backend is running fine

**Solution:**
```bash
# 1. Verify CORS in .env (must have https://)
sudo nano /etc/algoagent/.env

# Change:
CORS_ALLOWED_ORIGINS=algoai.biz,www.algoai.biz  # ❌ WRONG

# To:
CORS_ALLOWED_ORIGINS=https://algoai.biz,https://www.algoai.biz  # ✅ CORRECT

# 2. Check CSRF as well
CSRF_TRUSTED_ORIGINS=https://algoai.biz,https://www.algoai.biz

# 3. Restart Daphne
sudo systemctl restart algoagent-daphne

# 4. Clear browser cache or test in incognito
```

### Issue 3: 504 Gateway Timeout on Strategy Generation

**Symptoms:**
- `/api/strategies/api/generate_strategy_unified/` times out after 60 seconds
- Other endpoints work fine

**Solution:**
```bash
# Increase nginx proxy timeouts (already shown above in step 4)

# Also check if backend timeout needs adjustment
sudo nano /etc/algoagent/.env

# Add or update:
STRATEGY_GENERATION_TIMEOUT=300  # 5 minutes
```

**In Django settings (if needed), edit:**
```bash
sudo -u algoagent nano /opt/algoagent/AlgoAgent/monolithic_agent/algoagent_api/settings_production.py

# Add at the end:
STRATEGY_GENERATION_TIMEOUT = int(os.environ.get('STRATEGY_GENERATION_TIMEOUT', 300))
```

### Issue 4: Database Connection Errors

**Symptoms:**
- Logs show: "could not connect to server"
- Backend can't reach PostgreSQL

**Solution:**
```bash
# 1. Check PostgreSQL is running
sudo systemctl status postgresql

# 2. Test connection
sudo -u postgres psql -d algoagent -c "SELECT version();"

# 3. Verify credentials in .env
sudo grep "DB_" /etc/algoagent/.env

# 4. Reset password if needed
sudo -u postgres psql
ALTER USER algoagent WITH PASSWORD 'new_secure_password';
\q

# Update .env with new password
sudo nano /etc/algoagent/.env
# DB_PASSWORD=new_secure_password

# Restart
sudo systemctl restart algoagent-daphne
```

### Issue 5: Redis Connection Errors

**Symptoms:**
- WebSocket connections fail
- Logs show Redis connection errors

**Solution:**
```bash
# 1. Check Redis is running
sudo systemctl status redis-server

# 2. Test connection
redis-cli ping
# Should return: PONG

# 3. If not running
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 4. Restart Daphne
sudo systemctl restart algoagent-daphne
```

---

## 📊 Monitoring Commands

### Real-time Logs
```bash
# Daphne application logs
sudo journalctl -u algoagent-daphne -f

# Django application logs
sudo tail -f /var/log/algoagent/django.log

# Django errors
sudo tail -f /var/log/algoagent/django_error.log

# Nginx access logs
sudo tail -f /var/log/nginx/algoagent-access.log

# Nginx errors
sudo tail -f /var/log/nginx/algoagent-error.log

# All errors together
sudo tail -f /var/log/algoagent/django_error.log /var/log/nginx/algoagent-error.log
```

### Check What's Running
```bash
# All services
sudo systemctl status algoagent-daphne nginx postgresql redis-server

# What's on port 8000
sudo netstat -tlnp | grep 8000

# Resource usage
htop
```

---

## 🚀 After Fixing

### Test Your API
```bash
# 1. Health check
curl https://api.algoai.biz/health/

# 2. API root
curl https://api.algoai.biz/api/

# 3. Test strategy endpoint (may take 30-60 seconds)
curl -X POST https://api.algoai.biz/api/strategies/api/generate_strategy_unified/ \
  -H "Content-Type: application/json" \
  -H "Origin: https://www.algoai.biz" \
  -d '{"test": "data"}'
```

### From Your Frontend
1. Open browser DevTools (F12)
2. Go to Network tab
3. Try the strategy generation feature
4. Check:
   - Response status (should be 200, not 503/504)
   - Response headers (should include `access-control-allow-origin`)
   - No CORS errors in console

---

## 📝 Prevention

### 1. Set Up Monitoring
```bash
# Create a simple uptime monitor script
sudo nano /opt/algoagent/monitor.sh
```

```bash
#!/bin/bash
# Check if services are running and restart if needed

services=("algoagent-daphne" "nginx" "postgresql" "redis-server")

for service in "${services[@]}"; do
    if ! systemctl is-active --quiet "$service"; then
        echo "$(date): $service is down, restarting..."
        systemctl restart "$service"
        echo "$(date): $service restarted"
    fi
done
```

```bash
# Make executable
sudo chmod +x /opt/algoagent/monitor.sh

# Add to crontab (runs every 5 minutes)
sudo crontab -e
# Add line:
*/5 * * * * /opt/algoagent/monitor.sh >> /var/log/algoagent/monitor.log 2>&1
```

### 2. Set Up Log Rotation
```bash
sudo nano /etc/logrotate.d/algoagent
```

```
/var/log/algoagent/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 algoagent algoagent
    sharedscripts
}
```

### 3. Regular Database Backups
```bash
# Create backup script
sudo nano /opt/algoagent/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/algoagent/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump algoagent > "$BACKUP_DIR/algoagent_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "algoagent_*.sql" -mtime +7 -delete

echo "$(date): Backup completed - algoagent_$DATE.sql"
```

```bash
sudo chmod +x /opt/algoagent/backup.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add:
0 2 * * * /opt/algoagent/backup.sh >> /var/log/algoagent/backup.log 2>&1
```

---

## 📞 Still Having Issues?

If problems persist after following these steps, collect diagnostic information:

```bash
# Collect all diagnostic info
bash /tmp/fix_production_issues.sh > /tmp/diagnostic_output.txt 2>&1

# Add recent logs
echo "=== DAPHNE LOGS ===" >> /tmp/diagnostic_output.txt
sudo journalctl -u algoagent-daphne -n 100 --no-pager >> /tmp/diagnostic_output.txt

echo "=== DJANGO ERRORS ===" >> /tmp/diagnostic_output.txt
sudo tail -n 100 /var/log/algoagent/django_error.log >> /tmp/diagnostic_output.txt 2>&1

echo "=== NGINX ERRORS ===" >> /tmp/diagnostic_output.txt
sudo tail -n 100 /var/log/nginx/algoagent-error.log >> /tmp/diagnostic_output.txt 2>&1

# Download to your local machine
# Then from your Windows machine:
scp root@your-vps-ip:/tmp/diagnostic_output.txt C:\Users\nyaga\Documents\
```

Share the `diagnostic_output.txt` file for further analysis.

---

## ✅ Success Indicators

Your system is working correctly when:
- [ ] `systemctl status algoagent-daphne` shows "active (running)"
- [ ] `curl http://127.0.0.1:8000/health/` returns 200 OK
- [ ] `curl https://api.algoai.biz/health/` returns 200 OK
- [ ] No CORS errors in browser console
- [ ] Strategy generation completes (may take 30-60 seconds)
- [ ] WebSocket connections work
- [ ] All logs show normal operation (no errors)
