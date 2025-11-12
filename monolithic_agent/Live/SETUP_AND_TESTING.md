# Live Trading Setup & Testing Guide

## Complete Setup Procedure

### Step 1: Install Dependencies

```powershell
# Navigate to Live directory
cd C:\Users\nyaga\Documents\AlgoAgent\Live

# Install Python packages
pip install -r requirements.txt

# Verify MetaTrader5 SDK
python -c "import MetaTrader5 as mt5; print(f'MT5 version: {mt5.__version__}')"
```

Expected output:
```
MT5 version: 5.0.45
```

---

### Step 2: Configure MT5 Account

#### Option A: Demo Account (Recommended for Testing)
1. Open MetaTrader5 terminal
2. File → Open an Account
3. Select your broker and choose "Demo Account"
4. Register new demo account
5. Note down: Login, Password, Server

#### Option B: Live Account (Production Only)
⚠️ **Use extreme caution - real money at risk**
1. Ensure you have a funded account
2. Enable "Algo Trading" in MT5 (Tools → Options → Expert Advisors)
3. Note down: Login, Password, Server

---

### Step 3: Create Configuration

```powershell
# Copy template
Copy-Item .env.template .env

# Edit configuration
notepad .env
```

**Minimal configuration for testing:**
```env
# MT5 Connection
MT5_LOGIN=12345678                              # Your demo account
MT5_PASSWORD=your_password                      # Your demo password
MT5_SERVER=BrokerName-Demo                      # Demo server
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# Safe Testing Settings
DRY_RUN=true                                    # IMPORTANT: Start with true!
INTERVAL_SECONDS=60
MAX_RETRY_ATTEMPTS=3

# Conservative Risk Settings
DEFAULT_RISK_PCT=0.5                            # 0.5% risk per trade
MAX_POSITION_SIZE=0.01                          # Minimum lot size
MAX_DAILY_TRADES=3                              # Limited trades per day
MAX_DAILY_LOSS_PCT=2.0                          # Stop if lose 2%

# Test Strategy
SYMBOLS=EURUSD                                  # Single symbol for testing
TIMEFRAME=1h                                    # 1-hour bars
STRATEGY_ID=test_strategy
MAGIC_NUMBER=999999

# Safety
ENABLE_KILL_SWITCH=true
KILL_SWITCH_FILE=EMERGENCY_STOP

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
AUDIT_DB_PATH=./data/audit.db

# Alerts (optional - configure later)
ENABLE_ALERTS=false
```

---

### Step 4: Prepare Strategy

Use an existing strategy from Backtest module:

```powershell
# Check available strategies
dir ..\Backtest\codes\*.py

# Common strategies:
# - rsi_strategy.py (RSI-based)
# - ema_strategy.py (EMA crossover)
# - my_strategy.py (custom strategy)
```

Or create a simple test strategy in `../Backtest/codes/test_live_strategy.py`:

```python
# MUST NOT EDIT SimBroker
"""
Test Strategy for Live Trading
Simple RSI-based strategy for validation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sim_broker import SimBroker
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from datetime import datetime


class TestLiveStrategy:
    """Simple RSI strategy for testing live trading"""
    
    def __init__(self, broker: SimBroker):
        self.broker = broker
        self.positions = {}
        self.rsi_oversold = 30
        self.rsi_overbought = 70
    
    def on_bar(self, timestamp: datetime, data: dict):
        """Process each bar"""
        for symbol, bars in data.items():
            # Get RSI value
            rsi = bars.get('rsi_14')
            if rsi is None:
                continue
            
            # Check if we have position
            has_position = symbol in self.positions
            
            # Entry logic
            if not has_position and rsi < self.rsi_oversold:
                signal = create_signal(
                    timestamp=timestamp,
                    symbol=symbol,
                    side=OrderSide.BUY,
                    action=OrderAction.ENTRY,
                    order_type=OrderType.MARKET,
                    size=0.01
                )
                self.broker.submit_signal(signal.to_dict())
                self.positions[symbol] = True
            
            # Exit logic
            elif has_position and rsi > self.rsi_overbought:
                signal = create_signal(
                    timestamp=timestamp,
                    symbol=symbol,
                    side=OrderSide.SELL,
                    action=OrderAction.EXIT,
                    order_type=OrderType.MARKET,
                    size=0.01
                )
                self.broker.submit_signal(signal.to_dict())
                if symbol in self.positions:
                    del self.positions[symbol]
```

---

### Step 5: Test Connection

```powershell
# Test MT5 connection
python -c "from mt5_connector import MT5Connector; from config import LiveConfig; c = LiveConfig(); m = MT5Connector(c); print('Connected!' if m.initialize() else 'Failed'); m.shutdown()"
```

Expected output:
```
✓ MT5 connected successfully
  Terminal: MetaTrader 5 (Build 3850)
  Account: 12345678 - BrokerName-Demo
  Balance: $10000.00
  Equity: $10000.00
  Margin Free: $10000.00
✓ MT5 connection closed
Connected!
```

If connection fails, see Troubleshooting section in README.md

---

### Step 6: Dry-Run Test

```powershell
# Start trader in dry-run mode (safe - no real orders)
python live_trader.py --strategy ..\Backtest\codes\test_live_strategy.py --dry-run
```

Expected output:
```
================================================
ALGOAGENT LIVE TRADER
================================================
Version: 1.0.0
Mode: DRY RUN
Strategy: ..\Backtest\codes\test_live_strategy.py
================================================

🚀 Live Trader started
   Mode: DRY RUN
   Symbols: EURUSD
   Interval: 60s
   Strategy: TestLiveStrategy

--- Iteration 1 (2025-10-18 14:30:00) ---
Processing EURUSD...
Loaded 100 bars with columns: ['Open', 'High', 'Low', 'Close', 'Volume', 'RSI_14']
Generated 100 signals, 2 actionable
Executing BUY signal for EURUSD
DRY_RUN: Would send order: {'action': 1, 'symbol': 'EURUSD', 'volume': 0.01, ...}
✓ Position opened: EURUSD BUY 0.01 @ 1.09500
Loop completed in 2.35s, sleeping 57.65s
```

**What to verify:**
- [ ] MT5 connection successful
- [ ] Strategy loaded without errors
- [ ] Signals generated
- [ ] Orders logged as "DRY_RUN"
- [ ] No actual positions opened in MT5 terminal

---

### Step 7: Monitor Dashboard

While trader is running:

```powershell
# In a new terminal
python dashboard.py
```

Then open browser to: `http://127.0.0.1:5000`

**Dashboard should show:**
- Mode: DRY RUN
- Trading enabled: ✓
- Open positions: 0 (or as per dry-run simulation)
- Recent signals and orders

---

### Step 8: Test Kill-Switch

While trader is running:

```powershell
# In another terminal, create kill-switch file
New-Item -Path EMERGENCY_STOP -ItemType File
```

Expected behavior:
- Trader detects file within 1 interval (60s)
- Logs: "🚨 KILL SWITCH ACTIVATED"
- Trading stops gracefully
- Session summary printed

Remove kill-switch:
```powershell
Remove-Item EMERGENCY_STOP
```

---

### Step 9: Check Audit Logs

```powershell
# View log files
Get-Content logs\live_trader.log -Tail 50

# Query audit database
python -c "from audit_logger import AuditLogger; from pathlib import Path; a = AuditLogger(Path('data/audit.db')); print('Signals:', len(a.get_recent_signals(100))); print('Orders:', len(a.get_recent_orders(100)))"
```

Or use SQLite browser:
```powershell
# Install DB Browser for SQLite (optional)
# Download from: https://sqlitebrowser.org/

# Open database
# File: data\audit.db
# Browse tables: signals, orders, trades, events
```

---

## Testing Checklist

### ✅ Phase 1: Dry-Run Validation (1-2 days)

- [ ] Trader starts without errors
- [ ] MT5 connection stable (no disconnections)
- [ ] Signals generated correctly
- [ ] Orders show "DRY_RUN" in logs
- [ ] Kill-switch works
- [ ] Dashboard displays real-time data
- [ ] Audit database populated
- [ ] No actual orders in MT5 terminal

### ✅ Phase 2: Demo Account Testing (1-2 weeks)

**Configure for demo trading:**
```env
DRY_RUN=false                  # Execute real orders (on demo)
MAX_POSITION_SIZE=0.01         # Minimum lot size
MAX_DAILY_TRADES=3             # Conservative limit
```

Run trader:
```powershell
python live_trader.py --strategy ..\Backtest\codes\test_live_strategy.py
```

**Verify:**
- [ ] Orders executed in MT5 terminal
- [ ] Positions opened/closed correctly
- [ ] P/L matches expectations
- [ ] Slippage is acceptable (<5 pips for major pairs)
- [ ] No execution errors
- [ ] Daily limits work (test by lowering limit)
- [ ] Retry logic works (test by disconnecting MT5 briefly)

**Monitor metrics:**
- Win rate
- Average slippage
- Execution time
- Daily P/L variance

**Compare to backtest:**
| Metric | Backtest | Live Demo | Difference |
|--------|----------|-----------|------------|
| Win Rate | 65% | ? | ? |
| Avg Profit | $25 | ? | ? |
| Max Drawdown | 8% | ? | ? |
| Trades/Day | 5 | ? | ? |

### ✅ Phase 3: Small-Volume Live (1 week)

⚠️ **Real money - proceed with caution**

**Configure for live (minimal risk):**
```env
DRY_RUN=false
DEFAULT_RISK_PCT=0.5           # Very conservative
MAX_POSITION_SIZE=0.01         # Minimum lot
MAX_DAILY_TRADES=2             # Very limited
MAX_DAILY_LOSS_PCT=1.0         # Stop if lose 1%
ENABLE_ALERTS=true             # Enable notifications
```

**Verify:**
- [ ] Starting capital is amount you can afford to lose
- [ ] Alerts are working (test webhook/Telegram)
- [ ] Kill-switch file is accessible
- [ ] You can monitor 24/7 (or during trading hours)

**Daily checklist:**
- [ ] Check morning P/L
- [ ] Review overnight trades
- [ ] Verify positions align with strategy
- [ ] Check for errors in logs
- [ ] Monitor slippage and execution quality

**Weekly review:**
- [ ] Compare performance to backtest
- [ ] Analyze losing trades
- [ ] Check for unexpected patterns
- [ ] Adjust risk parameters if needed

---

## Performance Monitoring

### Key Metrics to Track

1. **Execution Quality**
   - Slippage: Difference between signal price and execution price
   - Fill rate: % of orders successfully executed
   - Retry rate: % of orders requiring retries

2. **Strategy Performance**
   - Daily P/L
   - Win rate
   - Average profit per trade
   - Maximum drawdown

3. **System Health**
   - Connection uptime
   - Loop iteration time
   - Error frequency
   - Alert frequency

### SQL Queries for Analysis

```sql
-- Daily P/L summary
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as trades,
  SUM(profit) as total_pnl,
  AVG(profit) as avg_pnl,
  SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
FROM trades
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Slippage analysis (difference between order price and execution price)
SELECT 
  symbol,
  AVG(ABS(executed_price - price)) as avg_slippage,
  MAX(ABS(executed_price - price)) as max_slippage
FROM orders
WHERE status = 'EXECUTED'
GROUP BY symbol;

-- Execution success rate
SELECT 
  status,
  COUNT(*) as count,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders) as percentage
FROM orders
GROUP BY status;

-- Most common errors
SELECT 
  retcode_message,
  COUNT(*) as count
FROM orders
WHERE status = 'FAILED'
GROUP BY retcode_message
ORDER BY count DESC;
```

---

## Troubleshooting Common Issues

### Issue 1: "Module not found" error on startup

**Cause:** Backtesting module not in path

**Solution:**
```powershell
# Verify Backtest module exists
dir ..\Backtest\sim_broker.py
dir ..\Backtest\data_loader.py

# If missing, ensure you're in the Live directory
cd C:\Users\nyaga\Documents\AlgoAgent\Live
```

### Issue 2: No signals generated

**Cause:** Insufficient data or indicator calculation fails

**Check:**
```powershell
# Test data loading
python -c "from backtesting_bridge import BacktestingBridge; from pathlib import Path; import sys; sys.path.insert(0, str(Path('../Backtest'))); from rsi_strategy import RSIStrategy; b = BacktestingBridge(RSIStrategy); from datetime import datetime, timedelta; s = b.generate_signals('EURUSD', datetime.now()-timedelta(days=7), datetime.now(), '1d', {'RSI': {'timeperiod': 14}}); print(f'Signals: {len(s)}')"
```

### Issue 3: Orders rejected with "Insufficient margin"

**Cause:** Position size too large for account

**Solution:**
- Reduce `MAX_POSITION_SIZE` in `.env`
- Increase account balance
- Check `mt5.order_check()` output for exact margin requirement

### Issue 4: High slippage

**Cause:** Market conditions or broker execution

**Solutions:**
- Use LIMIT orders instead of MARKET
- Increase `deviation` parameter
- Trade during liquid hours (avoid Asian session for EUR/USD)
- Switch to ECN broker

### Issue 5: Trader stops unexpectedly

**Check logs:**
```powershell
# View last 100 lines
Get-Content logs\live_trader.log -Tail 100

# Look for:
# - Connection errors
# - Unhandled exceptions
# - Kill-switch activation
```

**Check events table:**
```sql
SELECT * FROM events 
WHERE severity IN ('ERROR', 'CRITICAL') 
ORDER BY timestamp DESC 
LIMIT 20;
```

---

## Next Steps

Once testing is complete and you're confident:

1. **Scale Up Gradually**
   - Increase `MAX_POSITION_SIZE` by 0.01 lot increments
   - Raise `MAX_DAILY_TRADES` slowly
   - Monitor for 1 week after each change

2. **Optimize Strategy**
   - Review losing trades
   - Adjust entry/exit thresholds
   - Add filters (e.g., ADX for trend strength)

3. **Add More Symbols**
   - Add one symbol at a time
   - Ensure correlation is low (<0.7)
   - Monitor total exposure

4. **Implement Multiple Strategies**
   - Run different strategies with different magic numbers
   - Diversify across timeframes
   - Monitor combined portfolio metrics

5. **Automate Monitoring**
   - Set up automated daily reports
   - Create alerts for anomalies
   - Build custom dashboard widgets

---

## Emergency Procedures

### Stop Trading Immediately

**Method 1: Kill-Switch File**
```powershell
New-Item -Path EMERGENCY_STOP -ItemType File
```

**Method 2: Stop Process**
```powershell
# Find process ID
Get-Process python | Where-Object {$_.MainWindowTitle -like "*live_trader*"}

# Stop process (replace PID)
Stop-Process -Id PID
```

**Method 3: Close All Positions Manually**
1. Open MT5 terminal
2. Right-click on position → Close Position
3. Or use "Close All" in terminal

### Recover After Crash

1. **Check positions in MT5 terminal**
2. **Review audit database** for last successful operation
3. **Check logs** for error cause
4. **Restart trader** (it will sync state with MT5)

```powershell
# Restart
python live_trader.py --strategy ..\Backtest\codes\your_strategy.py
```

Trader automatically syncs with MT5 on startup, so orphaned positions are handled.

---

## Support & Resources

- **Documentation**: See `README.md` in this directory
- **MT5 Python SDK**: https://www.mql5.com/en/docs/python_metatrader5
- **Logs**: `logs/live_trader.log`
- **Audit DB**: `data/audit.db`
- **Dashboard**: http://127.0.0.1:5000

---

**Remember:** Always test thoroughly before risking real capital! 🚀
