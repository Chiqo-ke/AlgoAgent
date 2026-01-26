# SimBroker API Reference for Strategy Generation

**Version:** 1.0.0  
**Last Updated:** January 21, 2026

This document provides the complete API reference for generating trading strategies that use the SimBroker backtesting engine. Follow these specifications exactly to avoid runtime errors.

---

## Table of Contents
1. [File Structure & Imports](#file-structure--imports)
2. [Configuration Setup](#configuration-setup)
3. [Signal Schema](#signal-schema)
4. [SimBroker Methods](#simbroker-methods)
5. [Complete Working Example](#complete-working-example)
6. [Common Errors & Solutions](#common-errors--solutions)

---

## File Structure & Imports

### Directory Structure
```
monolithic_agent/
├── Backtest/
│   ├── sim_broker.py          ← Note: underscore!
│   ├── config.py
│   ├── canonical_schema.py
│   ├── tools.py
│   └── codes/
│       └── your_strategy.py   ← Generated strategy goes here
```

### CRITICAL: Correct Import Pattern

**✅ CORRECT - Use this pattern:**
```python
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path (codes -> Backtest -> monolithic_agent)
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import with Backtest prefix and sim_broker (with underscore)
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import OrderSide, OrderAction
from Backtest import tools
```

**❌ FORBIDDEN - These will cause ModuleNotFoundError:**
```python
# Wrong: Missing Backtest prefix
from sim_broker import SimBroker

# Wrong: Missing Backtest prefix
from simbroker import SimBroker

# Wrong: Incorrect module name (no underscore)
from Backtest.simbroker import SimBroker

# Wrong: Direct import without Backtest
import sim_broker
import simbroker
```

---

## Configuration Setup

### BacktestConfig Class

**Purpose:** Configure backtesting parameters  
**Location:** `Backtest.config.BacktestConfig`

**Required Parameters:**
```python
from Backtest.config import BacktestConfig

config = BacktestConfig(
    symbol="AAPL",              # Trading symbol
    start_date="2024-01-01",    # Start date (YYYY-MM-DD)
    end_date="2024-12-31",      # End date (YYYY-MM-DD)
    start_cash=100000.0,        # Initial capital
    commission=0.001,           # Commission (0.1% = 0.001)
    slippage=0.0005            # Slippage (0.05% = 0.0005)
)
```

**All Available Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `symbol` | str | Yes | - | Trading symbol (e.g., "AAPL") |
| `start_date` | str | Yes | - | Backtest start (YYYY-MM-DD) |
| `end_date` | str | Yes | - | Backtest end (YYYY-MM-DD) |
| `start_cash` | float | Yes | - | Initial capital |
| `commission` | float | No | 0.001 | Commission rate |
| `slippage` | float | No | 0.0005 | Slippage rate |
| `use_cache` | bool | No | True | Use cached data |

---

## Signal Schema

### Required Signal Format

**CRITICAL:** All signals MUST include these exact fields with correct data types and valid enum values.

```python
signal = {
    'signal_id': str,        # Unique ID (e.g., 'sig_0001')
    'timestamp': str,        # ISO format (e.g., '2024-01-15T10:30:00')
    'symbol': str,           # Trading symbol (e.g., 'AAPL')
    'side': str,             # OrderSide.BUY or OrderSide.SELL
    'action': str,           # OrderAction value (see below)
    'order_type': str,       # 'MARKET' or 'LIMIT'
    'size': int,             # Number of shares (positive integer)
    'meta': dict            # Optional metadata (e.g., {'reason': 'SMA cross'})
}
```

### Valid Enum Values

**OrderSide (from `Backtest.canonical_schema`):**
- `OrderSide.BUY` = `"BUY"` ✅
- `OrderSide.SELL` = `"SELL"` ✅
- ❌ NOT "LONG", "SHORT", or "CLOSE"

**OrderAction (from `Backtest.canonical_schema`):**
- `OrderAction.ENTRY` = `"ENTRY"` ✅ (Open new position)
- `OrderAction.EXIT` = `"EXIT"` ✅ (Close existing position)
- `OrderAction.MODIFY` = `"MODIFY"` (Modify existing order)
- `OrderAction.CANCEL` = `"CANCEL"` (Cancel pending order)
- ❌ NOT "BUY", "SELL", "OPEN", or "CLOSE"

### Signal Examples

**✅ CORRECT Buy Signal:**
```python
signal_id = 0
# ... in loop:
signal_id += 1
buy_signal = {
    'signal_id': f'sig_{signal_id:04d}',  # 'sig_0001'
    'timestamp': datetime(2024, 1, 15, 10, 30).isoformat(),
    'symbol': 'AAPL',
    'side': 'BUY',          # or OrderSide.BUY
    'action': 'ENTRY',      # or OrderAction.ENTRY
    'order_type': 'MARKET',
    'size': 100,
    'meta': {'reason': 'Bullish crossover', 'indicator': 'SMA'}
}
broker.submit_signal(buy_signal)
```

**✅ CORRECT Sell Signal:**
```python
signal_id += 1
sell_signal = {
    'signal_id': f'sig_{signal_id:04d}',  # 'sig_0002'
    'timestamp': datetime(2024, 2, 20, 14, 0).isoformat(),
    'symbol': 'AAPL',
    'side': 'SELL',         # or OrderSide.SELL
    'action': 'EXIT',       # or OrderAction.EXIT
    'order_type': 'MARKET',
    'size': 100,
    'meta': {'reason': 'Take profit', 'pnl': 500.0}
}
broker.submit_signal(sell_signal)
```

**❌ INCORRECT Signals (Common Mistakes):**
```python
# Missing signal_id
bad_signal_1 = {
    'timestamp': '2024-01-15T10:30:00',
    'symbol': 'AAPL',
    # ... other fields
}

# Wrong side value
bad_signal_2 = {
    'signal_id': 'sig_0001',
    'side': 'LONG',  # ❌ Should be 'BUY'
    # ...
}

# Wrong action value
bad_signal_3 = {
    'signal_id': 'sig_0001',
    'action': 'BUY',  # ❌ Should be 'ENTRY'
    # ...
}

# Wrong parameter name
bad_signal_4 = {
    'signal_id': 'sig_0001',
    'quantity': 100,  # ❌ Should be 'size'
    # ...
}

# Missing required meta structure
bad_signal_5 = {
    'signal_id': 'sig_0001',
    'reason': 'Buy signal',  # ❌ Should be 'meta': {'reason': 'Buy signal'}
    # ...
}
```

---

## SimBroker Methods

### Initialization

**✅ CORRECT:**
```python
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig

# Create config
config = BacktestConfig(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31",
    start_cash=100000.0
)

# Initialize broker with config object
broker = SimBroker(config)
```

**❌ INCORRECT (Old API - Will Fail):**
```python
# This will raise TypeError
broker = SimBroker(
    symbol="AAPL",          # ❌ Not accepted
    start_date="2024-01-01",
    end_date="2024-12-31",
    start_cash=100000.0
)
```

### Core Trading Methods

#### `step_to(timestamp, market_data)`
Step broker forward to specific timestamp with market data.

**Parameters:**
- `timestamp` (datetime): Current time
- `market_data` (dict): Nested dict format: `{symbol: {price_data}}`

**Market Data Format:**
```python
market_data = {
    'AAPL': {
        'open': 150.25,
        'high': 152.10,
        'low': 149.80,
        'close': 151.50,
        'volume': 1000000
    }
}

broker.step_to(current_timestamp, market_data)
```

#### `submit_signal(signal)`
Submit trading signal to broker.

**Parameters:**
- `signal` (dict): Signal dict following canonical schema (see Signal Schema section)

**Returns:** None

**Example:**
```python
signal = {
    'signal_id': 'sig_0001',
    'timestamp': datetime.now().isoformat(),
    'symbol': 'AAPL',
    'side': 'BUY',
    'action': 'ENTRY',
    'order_type': 'MARKET',
    'size': 100,
    'meta': {'strategy': 'momentum'}
}

broker.submit_signal(signal)
```

### Account Information Methods

#### `get_account_snapshot()`
Get current account state.

**Returns:** dict
```python
{
    'cash': 50000.0,
    'equity': 75000.0,
    'positions': {...},
    'buying_power': 50000.0
}
```

#### `get_equity()`
Get current total equity (cash + positions value).

**Returns:** float

#### `get_equity_curve()`
Get historical equity values.

**Returns:** List[dict]
```python
[
    {'timestamp': '2024-01-01T00:00:00', 'equity': 100000.0},
    {'timestamp': '2024-01-02T00:00:00', 'equity': 101500.0},
    # ...
]
```

### Performance & Analytics Methods

#### `get_statistics()`
Get backtest performance statistics.

**Returns:** dict
```python
{
    'total_return': 15.5,        # Percentage
    'trade_count': 25,
    'win_rate': 60.0,            # Percentage
    'max_drawdown': -8.2,        # Percentage
    'sharpe_ratio': 1.85,
    'profit_factor': 2.1,
    'equity': 115500.0
}
```

**❌ INCORRECT Method Name:**
```python
# This method does NOT exist
metrics = broker.get_metrics()  # ❌ Will raise AttributeError
```

#### `get_trade_log()`
Get list of all executed trades.

**Returns:** List[dict]

#### `get_fills()`
Get list of all order fills.

**Returns:** List[dict]

#### `get_order(order_id)`
Get specific order details.

**Parameters:**
- `order_id` (str): Order ID

**Returns:** dict

---

## Complete Working Example

This is a fully working SMA crossover strategy demonstrating correct API usage:

```python
#!/usr/bin/env python3
"""
SMA Crossover Strategy - Complete Working Example
Demonstrates correct SimBroker API usage
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import os

# === CRITICAL: Correct Import Setup ===
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Set Django settings (required for some features)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import OrderSide, OrderAction
from Backtest import tools


def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def main():
    """Main strategy execution"""
    
    # === 1. Configuration ===
    config = BacktestConfig(
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2024-06-30",
        start_cash=100000.0,
        commission=0.001,
        slippage=0.0005
    )
    
    # === 2. Initialize Broker ===
    broker = SimBroker(config)
    
    # === 3. Generate Mock Data (30 days) ===
    start = datetime.strptime(config.start_date, "%Y-%m-%d")
    mock_data = []
    base_price = 150.0
    
    for i in range(30):
        timestamp = start + timedelta(days=i)
        # Simple trending data
        price = base_price + (i * 0.5) + (i % 5 - 2)
        
        mock_data.append({
            'timestamp': timestamp,
            'open': price - 0.5,
            'high': price + 1.0,
            'low': price - 1.0,
            'close': price,
            'volume': 1000000
        })
    
    # === 4. Strategy Logic ===
    close_prices = []
    position = 0
    signal_id = 0
    
    for i, bar in enumerate(mock_data):
        timestamp = bar['timestamp']
        close = bar['close']
        close_prices.append(close)
        
        # Step broker forward with correct market data format
        market_data = {
            config.symbol: {
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'volume': bar['volume']
            }
        }
        broker.step_to(timestamp, market_data)
        
        # Calculate indicators (need at least 10 bars)
        if len(close_prices) < 10:
            continue
        
        sma_5 = calculate_sma(close_prices, 5)
        sma_10 = calculate_sma(close_prices, 10)
        
        # === 5. Generate Signals (Correct Schema) ===
        
        # Buy signal: 5-period SMA crosses above 10-period SMA
        if position == 0 and sma_5 > sma_10:
            signal_id += 1
            signal = {
                'signal_id': f'sig_{signal_id:04d}',
                'timestamp': timestamp.isoformat(),
                'symbol': config.symbol,
                'side': OrderSide.BUY,        # 'BUY'
                'action': OrderAction.ENTRY,   # 'ENTRY'
                'order_type': 'MARKET',
                'size': 10,
                'meta': {
                    'reason': f'SMA cross up: {sma_5:.2f} > {sma_10:.2f}',
                    'sma_5': sma_5,
                    'sma_10': sma_10
                }
            }
            broker.submit_signal(signal)
            position = 10
            print(f"[{timestamp.date()}] BUY: {signal['size']} shares @ ${close:.2f}")
        
        # Sell signal: 5-period SMA crosses below 10-period SMA
        elif position > 0 and sma_5 < sma_10:
            signal_id += 1
            signal = {
                'signal_id': f'sig_{signal_id:04d}',
                'timestamp': timestamp.isoformat(),
                'symbol': config.symbol,
                'side': OrderSide.SELL,       # 'SELL'
                'action': OrderAction.EXIT,    # 'EXIT'
                'order_type': 'MARKET',
                'size': 10,
                'meta': {
                    'reason': f'SMA cross down: {sma_5:.2f} < {sma_10:.2f}',
                    'sma_5': sma_5,
                    'sma_10': sma_10
                }
            }
            broker.submit_signal(signal)
            position = 0
            print(f"[{timestamp.date()}] SELL: {signal['size']} shares @ ${close:.2f}")
    
    # === 6. Get Results (Correct Method) ===
    stats = broker.get_statistics()  # NOT get_metrics()
    
    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    print(f"Total Trades:    {stats.get('trade_count', 0)}")
    print(f"Win Rate:        {stats.get('win_rate', 0):.2f}%")
    print(f"Total Return:    {stats.get('total_return', 0):.2f}%")
    print(f"Sharpe Ratio:    {stats.get('sharpe_ratio', 0):.2f}")
    print(f"Max Drawdown:    {stats.get('max_drawdown', 0):.2f}%")
    print(f"Final Equity:    ${stats.get('equity', config.start_cash):.2f}")
    print("="*60)


if __name__ == "__main__":
    main()
```

---

## Common Errors & Solutions

### 1. ModuleNotFoundError: No module named 'Backtest.simbroker'

**Error:**
```
ModuleNotFoundError: No module named 'Backtest.simbroker'
```

**Cause:** Incorrect module name (missing underscore)

**Solution:** Use `sim_broker` (with underscore)
```python
from Backtest.sim_broker import SimBroker  # ✅ Correct
```

### 2. TypeError: SimBroker.__init__() got unexpected keyword argument

**Error:**
```
TypeError: SimBroker.__init__() got unexpected keyword argument 'symbol'
```

**Cause:** Using old API with direct parameters instead of BacktestConfig

**Solution:** Use BacktestConfig object
```python
from Backtest.config import BacktestConfig

config = BacktestConfig(symbol="AAPL", ...)
broker = SimBroker(config)  # ✅ Correct
```

### 3. Signal validation failed: Invalid side/action

**Error:**
```
Signal validation failed: ['Invalid side: LONG', 'Invalid action: BUY']
```

**Cause:** Using incorrect enum values

**Solution:** Use correct OrderSide and OrderAction values
```python
signal = {
    'side': 'BUY',     # ✅ Not 'LONG'
    'action': 'ENTRY', # ✅ Not 'BUY'
    # ...
}
```

### 4. Signal.__init__() missing required positional argument

**Error:**
```
Signal.__init__() missing 1 required positional argument: 'signal_id'
```

**Cause:** Missing required field in signal dict

**Solution:** Include all required fields
```python
signal = {
    'signal_id': f'sig_{counter:04d}',  # ✅ Required
    'timestamp': datetime.now().isoformat(),
    # ... all other fields
}
```

### 5. AttributeError: 'SimBroker' object has no attribute 'get_metrics'

**Error:**
```
AttributeError: 'SimBroker' object has no attribute 'get_metrics'
```

**Cause:** Using incorrect method name

**Solution:** Use `get_statistics()` instead
```python
stats = broker.get_statistics()  # ✅ Correct method name
```

### 6. AttributeError: 'str' object has no attribute 'get'

**Error:**
```
AttributeError: 'str' object has no attribute 'get'
```

**Cause:** Incorrect market data format (flat dict instead of nested)

**Solution:** Use nested dict format
```python
# ✅ Correct format
market_data = {
    'AAPL': {  # Symbol as key
        'open': 150.0,
        'high': 151.0,
        # ...
    }
}
broker.step_to(timestamp, market_data)
```

---

## Validation Checklist

Before running your strategy, verify:

- [ ] Imports use `from Backtest.sim_broker import SimBroker` (with underscore)
- [ ] Path setup: `parent_dir = Path(__file__).parent.parent.parent`
- [ ] Config created: `config = BacktestConfig(...)`
- [ ] Broker initialized: `broker = SimBroker(config)`
- [ ] Signal has all required fields: signal_id, timestamp, symbol, side, action, order_type, size
- [ ] Signal uses correct enums: side='BUY'/'SELL', action='ENTRY'/'EXIT'
- [ ] Market data is nested: `{symbol: {price_data}}`
- [ ] Using `get_statistics()` not `get_metrics()`
- [ ] Django settings configured: `os.environ['DJANGO_SETTINGS_MODULE'] = 'algoagent_api.settings'`

---

**End of API Reference**
