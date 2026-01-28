# AlgoAgent VPS Deployment Guide

Complete step-by-step guide to deploy your Django backend on Ubuntu VPS with production-grade security and configuration.

## 📋 Prerequisites

- Ubuntu 22.04 or 24.04 VPS with root access
- Domain name pointed to your VPS IP address
- PuTTY or SSH client installed
- Basic knowledge of Linux commands

---

## 🚀 Part 1: Initial VPS Setup (One-Time)
 
### Step 1: Connect to Your VPS via SSH

Using PuTTY on Windows:
1. Open PuTTY
2. Enter your VPS IP address
3. Port: 22
4. Click "Open"
5. Login with your root credentials

Or using Windows PowerShell/Command Prompt:
```bash
ssh root@your-vps-ip-address
```

### Step 2: Update System Packages

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Reboot if kernel was updated (optional but recommended)
sudo reboot
```

Wait 1-2 minutes, then reconnect via SSH.

### Step 3: Install Required Software

```bash
# Add deadsnakes PPA for Python 3.11 (if Ubuntu 20.04/22.04)
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11 and development tools
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip build-essential libpq-dev python3-dev git curl

# Install PostgreSQL database
sudo apt install -y postgresql postgresql-contrib

# Install Redis for Django Channels
sudo apt install -y redis-server

# Install Nginx web server
sudo apt install -y nginx

# Install Certbot for SSL certificates
sudo apt install -y certbot python3-certbot-nginx

# Install UFW firewall
sudo apt install -y ufw
```

### Step 4: Configure Firewall

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Check firewall status
sudo ufw status
```

Expected output:
```
Status: active

To                         Action      From
--                         ------      ----
OpenSSH                    ALLOW       Anywhere
Nginx Full                 ALLOW       Anywhere
```

### Step 5: Create Application User

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash algoagent

# Set password for algoagent user (required for sudo operations)
sudo passwd algoagent
# Enter a strong password when prompted

# Create application directory
sudo mkdir -p /opt/algoagent

# Create log directory
sudo mkdir -p /var/log/algoagent

# Set ownership
sudo chown -R algoagent:algoagent /opt/algoagent
sudo chown -R algoagent:algoagent /var/log/algoagent
```

### Step 6: Configure PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt, run these commands:
```

```sql
-- Create database
CREATE DATABASE algoagent;

-- Create user with strong password (CHANGE 'your_secure_password_here')
CREATE USER algoagent WITH ENCRYPTED PASSWORD 'your_secure_password_here';

-- Set encoding and timezone
ALTER ROLE algoagent SET client_encoding TO 'utf8';
ALTER ROLE algoagent SET default_transaction_isolation TO 'read committed';
ALTER ROLE algoagent SET timezone TO 'UTC';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE algoagent TO algoagent;
ALTER DATABASE algoagent OWNER TO algoagent;

-- Exit PostgreSQL
\q
```

**Save your database password securely!**

### Step 7: Configure Redis

```bash
# Enable Redis to start on boot
sudo systemctl enable redis-server

# Start Redis
sudo systemctl start redis-server

# Check Redis status
sudo systemctl status redis-server
```

Should show "active (running)".

### Step 8: Install TA-Lib (Trading Analysis Library)

```bash
# Download TA-Lib source
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz

# Extract and install
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# Update library cache
sudo ldconfig

# Clean up
cd ~
rm -rf /tmp/ta-lib*
```

---

## 📦 Part 2: Deploy Your Application

### Step 9: Clone Your Repository

```bash
# Switch to algoagent user
sudo -u algoagent -i

# Navigate to application directory
cd /opt/algoagent

# Clone your repository (replace with your repo URL)
# This will create /opt/algoagent/AlgoAgent/
git clone https://github.com/yourusername/AlgoAgent.git

# Or if already cloned locally, use git to push and then clone
# Or use SCP/SFTP to upload files
```

If uploading via SCP from your Windows machine (in a new PowerShell window):
```powershell
# Upload from your local machine to create /opt/algoagent/AlgoAgent/
scp -r C:\Users\nyaga\Documents\AlgoAgent root@your-vps-ip:/opt/algoagent/
```

### Step 10: Create Python Virtual Environment

```bash
# Make sure you're the algoagent user
whoami  # Should output: algoagent

# Create virtual environment
python3.11 -m venv /opt/algoagent/venv

# Activate virtual environment
source /opt/algoagent/venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
cd /opt/algoagent/AlgoAgent/monolithic_agent
pip install -r requirements.txt
```

This will take 5-10 minutes depending on your VPS speed.

### Step 11: Create Environment Configuration File

```bash
# Exit from algoagent user
exit

# Create directory for environment file
sudo mkdir -p /etc/algoagent

# Create environment file
sudo nano /etc/algoagent/.env
```

Copy and paste this configuration (update the values in CAPS):

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=algoagent_api.settings_production
DJANGO_SECRET_KEY=GENERATE_A_RANDOM_SECRET_KEY_HERE
DJANGO_ALLOWED_HOSTS=api.algoai.biz,algoai.biz,www.algoai.biz
DEBUG=False

# Database Configuration
DB_NAME=algoagent
DB_USER=algoagent
DB_PASSWORD=YOUR_POSTGRES_PASSWORD_FROM_STEP6
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# CORS & CSRF Settings - IMPORTANT: Must include https:// scheme, no trailing slashes
CORS_ALLOWED_ORIGINS=https://algoai.biz,https://www.algoai.biz,https://api.algoai.biz
CSRF_TRUSTED_ORIGINS=https://algoai.biz,https://www.algoai.biz,https://api.algoai.biz
ALLOWED_WEBSOCKET_ORIGINS=algoai.biz,api.algoai.biz,www.algoai.biz

# Google OAuth (Optional - add if you have credentials)
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET

# LLM Configuration (add your API keys)
LLM_BACKEND=gemini
GOOGLE_API_KEY=YOUR_GOOGLE_GEMINI_API_KEY
GITHUB_TOKEN=YOUR_GITHUB_TOKEN

# Email Configuration (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
ADMIN_EMAIL=admin@your-domain.com
```

**To generate a Django SECRET_KEY (use any of these methods):**
```bash
# Option 1: Using Python secrets module (works without Django)
python3 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)))"

# Option 2: Using OpenSSL
openssl rand -base64 50

# Option 3: If Django is installed
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Save and exit nano: `Ctrl+X`, then `Y`, then `Enter`

```bash
# Set secure permissions
sudo chmod 600 /etc/algoagent/.env
```

### Step 12: Run Database Migrations

```bash
# Switch to algoagent user
sudo -u algoagent -i

# Activate virtual environment
source /opt/algoagent/venv/bin/activate

# Navigate to Django project
cd /opt/algoagent/AlgoAgent/monolithic_agent

# Run migrations (settings_production.py now loads /etc/algoagent/.env automatically)
python manage.py migrate --settings=algoagent_api.settings_production

# You should see:
# [Settings] Loaded .env from /etc/algoagent/.env
# ✓ Production settings loaded successfully

# Create superuser (optional but recommended)
python manage.py createsuperuser --settings=algoagent_api.settings_production

# Collect static files
python manage.py collectstatic --noinput --settings=algoagent_api.settings_production

# Exit algoagent user
exit
```

---

## ⚙️ Part 3: Configure System Services

### Step 13: Install Systemd Service Files

```bash
# Copy Daphne service file
sudo cp /opt/algoagent/AlgoAgent/monolithic_agent/deployment/daphne.service /etc/systemd/system/algoagent-daphne.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable algoagent-daphne

# Start the service
sudo systemctl start algoagent-daphne

# Check status
sudo systemctl status algoagent-daphne
```

You should see "active (running)" in green.

**View logs if there are errors:**
```bash
sudo journalctl -u algoagent-daphne -n 50 --no-pager
```

### Step 14: Configure Nginx

```bash
# Copy nginx configuration
sudo cp /opt/algoagent/AlgoAgent/monolithic_agent/deployment/nginx.conf /etc/nginx/sites-available/algoagent

# Edit the configuration to replace placeholders
sudo nano /etc/nginx/sites-available/algoagent
```

**Find and replace all occurrences:**
- `your-domain.com` → `api.algoai.biz` (or your actual domain)
- Make sure to update:
  - `server_name` directives (2 places)
  - SSL certificate paths (2 places)
  - `wss://your-domain.com` in Content-Security-Policy

Save: `Ctrl+X`, `Y`, `Enter`

```bash
# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/algoagent /etc/nginx/sites-enabled/

# Remove default nginx site
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx
```

### Step 15: Configure SSL Certificate (Let's Encrypt)

```bash
# Obtain SSL certificate (replace with your domain and email)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com --email your-email@example.com --agree-tos --non-interactive

# Test automatic renewal
sudo certbot renew --dry-run
```

Certbot will automatically update your nginx configuration with SSL settings.

**Verify HTTPS is working:**
```bash
curl -I https://your-domain.com/health/
```

Should return: `HTTP/2 200`

---

## 🧪 Part 4: Testing Your Deployment

### Step 16: Test API Endpoints

```bash
# Test health endpoint
curl https://your-domain.com/health/

# Test API root
curl https://your-domain.com/api/

# Test WebSocket (from your local machine with websocat or browser)
# wss://your-domain.com/ws/backtest/{run_id}/
```

### Step 17: Test from Frontend

Update your frontend environment variables:

```javascript
// .env or .env.production
VITE_API_URL=https://your-domain.com
VITE_WS_URL=wss://your-domain.com
```

Rebuild and test your frontend to ensure it connects properly.

---

## 📊 Part 5: Monitoring & Maintenance

### View Application Logs

```bash
# Real-time Daphne logs
sudo journalctl -u algoagent-daphne -f

# Django application logs
sudo tail -f /var/log/algoagent/django.log

# Django error logs
sudo tail -f /var/log/algoagent/django_error.log

# Nginx access logs
sudo tail -f /var/log/nginx/algoagent-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/algoagent-error.log
```

### Restart Services

```bash
# Restart Django application
sudo systemctl restart algoagent-daphne

# Restart Nginx
sudo systemctl restart nginx

# Restart PostgreSQL
sudo systemctl restart postgresql

# Restart Redis
sudo systemctl restart redis-server
```

### Check Service Status

```bash
# Check all services
sudo systemctl status algoagent-daphne nginx postgresql redis-server
```

---

## 🔄 Part 6: Deploying Updates

### Option A: Using the Deployment Script

```bash
# Make the script executable (first time only)
sudo chmod +x /opt/algoagent/AlgoAgent/monolithic_agent/deployment/deploy.sh

# Run deployment script
cd /opt/algoagent/AlgoAgent/monolithic_agent/deployment
bash deploy.sh
```

### Option B: Manual Deployment

```bash
# Switch to algoagent user
sudo -u algoagent -i

# Navigate to project root
cd /opt/algoagent/AlgoAgent

# Pull latest code
git pull origin main

# Navigate to monolithic_agent
cd monolithic_agent

# Activate virtual environment
source /opt/algoagent/venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --settings=algoagent_api.settings_production

# Collect static files
python manage.py collectstatic --noinput --settings=algoagent_api.settings_production

# Exit algoagent user
exit

# Restart service
sudo systemctl restart algoagent-daphne

# Check status
sudo systemctl status algoagent-daphne
```

---

## 🔒 Security Best Practices Checklist

- [ ] Changed default PostgreSQL password to strong password
- [ ] Set `DEBUG=False` in production environment file
- [ ] Generated unique `DJANGO_SECRET_KEY`
- [ ] Configured proper `ALLOWED_HOSTS`
- [ ] Set up SSL/TLS certificate (HTTPS)
- [ ] Configured firewall (UFW) to allow only necessary ports
- [ ] Restricted environment file permissions (600)
- [ ] Configured CORS to allow only your frontend domain
- [ ] Enabled HSTS and other security headers in nginx
- [ ] Set up regular database backups
- [ ] Configured log rotation for application logs
- [ ] Disabled root SSH login (optional but recommended)

### Disable Root SSH Login (Recommended)

```bash
# Create a sudo user first
sudo adduser yourusername
sudo usermod -aG sudo yourusername

# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Find and change:
# PermitRootLogin no

# Restart SSH
sudo systemctl restart sshd
```

---

## 🔧 Troubleshooting

### Application won't start

```bash
# Check logs for errors
sudo journalctl -u algoagent-daphne -n 100

# Check if port 8000 is in use
sudo netstat -tlnp | grep 8000

# Verify environment file exists and has correct permissions
ls -la /etc/algoagent/.env
```

### Database connection errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d algoagent -c "SELECT version();"

# Verify database credentials in /etc/algoagent/.env
```

### SSL certificate issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew

# Check nginx SSL configuration
sudo nginx -t
```

### WebSocket connection fails

```bash
# Check nginx websocket configuration
sudo nano /etc/nginx/sites-available/algoagent

# Verify Redis is running
sudo systemctl status redis-server

# Check Django channels layer in settings
```

### 502 Bad Gateway

```bash
# Ensure Daphne is running
sudo systemctl status algoagent-daphne

# Check if Daphne is listening on port 8000
sudo netstat -tlnp | grep 8000

# Check nginx error logs
sudo tail -f /var/log/nginx/algoagent-error.log
```

---

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Django Channels Documentation](https://channels.readthedocs.io/)

---

## 🎯 Quick Reference Commands

```bash
# View all services status
sudo systemctl status algoagent-daphne nginx postgresql redis-server

# Restart all services
sudo systemctl restart algoagent-daphne nginx postgresql redis-server

# View application logs
sudo journalctl -u algoagent-daphne -f

# View nginx logs
sudo tail -f /var/log/nginx/algoagent-access.log

# Run Django management commands
sudo -u algoagent bash -c "source /opt/algoagent/venv/bin/activate && cd /opt/algoagent/AlgoAgent/monolithic_agent && python manage.py <command> --settings=algoagent_api.settings_production"

# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
htop  # or top
```

---

## 📝 Notes

- **Repository location:** `/opt/algoagent/AlgoAgent/`
- **Django project:** `/opt/algoagent/AlgoAgent/monolithic_agent/`
- **Configuration files:** `/opt/algoagent/AlgoAgent/monolithic_agent/deployment/`
- **Virtual environment:** `/opt/algoagent/venv/`
- **Environment variables:** `/etc/algoagent/.env`
- **Application logs:** `/var/log/algoagent/`
- **Nginx logs:** `/var/log/nginx/`
- **Static files:** `/opt/algoagent/AlgoAgent/monolithic_agent/staticfiles/`
- **Media files:** `/opt/algoagent/AlgoAgent/monolithic_agent/media/`
- Database backups should be automated (not covered in this guide - see PostgreSQL documentation)

**Congratulations!** Your AlgoAgent backend is now deployed on a production VPS with industry-standard security and configuration. 🎉
