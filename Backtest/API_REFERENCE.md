# SimBroker API Reference

**Version:** 1.0.0  
**Last Updated:** 2025-10-16  
**Status:** STABLE - DO NOT MODIFY

## Overview

SimBroker is the stable, immutable backtesting execution engine. All AI-generated trading strategies MUST use this API and MUST NOT modify the SimBroker implementation.

## Core Principles

1. **Immutable API** - Function signatures and behavior are fixed
2. **Canonical Schemas** - All data follows predefined JSON schemas
3. **Deterministic** - Same inputs always produce same outputs
4. **Safe** - Validates all inputs, enforces risk limits
5. **Observable** - Provides metrics, logs, and exports

## Installation

```python
from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
```

## Quick Start

```python
# Initialize broker
config = BacktestConfig(start_cash=100000)
broker = SimBroker(config)

# Submit a signal
signal = create_signal(
    timestamp=datetime.now(),
    symbol="AAPL",
    side=OrderSide.BUY,
    action=OrderAction.ENTRY,
    order_type=OrderType.MARKET,
    size=100
)
order_id = broker.submit_signal(signal.to_dict())

# Process market data
market_data = {
    "AAPL": {"open": 150, "high": 151, "low": 149, "close": 150.5, "volume": 1000000}
}
broker.step_to(datetime.now(), market_data)

# Get results
snapshot = broker.get_account_snapshot()
metrics = broker.compute_metrics()
broker.export_trades("trades.csv")
```

---

## Stable API Methods

### `submit_signal(signal: dict) -> str`

**Purpose:** Submit a trading signal to the broker.

**Parameters:**
- `signal` (dict): Signal dictionary matching canonical schema

**Returns:**
- `str`: Order ID if accepted, empty string if rejected

**Signal Schema:**
```python
{
    "signal_id": "unique-id",        # Auto-generated if not provided
    "timestamp": datetime,            # Required
    "symbol": "AAPL",                # Required
    "side": "BUY" | "SELL",          # Required: OrderSide.BUY or OrderSide.SELL
    "action": "ENTRY" | "EXIT" | "MODIFY" | "CANCEL",  # Required
    "order_type": "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT",  # Required
    "size": 100,                     # Required: positive number
    "size_type": "SHARES",           # Optional: default SHARES
    "price": 150.0,                  # Required for LIMIT orders
    "stop_price": 145.0,             # Required for STOP orders
    "risk_params": {...},            # Optional
    "strategy_id": "my-strategy",    # Optional
    "meta": {}                       # Optional metadata
}
```

**Example:**
```python
signal_dict = {
    "signal_id": "sig-001",
    "timestamp": datetime(2025, 1, 1, 9, 30),
    "symbol": "AAPL",
    "side": "BUY",
    "action": "ENTRY",
    "order_type": "MARKET",
    "size": 100
}
order_id = broker.submit_signal(signal_dict)
```

**Validation:**
- Signal must match canonical schema
- Size must be positive
- Price required for LIMIT/STOP_LIMIT
- Stop price required for STOP/STOP_LIMIT

---

### `step_to(timestamp: datetime, market_data: dict = None)`

**Purpose:** Advance simulation to timestamp and process pending orders.

**Parameters:**
- `timestamp` (datetime): Time to advance to
- `market_data` (dict, optional): Market data by symbol

**Market Data Schema:**
```python
{
    "AAPL": {
        "open": 150.0,      # Required
        "high": 151.0,      # Required
        "low": 149.0,       # Required
        "close": 150.5,     # Required
        "volume": 1000000,  # Optional (needed for liquidity checks)
        "bid": 150.4,       # Optional
        "ask": 150.6        # Optional
    },
    "TSLA": {...}
}
```

**Behavior:**
1. Updates current time
2. Processes all active orders
3. Executes fills based on market data
4. Updates account state
5. Records equity snapshot

**Example:**
```python
market_data = {
    "AAPL": {
        "open": 150.0,
        "high": 151.5,
        "low": 149.5,
        "close": 150.75,
        "volume": 5000000
    }
}
broker.step_to(datetime(2025, 1, 1, 10, 0), market_data)
```

---

### `get_order(order_id: str) -> dict`

**Purpose:** Retrieve order details.

**Parameters:**
- `order_id` (str): Order ID returned from submit_signal

**Returns:**
- `dict`: Order details, or empty dict if not found

**Order Schema:**
```python
{
    "order_id": "ord-123",
    "signal_id": "sig-001",
    "timestamp": "2025-01-01T09:30:00",
    "symbol": "AAPL",
    "side": "BUY",
    "order_type": "MARKET",
    "price": None,
    "size_requested": 100,
    "size_filled": 100,
    "status": "FILLED",  # PENDING/PARTIAL/FILLED/CANCELLED
    "fills": [...]
}
```

---

### `cancel_order(order_id: str) -> bool`

**Purpose:** Cancel a pending order.

**Parameters:**
- `order_id` (str): Order ID to cancel

**Returns:**
- `bool`: True if cancelled, False if not found or already complete

**Example:**
```python
success = broker.cancel_order("ord-123")
```

---

### `get_account_snapshot() -> dict`

**Purpose:** Get current account state.

**Returns:**
- `dict`: Account snapshot

**Account Snapshot Schema:**
```python
{
    "timestamp": "2025-01-01T10:00:00",
    "cash": 95000.0,
    "equity": 100500.0,
    "portfolio_value": 5500.0,
    "used_margin": 0.0,
    "available_margin": 100500.0,
    "unrealized_pnl": 500.0,
    "realized_pnl": 0.0,
    "positions": [
        {
            "symbol": "AAPL",
            "size": 100,          # Positive=long, negative=short
            "avg_price": 150.0,
            "last_price": 155.0,
            "unrealized_pnl": 500.0
        }
    ]
}
```

---

### `get_equity_curve() -> List[dict]`

**Purpose:** Get historical equity snapshots.

**Returns:**
- `List[dict]`: List of account snapshots over time

**Example:**
```python
curve = broker.get_equity_curve()
for snapshot in curve:
    print(f"{snapshot['timestamp']}: ${snapshot['equity']:.2f}")
```

---

### `export_trades(path: str)`

**Purpose:** Export all trade records to CSV.

**Parameters:**
- `path` (str): Output file path

**Trade Record Format:**
```csv
trade_id,order_id,signal_id,timestamp,symbol,side,price,size,commission,slippage,realized_pnl,note
```

**Example:**
```python
broker.export_trades("results/trades.csv")
```

---

### `compute_metrics() -> dict`

**Purpose:** Calculate all performance metrics.

**Returns:**
- `dict`: Complete metrics dictionary

**Metrics Schema:**
```python
{
    # Metadata
    "version": "1.0.0",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "duration_days": 365,
    
    # Account
    "start_cash": 100000.0,
    "final_equity": 123456.78,
    "peak_equity": 125000.0,
    
    # P&L
    "net_profit": 23456.78,
    "gross_profit": 45000.0,
    "gross_loss": 21543.22,
    
    # Trades
    "total_trades": 140,
    "winning_trades": 78,
    "losing_trades": 62,
    "win_rate": 0.557,
    
    # Performance
    "profit_factor": 2.09,
    "average_trade": 167.55,
    "average_win": 576.92,
    "average_loss": -347.47,
    "expectancy": 167.55,
    
    # Risk
    "max_drawdown_abs": 8500.0,
    "max_drawdown_pct": 0.068,
    "recovery_factor": 2.76,
    
    # Returns
    "total_return_pct": 23.46,
    "cagr": 21.34,
    
    # Risk-adjusted
    "sharpe_ratio": 1.45,
    "sortino_ratio": 2.13,
    "calmar_ratio": 3.14,
    
    # Streaks
    "max_consecutive_wins": 7,
    "max_consecutive_losses": 5,
    
    # Other
    "largest_win": 2500.0,
    "largest_loss": 1200.0,
    "total_commission": 1800.0,
    "total_slippage": 450.0
}
```

**Example:**
```python
metrics = broker.compute_metrics()
print(f"Net Profit: ${metrics['net_profit']:,.2f}")
print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
```

---

## Configuration

### BacktestConfig Parameters

```python
from config import BacktestConfig, get_realistic_config

# Use defaults
config = BacktestConfig()

# Or customize
config = BacktestConfig(
    start_cash=100000.0,
    fee_flat=1.0,
    fee_pct=0.001,
    slippage_pct=0.0005,
    leverage=1.0,
    fill_policy="realistic"
)

# Or use presets
config = get_realistic_config()  # Realistic fees/slippage
```

**Key Parameters:**
- `start_cash`: Starting capital
- `fee_flat`: Fixed fee per trade
- `fee_pct`: Percentage fee (0.001 = 0.1%)
- `slippage_pct`: Slippage percentage
- `leverage`: Maximum leverage allowed
- `fill_policy`: "aggressive", "realistic", or "conservative"
- `require_stop_loss`: Warn if no stop loss
- `max_drawdown_stop`: Auto-stop at % drawdown

See `config.py` for all 30+ parameters.

---

## Helper Functions

### Creating Signals

```python
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType

signal = create_signal(
    timestamp=datetime.now(),
    symbol="AAPL",
    side=OrderSide.BUY,
    action=OrderAction.ENTRY,
    order_type=OrderType.MARKET,
    size=100,
    strategy_id="my-strategy"
)
```

---

## Canonical Enums

```python
from canonical_schema import OrderSide, OrderAction, OrderType

# Sides
OrderSide.BUY    # Open long or close short
OrderSide.SELL   # Open short or close long

# Actions
OrderAction.ENTRY    # Open new position
OrderAction.EXIT     # Close position
OrderAction.MODIFY   # Modify existing order
OrderAction.CANCEL   # Cancel order

# Order Types
OrderType.MARKET      # Fill at market price
OrderType.LIMIT       # Fill at limit price or better
OrderType.STOP        # Trigger at stop, fill at market
OrderType.STOP_LIMIT  # Trigger at stop, fill at limit
```

---

## Error Handling

```python
# Signals are validated automatically
order_id = broker.submit_signal(invalid_signal)
if not order_id:
    print("Signal rejected - check logs")

# Orders may not fill
order = broker.get_order(order_id)
if order['status'] == 'PENDING':
    print("Order not filled yet")

# Check account state
snapshot = broker.get_account_snapshot()
if snapshot['equity'] < broker.config.start_cash * 0.8:
    print("Warning: 20% drawdown")
```

---

## Best Practices

### 1. Always Validate Signals

```python
from canonical_schema import validate_signal

errors = validate_signal(signal_dict)
if errors:
    print(f"Invalid signal: {errors}")
else:
    broker.submit_signal(signal_dict)
```

### 2. Check Order Status

```python
order_id = broker.submit_signal(signal)
if order_id:
    order = broker.get_order(order_id)
    print(f"Order status: {order['status']}")
```

### 3. Monitor Account State

```python
snapshot = broker.get_account_snapshot()
equity = snapshot['equity']
cash = snapshot['cash']
positions = len(snapshot['positions'])
```

### 4. Export Results

```python
broker.export_trades("results/trades.csv")
metrics = broker.compute_metrics()

import json
with open("results/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
```

---

## Limitations

1. **No real broker connection** - Simulation only
2. **No tick data** - OHLC bars only
3. **Simple slippage model** - Fixed percentage by default
4. **No partial bar data** - Intrabar simulation uses OHLC rules
5. **Single currency** - Multi-currency needs manual conversion

---

## Support

- Full source code in `Backtest.py/` directory
- Canonical schemas in `canonical_schema.py`
- Configuration presets in `config.py`
- Example strategies in `examples/`

**Remember:** MUST NOT EDIT SimBroker internals. Use only the stable API.
