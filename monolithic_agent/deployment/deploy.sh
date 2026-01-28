#!/bin/bash
# AlgoAgent Deployment Script
# Run this to deploy updates to your application
# Usage: bash deploy.sh

set -e  # Exit on any error

echo "========================================="
echo "  AlgoAgent Deployment Script"
echo "========================================="

# Configuration
APP_USER="algoagent"
APP_DIR="/opt/algoagent/AlgoAgent/monolithic_agent"
VENV_DIR="/opt/algoagent/venv"
ENV_FILE="/etc/algoagent/.env"

# Check if running as root or algoagent user
if [ "$EUID" -eq 0 ]; then
    echo "Running as root - switching to $APP_USER for deployment..."
    exec sudo -u $APP_USER bash "$0" "$@"
fi

# Verify we're in the correct directory
if [ ! -d "$APP_DIR" ]; then
    echo "Error: Application directory not found: $APP_DIR"
    exit 1
fi

cd $APP_DIR

echo ""
echo "Step 1: Pulling latest code from git..."
git fetch origin
git pull origin main  # Change 'main' to your branch name if different

echo ""
echo "Step 2: Activating virtual environment..."
source $VENV_DIR/bin/activate

echo ""
echo "Step 3: Installing/updating Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Step 4: Collecting static files..."
python manage.py collectstatic --noinput --settings=algoagent_api.settings_production

echo ""
echo "Step 5: Running database migrations..."
python manage.py migrate --settings=algoagent_api.settings_production

echo ""
echo "Step 6: Checking for missing dependencies..."
python manage.py check --deploy --settings=algoagent_api.settings_production

echo ""
echo "Step 7: Restarting application services..."
sudo systemctl restart algoagent-daphne
sudo systemctl status algoagent-daphne --no-pager

echo ""
echo "Step 8: Restarting nginx..."
sudo nginx -t  # Test configuration
sudo systemctl reload nginx

echo ""
echo "Step 9: Checking service health..."
sleep 3
if systemctl is-active --quiet algoagent-daphne; then
    echo "✓ Daphne service is running"
else
    echo "✗ Daphne service failed to start!"
    echo "Check logs: sudo journalctl -u algoagent-daphne -n 50"
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo "✓ Nginx is running"
else
    echo "✗ Nginx failed to start!"
    exit 1
fi

echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "========================================="
echo ""
echo "Service Status:"
sudo systemctl status algoagent-daphne --no-pager --lines=5
echo ""
echo "View logs:"
echo "  Application: sudo journalctl -u algoagent-daphne -f"
echo "  Django: sudo tail -f /var/log/algoagent/django.log"
echo "  Nginx: sudo tail -f /var/log/nginx/algoagent-access.log"
echo ""
