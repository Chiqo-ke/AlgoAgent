#!/bin/bash
# AlgoAgent VPS Initial Setup Script
# Run this once on a fresh Ubuntu VPS
# Usage: sudo bash setup_vps.sh

set -e  # Exit on any error

echo "========================================="
echo "  AlgoAgent VPS Setup Script"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: Please run as root (use sudo)"
    exit 1
fi

# Configuration
APP_USER="algoagent"
APP_DIR="/opt/algoagent"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/var/log/algoagent"
ENV_FILE="/etc/algoagent/.env"

# Prompt for domain
read -p "Enter your domain name (e.g., api.algoai.biz): " DOMAIN
read -p "Enter your email for SSL certificate: " SSL_EMAIL

echo ""
echo "Step 1: Updating system packages..."
apt update && apt upgrade -y

echo ""
echo "Step 2: Installing dependencies..."
apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    build-essential \
    libpq-dev \
    python3-dev \
    curl \
    ufw

echo ""
echo "Step 3: Configuring firewall..."
ufw --force enable
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw status

echo ""
echo "Step 4: Creating application user..."
if id "$APP_USER" &>/dev/null; then
    echo "User $APP_USER already exists"
else
    useradd -m -s /bin/bash $APP_USER
    echo "User $APP_USER created"
fi

echo ""
echo "Step 5: Creating directory structure..."
mkdir -p $APP_DIR
mkdir -p $LOG_DIR
mkdir -p /etc/algoagent
chown -R $APP_USER:$APP_USER $APP_DIR
chown -R $APP_USER:$APP_USER $LOG_DIR

echo ""
echo "Step 6: Configuring PostgreSQL..."
sudo -u postgres psql <<EOF
-- Create database and user
CREATE DATABASE algoagent;
CREATE USER algoagent WITH ENCRYPTED PASSWORD 'CHANGE_THIS_PASSWORD';
ALTER ROLE algoagent SET client_encoding TO 'utf8';
ALTER ROLE algoagent SET default_transaction_isolation TO 'read committed';
ALTER ROLE algoagent SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE algoagent TO algoagent;
ALTER DATABASE algoagent OWNER TO algoagent;
\q
EOF

echo ""
echo "Step 7: Configuring Redis..."
systemctl enable redis-server
systemctl start redis-server

echo ""
echo "Step 8: Creating Python virtual environment..."
sudo -u $APP_USER python3.11 -m venv $VENV_DIR

echo ""
echo "Step 9: Creating environment file template..."
cat > $ENV_FILE <<EOF
# Django Settings
DJANGO_SETTINGS_MODULE=algoagent_api.settings_production
DJANGO_SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DJANGO_ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
DEBUG=False

# Database
DB_NAME=algoagent
DB_USER=algoagent
DB_PASSWORD=CHANGE_THIS_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS & CSRF
CORS_ALLOWED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
ALLOWED_WEBSOCKET_ORIGINS=$DOMAIN,www.$DOMAIN

# Google OAuth (Optional - add your credentials)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# LLM Configuration (Add your keys)
LLM_BACKEND=gemini
GOOGLE_API_KEY=
GITHUB_TOKEN=

# Email (Optional)
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
ADMIN_EMAIL=admin@$DOMAIN
EOF

chmod 600 $ENV_FILE
echo "Environment file created at: $ENV_FILE"
echo "IMPORTANT: Edit this file and update all passwords and API keys!"

echo ""
echo "Step 10: Installing TA-Lib (for trading indicators)..."
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
make install
ldconfig
rm -rf /tmp/ta-lib*

echo ""
echo "========================================="
echo "  Initial Setup Complete!"
echo "========================================="
echo ""
echo "Next Steps:"
echo "1. Edit environment file: nano $ENV_FILE"
echo "   - Update DB_PASSWORD"
echo "   - Add your API keys (Google, GitHub, etc.)"
echo "   - Add frontend domain to CORS_ALLOWED_ORIGINS"
echo ""
echo "2. Clone your repository to $APP_DIR"
echo "   Example: sudo -u $APP_USER git clone <repo-url> $APP_DIR"
echo ""
echo "3. Run the deployment script: bash deploy.sh"
echo ""
echo "4. Configure SSL certificate:"
echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $SSL_EMAIL"
echo ""
