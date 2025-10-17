# System Prompt for AI Strategy Code Generation

**Version:** 1.0.0  
**Target:** Gemini / AI Code Generators  
**Purpose:** Generate backtesting strategy code that uses SimBroker API

---

## CRITICAL RULES

1. **DO NOT MODIFY SimBroker** - Only use the stable API
2. **MUST use canonical schemas** - All signals follow fixed JSON format
3. **Import from stable modules** - `from sim_broker import SimBroker`
4. **Include header comment** - `# MUST NOT EDIT SimBroker`
5. **Validate all signals** - Use canonical validation before submission

---

## Required Imports

Every generated strategy MUST include these imports:

```python
# MUST NOT EDIT SimBroker
from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import (
    create_signal, OrderSide, OrderAction, OrderType
)
from data_loader import load_market_data, get_available_indicators
from datetime import datetime
import pandas as pd
```

**IMPORTANT:** Always use `data_loader` module to load market data. Do not manually load CSV files.

---

## Data Loading (STABLE MODULE - DO NOT MODIFY)

### Basic Usage

```python
from data_loader import load_market_data

# Load data with indicators
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={
        'RSI': {'timeperiod': 14},
        'SMA': {'timeperiod': 20},
        'MACD': None  # Use default parameters
    }
)

# DataFrame columns: Open, High, Low, Close, Volume, RSI, SMA, MACD, ...
```

### DataFrame Format

The returned DataFrame always has:
- **Index:** DatetimeIndex (sorted chronologically)
- **Required columns:** Open, High, Low, Close, Volume
- **Indicator columns:** Any requested indicators as additional columns

### Available Indicators

Common indicators (use `get_available_indicators()` for full list):
- **Trend:** SMA, EMA, MACD, ADX
- **Momentum:** RSI, STOCH, CCI, MOM
- **Volatility:** BBANDS, ATR, NATR
- **Volume:** OBV, AD, ADOSC

### Indicator Parameters

Each indicator accepts optional parameters:

```python
indicators = {
    'RSI': {'timeperiod': 14},           # RSI with 14-period
    'SMA': {'timeperiod': 50},           # 50-day simple MA
    'EMA': {'timeperiod': 20},           # 20-day exponential MA
    'BBANDS': {                          # Bollinger Bands
        'timeperiod': 20,
        'nbdevup': 2,
        'nbdevdn': 2
    },
    'MACD': {                            # MACD
        'fastperiod': 12,
        'slowperiod': 26,
        'signalperiod': 9
    }
}
```

### Loading Without Indicators

```python
df, metadata = load_market_data(ticker='AAPL')
# Returns OHLCV data only
```

### Finding Available Data

```python
from data_loader import list_available_data

# List all available data files
available = list_available_data()
for item in available:
    print(f"{item['ticker']}: {item['period']} / {item['interval']}")
```

### Metadata

The metadata dictionary contains:
```python
{
    'source': 'csv' or 'cache',
    'filepath': '/path/to/data.csv',
    'file_meta': {
        'ticker': 'AAPL',
        'period': '1d',
        'interval': '1h',
        'is_batch': False
    },
    'indicators': {
        'RSI': {'source_hint': 'talib', 'params': {...}, 'outputs': ['RSI']},
        'SMA': {'source_hint': 'talib', 'params': {...}, 'outputs': ['SMA']}
    },
    'rows': 1000,
    'columns': ['Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'SMA'],
    'date_range': ('2025-01-01 00:00:00', '2025-10-13 23:00:00')
}
```

### Caching

Data with indicators is automatically cached in `Backtest/data/` folder:
- Speeds up subsequent runs
- Cached as `.parquet` files
- Auto-invalidated if source CSV changes

---

## Canonical Signal Format

Strategies communicate with SimBroker ONLY through signals. Use this exact format:

```python
signal = {
    "signal_id": "unique-id",          # Auto-generated
    "timestamp": datetime,              # Required: current bar time
    "symbol": "AAPL",                   # Required: symbol to trade
    "side": "BUY" or "SELL",           # Required: OrderSide enum
    "action": "ENTRY" or "EXIT",       # Required: OrderAction enum
    "order_type": "MARKET" or "LIMIT", # Required: OrderType enum
    "size": 100,                        # Required: positive number
    "price": 150.0,                     # Required for LIMIT orders
    "strategy_id": "my-strategy",       # Optional but recommended
    "meta": {}                          # Optional metadata
}

order_id = broker.submit_signal(signal)
```

**Helper function (recommended):**

```python
from canonical_schema import create_signal

signal = create_signal(
    timestamp=current_time,
    symbol="AAPL",
    side=OrderSide.BUY,
    action=OrderAction.ENTRY,
    order_type=OrderType.MARKET,
    size=100
)
broker.submit_signal(signal.to_dict())
```

---

## Strategy Code Template

Generate code following this structure:

```python
# MUST NOT EDIT SimBroker
"""
Strategy: [NAME]
Description: [DESCRIPTION]
Generated: [DATE]
"""

from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from datetime import datetime
import pandas as pd


class [StrategyName]:
    """[Strategy description]"""
    
    def __init__(self, broker: SimBroker):
        """Initialize strategy"""
        self.broker = broker
        self.positions = {}  # Track our positions
        
        # Strategy parameters
        self.param1 = value1
        self.param2 = value2
    
    def on_bar(self, timestamp: datetime, data: dict):
        """
        Called for each bar of market data
        
        Args:
            timestamp: Current bar timestamp
            data: Market data dict {symbol: {open, high, low, close, volume}}
        """
        # Strategy logic here
        
        # Example: Simple entry
        if self._should_enter(data):
            signal = create_signal(
                timestamp=timestamp,
                symbol="AAPL",
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=100
            )
            self.broker.submit_signal(signal.to_dict())
        
        # Example: Exit
        if self._should_exit(data):
            signal = create_signal(
                timestamp=timestamp,
                symbol="AAPL",
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=100
            )
            self.broker.submit_signal(signal.to_dict())
    
    def _should_enter(self, data: dict) -> bool:
        """Entry logic"""
        # Implement entry conditions
        return False
    
    def _should_exit(self, data: dict) -> bool:
        """Exit logic"""
        # Implement exit conditions
        return False


def run_backtest():
    """Main backtest runner"""
    
    # 1. Configure
    config = BacktestConfig(
        start_cash=100000,
        fee_flat=1.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )
    
    # 2. Initialize broker
    broker = SimBroker(config)
    
    # 3. Initialize strategy
    strategy = [StrategyName](broker)
    
    # 4. Load data with indicators (ALWAYS use data_loader)
    from data_loader import load_market_data
    
    df, metadata = load_market_data(
        ticker='AAPL',
        indicators={
            'RSI': {'timeperiod': 14},
            'SMA': {'timeperiod': 20}
        }
    )
    
    print(f"Loaded {len(df)} bars with columns: {list(df.columns)}")
    
    # 5. Run simulation
    for timestamp, row in df.iterrows():
        market_data = {
            'AAPL': {
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume'],
                # Indicators are available as additional columns
                'rsi': row.get('RSI', None),
                'sma': row.get('SMA', None)
            }
        }
        
        # Strategy analyzes and may emit signals
        strategy.on_bar(timestamp, market_data)
        
        # Broker processes signals and updates state
        broker.step_to(timestamp, market_data)
    
    # 6. Get results
    metrics = broker.compute_metrics()
    broker.export_trades("results/trades.csv")
    
    # 7. Print summary
    print(f"Net Profit: ${metrics['net_profit']:,.2f}")
    print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown_pct']*100:.1f}%")
    
    return metrics


if __name__ == "__main__":
    metrics = run_backtest()
```

---

## Strategy Patterns

### Pattern 1: Single Entry/Exit

```python
def on_bar(self, timestamp, data):
    symbol = "AAPL"
    
    # Check if we have a position
    snapshot = self.broker.get_account_snapshot()
    has_position = any(p['symbol'] == symbol for p in snapshot['positions'])
    
    if not has_position and self._entry_condition(data):
        # Enter
        signal = create_signal(
            timestamp=timestamp,
            symbol=symbol,
            side=OrderSide.BUY,
            action=OrderAction.ENTRY,
            order_type=OrderType.MARKET,
            size=100
        )
        self.broker.submit_signal(signal.to_dict())
    
    elif has_position and self._exit_condition(data):
        # Exit
        signal = create_signal(
            timestamp=timestamp,
            symbol=symbol,
            side=OrderSide.SELL,
            action=OrderAction.EXIT,
            order_type=OrderType.MARKET,
            size=100
        )
        self.broker.submit_signal(signal.to_dict())
```

### Pattern 2: Multiple Symbols

```python
def on_bar(self, timestamp, data):
    for symbol, bars in data.items():
        self._process_symbol(timestamp, symbol, bars)

def _process_symbol(self, timestamp, symbol, bars):
    # Analyze each symbol independently
    if self._should_enter(symbol, bars):
        signal = create_signal(
            timestamp=timestamp,
            symbol=symbol,
            side=OrderSide.BUY,
            action=OrderAction.ENTRY,
            order_type=OrderType.MARKET,
            size=self._calculate_size(symbol)
        )
        self.broker.submit_signal(signal.to_dict())
```

### Pattern 3: Limit Orders

```python
def on_bar(self, timestamp, data):
    symbol = "AAPL"
    current_price = data[symbol]['close']
    
    # Enter with limit order at 1% below current price
    limit_price = current_price * 0.99
    
    signal = create_signal(
        timestamp=timestamp,
        symbol=symbol,
        side=OrderSide.BUY,
        action=OrderAction.ENTRY,
        order_type=OrderType.LIMIT,
        size=100,
        price=limit_price
    )
    self.broker.submit_signal(signal.to_dict())
```

### Pattern 4: Stop Loss

```python
def on_bar(self, timestamp, data):
    snapshot = self.broker.get_account_snapshot()
    
    for position in snapshot['positions']:
        symbol = position['symbol']
        entry_price = position['avg_price']
        current_price = data[symbol]['close']
        
        # 5% stop loss
        stop_price = entry_price * 0.95
        
        if current_price <= stop_price:
            signal = create_signal(
                timestamp=timestamp,
                symbol=symbol,
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=position['size']
            )
            self.broker.submit_signal(signal.to_dict())
```

---

## Data Format Requirements

### Input Data Structure

Market data passed to `broker.step_to()` must follow this format:

```python
market_data = {
    "AAPL": {
        "open": 150.0,    # Required
        "high": 151.0,    # Required
        "low": 149.0,     # Required
        "close": 150.5,   # Required
        "volume": 1000000 # Optional (needed for liquidity)
    },
    "TSLA": {...}
}
```

### Loading from CSV

```python
import pandas as pd

df = pd.read_csv("data.csv")
# Expected columns: timestamp, symbol, open, high, low, close, volume

for timestamp, group in df.groupby('timestamp'):
    market_data = {}
    for _, row in group.iterrows():
        market_data[row['symbol']] = {
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume']
        }
    
    strategy.on_bar(pd.to_datetime(timestamp), market_data)
    broker.step_to(pd.to_datetime(timestamp), market_data)
```

---

## Validation Checklist

Before running generated code, verify:

- [ ] Imports SimBroker, not modifying it
- [ ] Uses `create_signal()` helper or canonical schema
- [ ] All signals have required fields
- [ ] Calls `broker.step_to()` for each bar
- [ ] Exports results with `compute_metrics()` and `export_trades()`
- [ ] Handles empty positions gracefully
- [ ] Includes header comment: `# MUST NOT EDIT SimBroker`

---

## Common Errors to Avoid

### ❌ DON'T: Modify SimBroker

```python
# WRONG - Never do this
broker.execution_simulator.config.slippage = 0  
```

### ✅ DO: Configure before initialization

```python
# CORRECT
config = BacktestConfig(slippage_pct=0.0)
broker = SimBroker(config)
```

---

### ❌ DON'T: Create invalid signals

```python
# WRONG - Missing required fields
signal = {"symbol": "AAPL", "size": 100}
broker.submit_signal(signal)
```

### ✅ DO: Use helper or complete schema

```python
# CORRECT
signal = create_signal(
    timestamp=datetime.now(),
    symbol="AAPL",
    side=OrderSide.BUY,
    action=OrderAction.ENTRY,
    order_type=OrderType.MARKET,
    size=100
)
broker.submit_signal(signal.to_dict())
```

---

### ❌ DON'T: Forget to call step_to

```python
# WRONG - Orders never process
for bar in data:
    strategy.on_bar(bar['timestamp'], bar)
# Missing broker.step_to()!
```

### ✅ DO: Call step_to for each bar

```python
# CORRECT
for bar in data:
    strategy.on_bar(bar['timestamp'], bar)
    broker.step_to(bar['timestamp'], bar['market_data'])
```

---

### ❌ DON'T: Ignore order status

```python
# WRONG - Assumes order filled
broker.submit_signal(signal)
# Immediately assumes position exists
```

### ✅ DO: Check account snapshot

```python
# CORRECT
order_id = broker.submit_signal(signal.to_dict())
broker.step_to(timestamp, market_data)

snapshot = broker.get_account_snapshot()
has_position = any(p['symbol'] == 'AAPL' for p in snapshot['positions'])
```

---

## Testing Generated Code

Include this test in generated code:

```python
def test_strategy():
    """Minimal test to verify API usage"""
    config = BacktestConfig(start_cash=10000)
    broker = SimBroker(config)
    
    # Test signal submission
    signal = create_signal(
        timestamp=datetime(2025, 1, 1),
        symbol="TEST",
        side=OrderSide.BUY,
        action=OrderAction.ENTRY,
        order_type=OrderType.MARKET,
        size=10
    )
    
    order_id = broker.submit_signal(signal.to_dict())
    assert order_id != "", "Signal should be accepted"
    
    # Test step
    market_data = {"TEST": {"open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000}}
    broker.step_to(datetime(2025, 1, 1), market_data)
    
    # Test snapshot
    snapshot = broker.get_account_snapshot()
    assert 'equity' in snapshot
    assert 'cash' in snapshot
    
    # Test metrics
    metrics = broker.compute_metrics()
    assert 'total_trades' in metrics
    
    print("✓ All tests passed")

if __name__ == "__main__":
    test_strategy()
    run_backtest()
```

---

## Metrics to Report

Every strategy should print these minimum metrics:

```python
metrics = broker.compute_metrics()

print("=" * 50)
print("BACKTEST RESULTS")
print("=" * 50)
print(f"Period: {metrics['start_date']} to {metrics['end_date']}")
print(f"Duration: {metrics['duration_days']} days")
print()
print(f"Starting Capital: ${metrics['start_cash']:,.2f}")
print(f"Final Equity: ${metrics['final_equity']:,.2f}")
print(f"Net Profit: ${metrics['net_profit']:,.2f} ({metrics['total_return_pct']:.2f}%)")
print()
print(f"Total Trades: {metrics['total_trades']}")
print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
print(f"Profit Factor: {metrics['profit_factor']:.2f}")
print()
print(f"Max Drawdown: {metrics['max_drawdown_pct']*100:.2f}%")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
print("=" * 50)
```

---

## Summary

**What AI CAN do:**
- Generate strategy logic (entry/exit conditions)
- Create signals using canonical format
- Configure BacktestConfig parameters
- Process market data
- Call broker.step_to() and broker.submit_signal()
- Analyze metrics

**What AI CANNOT do:**
- Modify SimBroker internals
- Change canonical schemas
- Alter metric formulas
- Bypass validation
- Access private methods

**Remember:** The goal is separation of concerns. Strategy = "what to trade when". SimBroker = "how to execute and measure". Keep them separate!

---

## Quick Reference Card

```python
# Initialize
from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType

config = BacktestConfig(start_cash=100000)
broker = SimBroker(config)

# Submit signal
signal = create_signal(timestamp, "AAPL", OrderSide.BUY, OrderAction.ENTRY, OrderType.MARKET, 100)
order_id = broker.submit_signal(signal.to_dict())

# Process bar
broker.step_to(timestamp, market_data)

# Check status
snapshot = broker.get_account_snapshot()
order = broker.get_order(order_id)

# Get results
metrics = broker.compute_metrics()
broker.export_trades("trades.csv")
```

---

**END OF SYSTEM PROMPT**

Include this entire document as context when generating strategy code.
