# AlgoAgent Live Trading Module

**Production-ready live trading system that reuses the Backtesting module and executes trades via MetaTrader5.**

---

## 🎯 Overview

The Live module is a **thin execution layer** that:
- Reuses Backtesting strategies, signals, and risk calculations
- Connects to MetaTrader5 via the official Python SDK
- Executes trades with retry logic and idempotency
- Provides safety features (kill-switch, daily limits, dry-run mode)
- Maintains complete audit trails in SQLite
- Offers real-time monitoring via web dashboard

**Design Philosophy:**
- **Single source of truth**: Strategy logic lives in Backtesting, not duplicated
- **Safety first**: Multiple layers of protection and validation
- **Observability**: Structured logging, audit DB, and real-time dashboard
- **Idempotency**: Deduplication prevents duplicate orders
- **Graceful degradation**: Automatic reconnection and error recovery

---

## 📁 Architecture

```
Live/
├── config.py              # Configuration & constants
├── backtesting_bridge.py  # Bridge to Backtesting module (signals, sizing, orders)
├── mt5_connector.py       # MT5 connection management
├── order_executor.py      # Order execution with retries
├── state_manager.py       # Position & state tracking
├── audit_logger.py        # Persistent SQLite audit log
├── alerts.py              # Telegram/webhook alerts
├── dashboard.py           # Web monitoring dashboard
├── live_trader.py         # Main trading loop (orchestrator)
├── .env.template          # Configuration template
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

### Component Responsibilities

| Component | Purpose |
|-----------|---------|
| **config.py** | Loads `.env`, validates config, defines MT5 constants |
| **backtesting_bridge.py** | Exposes Backtesting APIs: `generate_signals()`, `position_size()`, `build_order_request()`, `simulate_precheck()` |
| **mt5_connector.py** | MT5 lifecycle: `initialize()`, `login()`, `ensure_connected()`, `send_order()` |
| **order_executor.py** | Retry logic, idempotency (client_order_id), execution tracking |
| **state_manager.py** | Position tracking, daily limits, kill-switch state |
| **audit_logger.py** | SQLite logging: signals, orders, trades, events, account snapshots |
| **alerts.py** | Send notifications via Telegram/webhook |
| **dashboard.py** | Flask web UI at `http://127.0.0.1:5000` |
| **live_trader.py** | Main loop: fetch signals → execute → monitor → repeat |

---

## 🚀 Quick Start

### 1. Prerequisites

- **Windows** (MetaTrader5 is Windows-only)
- **Python 3.9+**
- **MetaTrader5 terminal** installed and logged in
- **Demo or live MT5 account**

### 2. Installation

```powershell
# Navigate to Live directory
cd AlgoAgent\Live

# Install dependencies
pip install -r requirements.txt

# Copy and configure .env
cp .env.template .env
notepad .env  # Edit with your settings
```

### 3. Configuration

Edit `.env` file:

```env
# MT5 Connection (REQUIRED for live mode)
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# Trading Mode
DRY_RUN=true                # Set to 'false' for live trading
INTERVAL_SECONDS=60         # Loop interval (seconds)

# Risk Management
DEFAULT_RISK_PCT=1.0        # Risk per trade (%)
MAX_POSITION_SIZE=10.0      # Max lot size
MAX_DAILY_TRADES=10         # Daily trade limit
MAX_DAILY_LOSS_PCT=5.0      # Max daily loss (%)

# Strategy
SYMBOLS=EURUSD,GBPUSD       # Comma-separated symbols
TIMEFRAME=1d                # '1d', '1h', '5m', etc.
STRATEGY_ID=my_strategy     # Strategy identifier
MAGIC_NUMBER=123456         # EA magic number

# Safety
ENABLE_KILL_SWITCH=true     # Emergency stop file
KILL_SWITCH_FILE=EMERGENCY_STOP
```

**Important:**
- Start with `DRY_RUN=true` (simulates execution, doesn't send orders)
- Use a **demo account** for initial testing
- Set conservative risk limits initially

### 4. Run the Trader

```powershell
# Dry-run mode (safe testing)
python live_trader.py --strategy ../Backtest/codes/my_strategy.py --dry-run

# Live mode (actual trading - use with caution!)
python live_trader.py --strategy ../Backtest/codes/my_strategy.py
```

### 5. Monitor via Dashboard

Open browser to: `http://127.0.0.1:5000`

Dashboard shows:
- Real-time status (mode, trading enabled/disabled)
- Open positions and daily P/L
- Success rate and order statistics
- Recent signals and orders

---

## 📋 Workflow & Runtime Flow

### Initialization
1. Load `.env` configuration
2. Initialize MT5 connection (`mt5.initialize()` → `mt5.login()`)
3. Setup logging (structured JSON to files)
4. Initialize SQLite audit DB
5. Load strategy from Backtesting module
6. Sync state with MT5 (get open positions)

### Main Loop (repeats every `INTERVAL_SECONDS`)
1. **Check kill-switch**: Exit if `EMERGENCY_STOP` file exists
2. **Check daily limits**: Pause if trade count or loss limit reached
3. **Ensure MT5 connection**: Reconnect if disconnected
4. **Sync state**: Update positions from MT5
5. **For each symbol**:
   - Call `generate_signals()` (from Backtesting bridge)
   - Process latest signal (BUY/SELL/HOLD)
   - If actionable:
     - Calculate position size (`position_size()`)
     - Build order request (`build_order_request()`)
     - Run pre-checks (`simulate_precheck()`)
     - Execute order with retries (`order_executor.execute_order()`)
     - Update state and audit log
6. **Take account snapshot** (every 5 minutes)
7. **Sleep** until next interval

### Shutdown
1. Log session summary (orders, trades, P/L)
2. Close MT5 connection (`mt5.shutdown()`)
3. Write final audit logs

---

## 🛡️ Safety Features

### 1. Dry-Run Mode
- Set `DRY_RUN=true` in `.env`
- All logic runs normally, but `mt5.order_send()` is simulated
- Logs show "DRY_RUN: Would send order..."
- **Use this for testing strategies before going live**

### 2. Kill-Switch
- Create a file named `EMERGENCY_STOP` (or your configured name)
- Trader detects it on next loop iteration and stops immediately
- Useful for instant manual intervention

```powershell
# Activate kill-switch
New-Item -Path EMERGENCY_STOP -ItemType File

# Deactivate
Remove-Item EMERGENCY_STOP
```

### 3. Daily Limits
- **Trade count limit**: `MAX_DAILY_TRADES=10`
- **Loss limit**: `MAX_DAILY_LOSS_PCT=5.0` (5% of account)
- Trading pauses when limits are reached

### 4. Idempotency
- Each order gets a unique `client_order_id`
- Duplicate orders are rejected
- Safe against accidental re-execution

### 5. Pre-Execution Checks
- Validates order fields (price, volume, SL/TP)
- Checks margin requirements via `mt5.order_check()`
- Runs backtest-style validation via `simulate_precheck()`
- Blocks invalid orders before sending

### 6. Retry Logic
- Exponential backoff for transient errors (timeouts, requotes)
- Max retries: `MAX_RETRY_ATTEMPTS=3`
- Non-retryable errors (insufficient margin) fail immediately

### 7. Alerts
- Telegram & webhook notifications for:
  - Startup/shutdown
  - Trade execution
  - Errors and kill-switch activation
- Configure in `.env`:
  ```env
  ENABLE_ALERTS=true
  TELEGRAM_BOT_TOKEN=your_bot_token
  TELEGRAM_CHAT_ID=your_chat_id
  ALERT_WEBHOOK_URL=https://your-webhook-url
  ```

---

## 📊 Monitoring & Observability

### 1. Web Dashboard
- URL: `http://127.0.0.1:5000`
- Auto-refreshes every 2 seconds
- Shows:
  - Live status (mode, enabled/disabled, kill-switch)
  - Open positions & daily stats
  - Recent signals & orders

### 2. Structured Logs
- Location: `./logs/live_trader.log`
- Format: JSON (one object per line)
- Fields: `timestamp`, `level`, `logger`, `message`, `extra_data`
- Rotating logs: max 100MB per file, keeps 10 backups

Example log entry:
```json
{
  "timestamp": "2025-10-18 14:30:45",
  "level": "INFO",
  "logger": "LiveTrader",
  "message": "Order executed successfully",
  "module": "order_executor",
  "function": "execute_order",
  "line": 123,
  "extra_data": {
    "symbol": "EURUSD",
    "side": "BUY",
    "volume": 0.01,
    "price": 1.0950
  }
}
```

### 3. Audit Database
- Location: `./data/audit.db` (SQLite)
- Tables:
  - **signals**: All generated signals
  - **orders**: Order submissions & results
  - **trades**: Completed trades with P/L
  - **events**: System events (errors, kill-switch, etc.)
  - **account_snapshots**: Periodic account state

Query examples:
```sql
-- Recent trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

-- Daily summary
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as trades,
  SUM(profit) as total_pnl
FROM trades
GROUP BY DATE(timestamp);

-- Failed orders
SELECT * FROM orders WHERE status = 'FAILED';
```

### 4. Alerts
- Real-time notifications via Telegram or webhook
- Configurable severity levels (INFO, WARNING, ERROR, CRITICAL)

---

## 🔧 Advanced Configuration

### Position Sizing
Edit `backtesting_bridge.py` → `position_size()` method:
```python
def position_size(self, account_balance, risk_pct, stop_loss_price, entry_price, symbol):
    # Custom logic here
    # Example: Fixed lot size
    return 0.01
    
    # Example: Kelly criterion
    # win_rate = 0.6
    # win_loss_ratio = 1.5
    # kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
    # return account_balance * kelly / entry_price
```

### Custom Indicators
Modify `generate_signals()` call in `live_trader.py`:
```python
signals = self.bridge.generate_signals(
    symbol=symbol,
    from_ts=start_time,
    to_ts=end_time,
    timeframe=self.config.timeframe,
    indicators={
        'RSI': {'timeperiod': 14},
        'SMA': {'timeperiod': 50},
        'BOLLINGER': {'timeperiod': 20, 'nbdevup': 2}
    }
)
```

### Multi-Strategy Trading
Run multiple instances with different strategies:
```powershell
# Terminal 1
python live_trader.py --strategy ../Backtest/codes/rsi_strategy.py

# Terminal 2
python live_trader.py --strategy ../Backtest/codes/ema_strategy.py --config .env.ema
```

**Note:** Use different `MAGIC_NUMBER` for each strategy to avoid conflicts.

---

## 🧪 Testing Plan

### Phase 1: Dry-Run Testing
```powershell
# 1. Run in dry-run mode
python live_trader.py --strategy ../Backtest/codes/my_strategy.py --dry-run

# 2. Monitor dashboard
# Open http://127.0.0.1:5000

# 3. Check logs
Get-Content logs\live_trader.log -Tail 50

# 4. Verify signals are generated
# Check dashboard "Recent Signals" table

# 5. Test kill-switch
New-Item -Path EMERGENCY_STOP -ItemType File
# Trader should stop within 1 interval
```

### Phase 2: Demo Account Testing
```powershell
# 1. Configure demo account in .env
# MT5_LOGIN=demo_account_number
# MT5_PASSWORD=demo_password
# DRY_RUN=false

# 2. Start with small limits
# MAX_POSITION_SIZE=0.01
# MAX_DAILY_TRADES=3

# 3. Run trader
python live_trader.py --strategy ../Backtest/codes/my_strategy.py

# 4. Monitor for 1-2 weeks
# Check daily P/L, success rate, slippage
```

### Phase 3: Paper Trading (Live Prices, Simulated Orders)
- Use `DRY_RUN=true` but connect to live MT5
- Monitor slippage and execution quality
- Compare backtest vs live signal generation

### Phase 4: Small-Volume Live Trading
```powershell
# 1. Use live account with minimal capital
# 2. Set very conservative limits
# MAX_POSITION_SIZE=0.01
# DEFAULT_RISK_PCT=0.5
# MAX_DAILY_TRADES=2
# MAX_DAILY_LOSS_PCT=2.0

# 3. Enable all alerts
# ENABLE_ALERTS=true

# 4. Monitor closely for first week
```

### Phase 5: Full Production
- Gradually increase position sizes and limits
- Monitor daily P/L vs backtest expectations
- Adjust strategy parameters based on live performance

---

## 🐛 Troubleshooting

### MT5 Connection Fails
**Error:** `MT5 initialize failed: (-1, 'Module not found')`

**Solutions:**
- Ensure MT5 terminal is installed
- Verify `MT5_PATH` in `.env` points to `terminal64.exe`
- Try running MT5 terminal manually first
- Check `mt5.initialize()` without path (auto-detect):
  ```python
  mt5.initialize()  # Remove path parameter
  ```

### Symbol Not Available
**Error:** `Failed to select symbol: EURUSD`

**Solutions:**
- Symbol must be in Market Watch (MT5 terminal)
- Right-click Market Watch → "Symbols" → Add symbol
- Or programmatically: `mt5.symbol_select('EURUSD', True)`

### Orders Rejected
**Error:** `Order failed: TRADE_RETCODE_INVALID_STOPS`

**Solutions:**
- Check broker's minimum stop distance
- Ensure SL is not too close to entry price
- Verify lot size meets broker's min/max/step
- Use `mt5.order_check()` for detailed validation

### High Slippage
**Issue:** Execution price differs significantly from signal price

**Solutions:**
- Increase `deviation` in order request (default 20 points)
- Use LIMIT orders instead of MARKET orders
- Trade during liquid hours
- Avoid news events

### Daily Limit Reached Prematurely
**Issue:** "Daily trade limit reached" but you want to trade more

**Solutions:**
- Increase `MAX_DAILY_TRADES` in `.env`
- Check if limit is appropriate for your strategy frequency
- Review if strategy is over-trading

---

## 📚 API Reference

### BacktestingBridge

```python
bridge = BacktestingBridge(strategy_class)

# Generate signals
signals = bridge.generate_signals(
    symbol='EURUSD',
    from_ts=datetime(2025, 10, 1),
    to_ts=datetime(2025, 10, 18),
    timeframe='1d',
    indicators={'RSI': {'timeperiod': 14}}
)
# Returns: DataFrame with columns [signal, confidence, price, strategy_id]

# Calculate position size
volume = bridge.position_size(
    account_balance=10000,
    risk_pct=1.0,
    stop_loss_price=1.0920,
    entry_price=1.0950,
    symbol='EURUSD'
)
# Returns: float (lot size)

# Build order request
order_request = bridge.build_order_request(
    signal_row=signal,
    volume=0.01,
    meta={'symbol': 'EURUSD', 'magic': 123456, 'sl': 1.0920},
    symbol_info=symbol_info
)
# Returns: dict ready for mt5.order_send()

# Pre-check order
result = bridge.simulate_precheck(order_request, account_info)
# Returns: {'pass': bool, 'reason': str, 'warnings': list}
```

### MT5Connector

```python
connector = MT5Connector(config)

# Initialize connection
connector.initialize()

# Get account info
account = connector.get_account_info()
# Returns: dict with balance, equity, margin, etc.

# Get symbol info
symbol_info = connector.get_symbol_info('EURUSD')
# Returns: dict with bid, ask, spread, min/max volume, etc.

# Send order
result = connector.send_order(order_request)
# Returns: dict with retcode, deal/order IDs, executed price

# Get positions
positions = connector.get_positions()
# Returns: list of position dicts

# Shutdown
connector.shutdown()
```

### OrderExecutor

```python
executor = OrderExecutor(config, connector)

# Execute order with retry
result = executor.execute_order(
    order_request=order_request,
    client_order_id='unique_id',
    allow_retry=True
)
# Returns: {'success': bool, 'mt5_order_id': int, 'message': str, ...}

# Get order status
status = executor.get_order_status('client_order_id')
# Returns: {'status': str, 'details': dict}

# Get summary
summary = executor.get_execution_summary()
# Returns: {'total_orders': int, 'executed': int, 'failed': int, 'success_rate': float}
```

---

## 🔒 Security Best Practices

### 1. Credentials Management
- **Never commit `.env` to version control** (use `.gitignore`)
- Consider using Windows Credential Manager:
  ```python
  import keyring
  password = keyring.get_password('MT5', 'account_login')
  ```

### 2. File Permissions
```powershell
# Restrict .env to your user account only
icacls .env /inheritance:r /grant:r "$env:USERNAME:F"
```

### 3. API Keys (Telegram/Webhooks)
- Use environment variables, not hardcoded values
- Rotate keys periodically
- Limit webhook URL exposure

### 4. Audit Logs
- Review audit DB regularly for suspicious activity
- Monitor for:
  - Unexpected order volumes
  - Repeated failures
  - Unusual trading patterns

---

## 🤝 Contributing

To extend the Live module:

1. **Add new safety check**: Edit `state_manager.py` → `can_trade()`
2. **Custom alert channel**: Edit `alerts.py` → Add new method
3. **Enhanced position sizing**: Edit `backtesting_bridge.py` → `position_size()`
4. **New dashboard features**: Edit `dashboard.py` → Add route & HTML

---

## 📄 License

Part of AlgoAgent project. See parent directory for license.

---

## 📞 Support

For issues:
1. Check logs: `logs/live_trader.log`
2. Check audit DB: `data/audit.db`
3. Review MT5 terminal logs (Tools → Journal)
4. Enable DEBUG logging: `LOG_LEVEL=DEBUG` in `.env`

---

## ✅ Checklist Before Going Live

- [ ] Tested extensively in dry-run mode
- [ ] Validated on demo account for 1+ weeks
- [ ] Reviewed backtesting performance vs live performance
- [ ] Set conservative risk limits (`DEFAULT_RISK_PCT`, `MAX_POSITION_SIZE`)
- [ ] Configured daily limits (`MAX_DAILY_TRADES`, `MAX_DAILY_LOSS_PCT`)
- [ ] Enabled alerts (`TELEGRAM_BOT_TOKEN`, `ALERT_WEBHOOK_URL`)
- [ ] Tested kill-switch mechanism
- [ ] Verified broker allows automated trading (EA enabled)
- [ ] Documented expected P/L and drawdown targets
- [ ] Have a plan for monitoring and intervention

---

**Remember:** 
- 🟢 Start with `DRY_RUN=true`
- 🟡 Test on demo account
- 🔴 Go live with minimal capital
- Always have a kill-switch ready!

Good luck and trade responsibly! 🚀📈
