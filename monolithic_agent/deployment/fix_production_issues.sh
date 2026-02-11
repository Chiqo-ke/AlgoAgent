#!/bin/bash
# AlgoAgent Production Issue Diagnostic and Fix Script
# Run this on your VPS to diagnose and fix common production issues

echo "========================================"
echo "AlgoAgent Production Diagnostic Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check if services are running
echo -e "${YELLOW}[1/8] Checking service status...${NC}"
echo "---"

services=("postgresql" "redis-server" "algoagent-daphne" "nginx")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✓${NC} $service is running"
    else
        echo -e "${RED}✗${NC} $service is NOT running"
        echo "  Attempting to start $service..."
        sudo systemctl start "$service"
    fi
done
echo ""

# 2. Check if port 8000 is listening
echo -e "${YELLOW}[2/8] Checking if Daphne is listening on port 8000...${NC}"
echo "---"
if sudo netstat -tlnp | grep -q ":8000"; then
    echo -e "${GREEN}✓${NC} Port 8000 is listening"
    sudo netstat -tlnp | grep ":8000"
else
    echo -e "${RED}✗${NC} Port 8000 is NOT listening"
    echo "  Daphne service may have failed to start"
fi
echo ""

# 3. Check environment file
echo -e "${YELLOW}[3/8] Checking environment file...${NC}"
echo "---"
if [ -f "/etc/algoagent/.env" ]; then
    echo -e "${GREEN}✓${NC} /etc/algoagent/.env exists"
    echo "  Permissions: $(ls -l /etc/algoagent/.env | awk '{print $1}')"
    
    # Check critical variables
    echo ""
    echo "  Critical variables:"
    for var in "DJANGO_SECRET_KEY" "DJANGO_ALLOWED_HOSTS" "CORS_ALLOWED_ORIGINS" "CSRF_TRUSTED_ORIGINS" "DB_PASSWORD"; do
        if grep -q "^${var}=" /etc/algoagent/.env 2>/dev/null; then
            if [ "$var" = "DB_PASSWORD" ] || [ "$var" = "DJANGO_SECRET_KEY" ]; then
                echo -e "    ${GREEN}✓${NC} $var is set (hidden for security)"
            else
                value=$(grep "^${var}=" /etc/algoagent/.env | cut -d'=' -f2-)
                echo -e "    ${GREEN}✓${NC} $var = $value"
            fi
        else
            echo -e "    ${RED}✗${NC} $var is NOT set"
        fi
    done
else
    echo -e "${RED}✗${NC} /etc/algoagent/.env does NOT exist"
    echo "  You need to create this file!"
fi
echo ""

# 4. Test local backend connection
echo -e "${YELLOW}[4/8] Testing local backend connection...${NC}"
echo "---"
response=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health/ 2>/dev/null)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓${NC} Backend is responding locally (HTTP $response)"
else
    echo -e "${RED}✗${NC} Backend is NOT responding locally (HTTP $response)"
    echo "  Checking Daphne logs..."
    sudo journalctl -u algoagent-daphne -n 20 --no-pager
fi
echo ""

# 5. Check nginx configuration
echo -e "${YELLOW}[5/8] Checking nginx configuration...${NC}"
echo "---"
if sudo nginx -t 2>&1 | grep -q "test is successful"; then
    echo -e "${GREEN}✓${NC} Nginx configuration is valid"
else
    echo -e "${RED}✗${NC} Nginx configuration has errors:"
    sudo nginx -t
fi
echo ""

# 6. Check SSL certificate
echo -e "${YELLOW}[6/8] Checking SSL certificates...${NC}"
echo "---"
if sudo certbot certificates 2>/dev/null | grep -q "Certificate Name"; then
    echo -e "${GREEN}✓${NC} SSL certificates found:"
    sudo certbot certificates 2>/dev/null | grep -E "(Certificate Name|Domains|Expiry Date)"
else
    echo -e "${YELLOW}!${NC} No SSL certificates found or certbot not configured"
fi
echo ""

# 7. Check recent errors
echo -e "${YELLOW}[7/8] Checking recent errors...${NC}"
echo "---"
echo "Recent Daphne errors (last 10):"
sudo journalctl -u algoagent-daphne -p err -n 10 --no-pager --since "1 hour ago" 2>/dev/null || echo "  No recent errors"
echo ""

echo "Recent Django errors (last 10):"
if [ -f "/var/log/algoagent/django_error.log" ]; then
    sudo tail -n 10 /var/log/algoagent/django_error.log 2>/dev/null || echo "  No recent errors"
else
    echo "  Log file not found"
fi
echo ""

# 8. Check disk space and memory
echo -e "${YELLOW}[8/8] Checking system resources...${NC}"
echo "---"
echo "Disk usage:"
df -h / | tail -n 1
echo ""
echo "Memory usage:"
free -h | grep -E "(Mem|Swap)"
echo ""

# Summary and recommendations
echo "========================================"
echo "Summary and Recommendations"
echo "========================================"
echo ""

# Check if Daphne is running
if systemctl is-active --quiet algoagent-daphne; then
    echo -e "${GREEN}✓${NC} Backend service is running"
else
    echo -e "${RED}✗${NC} CRITICAL: Backend service is not running"
    echo "  → Run: sudo systemctl restart algoagent-daphne"
    echo "  → Check logs: sudo journalctl -u algoagent-daphne -n 50"
fi

# Check CORS configuration
if grep -q "^CORS_ALLOWED_ORIGINS=https://" /etc/algoagent/.env 2>/dev/null; then
    echo -e "${GREEN}✓${NC} CORS configuration looks correct"
else
    echo -e "${RED}✗${NC} CRITICAL: CORS configuration may be incorrect"
    echo "  → Ensure CORS_ALLOWED_ORIGINS starts with 'https://'"
    echo "  → Example: CORS_ALLOWED_ORIGINS=https://algoai.biz,https://www.algoai.biz"
fi

echo ""
echo "To view live logs, run:"
echo "  sudo journalctl -u algoagent-daphne -f"
echo ""
echo "To restart all services, run:"
echo "  sudo systemctl restart algoagent-daphne nginx"
echo ""
