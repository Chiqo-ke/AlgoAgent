#!/bin/bash
# Fix BotPerformance Table Issue
# Run this on VPS to fix the missing strategy_api_botperformance table

echo "=========================================="
echo "Fixing BotPerformance Table Issue"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Check if table exists
echo -e "${YELLOW}[1/4] Checking if table exists...${NC}"
TABLE_EXISTS=$(sudo -u postgres psql -d algoagent -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'strategy_api_botperformance');")

if [ "$TABLE_EXISTS" = "t" ]; then
    echo -e "${GREEN}✓${NC} Table strategy_api_botperformance exists"
    echo "  Issue might be with permissions or connection. Checking..."
    sudo -u postgres psql -d algoagent -c "\dt strategy_api_botperformance"
else
    echo -e "${RED}✗${NC} Table strategy_api_botperformance does NOT exist"
    echo "  Will attempt to create it..."
fi
echo ""

# Step 2: Show migration status
echo -e "${YELLOW}[2/4] Checking migration status...${NC}"
sudo -u algoagent bash -c "source /opt/algoagent/venv/bin/activate && cd /opt/algoagent/AlgoAgent/monolithic_agent && python manage.py showmigrations strategy_api --settings=algoagent_api.settings_production" | grep "0002_bot_performance"
echo ""

# Step 3: Check if migration file exists
echo -e "${YELLOW}[3/4] Checking migration file...${NC}"
if [ -f "/opt/algoagent/AlgoAgent/monolithic_agent/strategy_api/migrations/0002_bot_performance.py" ]; then
    echo -e "${GREEN}✓${NC} Migration file exists"
    echo "  Showing migration SQL..."
    sudo -u algoagent bash -c "source /opt/algoagent/venv/bin/activate && cd /opt/algoagent/AlgoAgent/monolithic_agent && python manage.py sqlmigrate strategy_api 0002_bot_performance --settings=algoagent_api.settings_production" | head -30
else
    echo -e "${RED}✗${NC} Migration file does NOT exist"
fi
echo ""

# Step 4: Attempt fixes
echo -e "${YELLOW}[4/4] Attempting to fix...${NC}"
echo ""

if [ "$TABLE_EXISTS" != "t" ]; then
    echo "Option 1: Trying to run migration with --run-syncdb"
    sudo -u algoagent bash -c "source /opt/algoagent/venv/bin/activate && cd /opt/algoagent/AlgoAgent/monolithic_agent && python manage.py migrate strategy_api --settings=algoagent_api.settings_production --run-syncdb"
    echo ""
    
    # Check again
    TABLE_EXISTS=$(sudo -u postgres psql -d algoagent -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'strategy_api_botperformance');")
    
    if [ "$TABLE_EXISTS" = "t" ]; then
        echo -e "${GREEN}✓${NC} Table created successfully!"
    else
        echo -e "${YELLOW}!${NC} Option 1 didn't work. Trying Option 2..."
        echo ""
        
        echo "Option 2: Fake-initial migration"
        sudo -u algoagent bash -c "source /opt/algoagent/venv/bin/activate && cd /opt/algoagent/AlgoAgent/monolithic_agent && python manage.py migrate strategy_api --settings=algoagent_api.settings_production --fake-initial"
        
        # Check again
        TABLE_EXISTS=$(sudo -u postgres psql -d algoagent -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'strategy_api_botperformance');")
        
        if [ "$TABLE_EXISTS" = "t" ]; then
            echo -e "${GREEN}✓${NC} Table created successfully!"
        else
            echo -e "${RED}✗${NC} Automatic fixes didn't work."
            echo ""
            echo "Manual fix required. Here's what to do:"
            echo ""
            echo "1. Check the migration SQL:"
            echo "   sudo -u algoagent bash -c \"source /opt/algoagent/venv/bin/activate && cd /opt/algoagent/AlgoAgent/monolithic_agent && python manage.py sqlmigrate strategy_api 0002_bot_performance --settings=algoagent_api.settings_production\" > /tmp/migration.sql"
            echo ""
            echo "2. Run the SQL manually:"
            echo "   sudo -u postgres psql -d algoagent -f /tmp/migration.sql"
            echo ""
            echo "3. Mark migration as applied:"
            echo "   sudo -u algoagent bash -c \"source /opt/algoagent/venv/bin/activate && cd /opt/algoagent/AlgoAgent/monolithic_agent && python manage.py migrate strategy_api --fake --settings=algoagent_api.settings_production\""
        fi
    fi
fi

echo ""
echo "=========================================="
echo "Final Check"
echo "=========================================="

# Final verification
TABLE_EXISTS=$(sudo -u postgres psql -d algoagent -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'strategy_api_botperformance');")

if [ "$TABLE_EXISTS" = "t" ]; then
    echo -e "${GREEN}✓ SUCCESS${NC} - Table exists"
    echo ""
    echo "Table structure:"
    sudo -u postgres psql -d algoagent -c "\d strategy_api_botperformance"
    echo ""
    echo "Row count:"
    sudo -u postgres psql -d algoagent -c "SELECT COUNT(*) FROM strategy_api_botperformance;"
    echo ""
    echo "Restarting Daphne service..."
    sudo systemctl restart algoagent-daphne
    echo -e "${GREEN}✓${NC} Service restarted"
    echo ""
    echo "Test the endpoint:"
    echo "  curl http://127.0.0.1:8000/api/strategies/bot-performance/"
else
    echo -e "${RED}✗ FAILED${NC} - Table still doesn't exist"
    echo ""
    echo "Please follow the manual steps above or check the logs:"
    echo "  sudo journalctl -u algoagent-daphne -n 50"
fi

echo ""
