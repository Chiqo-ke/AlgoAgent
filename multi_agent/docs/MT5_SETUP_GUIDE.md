# MT5 + MTsocketAPI Setup Guide

## Quick Setup Instructions

### Step 1: Start MetaTrader5
1. Open MetaTrader5 terminal
2. Login with your demo or live trading account
3. Ensure "Allow automated trading" is enabled in Tools → Options → Expert Advisors

### Step 2: Install MTsocketAPI
1. Download MTsocketAPI from: https://www.mtsocketapi.com/mt5/restapi/
2. Extract the plugin to your MT5 installation directory
3. Restart MT5 terminal
4. The API should auto-start on port 81

### Step 3: Verify Installation
```bash
# Test basic connectivity
curl http://127.0.0.1:81/v1/account

# Expected response: Account information in JSON format
```

### Step 4: Test Market Data
```bash
# Get EURUSD price
curl http://127.0.0.1:81/v1/quote?symbol=EURUSD

# Expected response: { "symbol": "EURUSD", "bid": 1.0845, "ask": 1.0847, ... }
```

## Alternative Testing Without MT5

If MT5/MTsocketAPI is not immediately available, we can still test:

1. **TradingView Integration**: Already working ✅
2. **Algorithm Framework**: Code structure and logic
3. **Agent Activation**: Strategy development workflow
4. **Backtesting Logic**: Historical data simulation
5. **Risk Management**: Position sizing calculations

## Next Steps

1. **With MT5**: Complete live integration testing
2. **Without MT5**: Demo the agent workflow and algorithm structure

Let me proceed with testing the agent system and algorithm framework...