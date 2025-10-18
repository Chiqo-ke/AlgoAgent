# SimBroker - Stable Backtesting Execution Engine

**Version:** 1.0.0  
**Status:** Production Ready  
**API:** STABLE - Do Not Modify

---

## Overview

SimBroker is a production-ready, immutable backtesting framework designed specifically for AI-generated trading strategies. It provides a stable API that **MUST NOT be modified** by strategy code, ensuring reproducible, reliable backtesting results.

## Key Features

✅ **Immutable Core** - Stable API across all strategy implementations  
✅ **Canonical Schemas** - Fixed JSON schemas for all data structures  
✅ **Realistic Execution** - Market/limit/stop orders, slippage, fees, partial fills  
✅ **Comprehensive Metrics** - 30+ performance metrics with canonical formulas  
✅ **Risk Guardrails** - Position limits, leverage checks, drawdown stops  
✅ **Deterministic** - Same inputs always produce same outputs  
✅ **AI-Friendly** - Designed for code generation pipelines  

## Architecture

```
SimBroker (Main API)
├── OrderManager (Signal → Order conversion)
├── ExecutionSimulator (Fill logic)
├── AccountManager (Positions, P&L, equity)
├── MetricsEngine (Performance calculations)
└── Validators (Risk checks)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install pandas numpy
```

### 2. Basic Usage

```python
from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from datetime import datetime

# Initialize
config = BacktestConfig(start_cash=100000)
broker = SimBroker(config)

# Submit signal
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
    "AAPL": {
        "open": 150.0,
        "high": 151.0,
        "low": 149.0,
        "close": 150.5,
        "volume": 1000000
    }
}
broker.step_to(datetime.now(), market_data)

# Get results
snapshot = broker.get_account_snapshot()
metrics = broker.compute_metrics()
broker.export_trades("trades.csv")
```

### 3. Run Example

```bash
cd Backtest
python example_strategy.py
```

## Strategy Development

### ⚠️ Important: Correct Import Pattern

All strategies in the `codes/` directory **MUST** use the following import pattern to work with both backtesting and live trading:

```python
# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
```

**📖 See [`STRATEGY_TEMPLATE.md`](STRATEGY_TEMPLATE.md) for complete template and guidelines.**

### Generate New Strategy

Use the Gemini strategy generator (updated with correct imports):

```bash
cd Backtest
python gemini_strategy_generator.py
```

Or manually create using the template in `STRATEGY_TEMPLATE.md`.

### Example Strategies

All examples use the correct import pattern:
- `example_strategy.py` - Moving average crossover
- `rsi_strategy.py` - RSI-based trading
- `ema_strategy.py` - EMA crossover
- `codes/my_strategy.py` - Your custom strategies

## Stable API

The following methods are **STABLE** and must not be changed:

### Core Methods

```python
broker.submit_signal(signal: dict) -> str
broker.get_order(order_id: str) -> dict
broker.cancel_order(order_id: str) -> bool
broker.step_to(timestamp: datetime, market_data: dict) -> None
broker.get_account_snapshot() -> dict
broker.get_equity_curve() -> List[dict]
broker.export_trades(path: str) -> None
broker.compute_metrics() -> dict
```

See [`API_REFERENCE.md`](API_REFERENCE.md) for complete documentation.

## Configuration

### Preset Configurations

```python
from config import (
    get_default_config,      # Default settings
    get_realistic_config,    # Realistic fees/slippage
    get_zero_cost_config,    # No fees/slippage (optimistic)
    get_high_cost_config,    # High fees/slippage (conservative)
    get_futures_config,      # Futures trading
    get_forex_config,        # Forex trading
    get_crypto_config        # Crypto trading
)

config = get_realistic_config()
broker = SimBroker(config)
```

### Custom Configuration

```python
config = BacktestConfig(
    start_cash=100000.0,
    fee_flat=1.0,           # $1 flat fee
    fee_pct=0.001,          # 0.1% fee
    slippage_pct=0.0005,    # 0.05% slippage
    leverage=1.0,           # No leverage
    fill_policy="realistic"
)
```

### All Parameters (30+)

See [`config.py`](config.py) for complete list including:
- Account settings
- Fee structure
- Slippage model
- Execution parameters
- Risk controls
- Margin settings
- Output options

## Canonical Schemas

All data follows fixed schemas defined in [`canonical_schema.py`](canonical_schema.py):

### Signal Schema

```python
{
    "signal_id": "uuid",
    "timestamp": datetime,
    "symbol": "AAPL",
    "side": "BUY" | "SELL",
    "action": "ENTRY" | "EXIT" | "MODIFY" | "CANCEL",
    "order_type": "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT",
    "size": 100,
    "price": 150.0,  # For LIMIT orders
    "stop_price": 145.0,  # For STOP orders
    "strategy_id": "my-strategy"
}
```

### Order Schema

```python
{
    "order_id": "uuid",
    "signal_id": "uuid",
    "timestamp": datetime,
    "symbol": "AAPL",
    "side": "BUY",
    "order_type": "MARKET",
    "size_requested": 100,
    "size_filled": 100,
    "status": "FILLED"
}
```

### Account Snapshot Schema

```python
{
    "timestamp": datetime,
    "cash": 95000.0,
    "equity": 100500.0,
    "positions": [
        {
            "symbol": "AAPL",
            "size": 100,
            "avg_price": 150.0,
            "unrealized_pnl": 500.0
        }
    ]
}
```

## Performance Metrics

30+ metrics with **canonical formulas** (IMMUTABLE):

### Basic Metrics
- Net profit, Gross profit/loss
- Win rate, Total trades
- Average trade, Average win/loss

### Risk Metrics
- Max drawdown (absolute & %)
- Recovery factor
- Max consecutive wins/losses

### Return Metrics
- Total return %
- CAGR (Compound Annual Growth Rate)

### Risk-Adjusted Returns
- Sharpe ratio
- Sortino ratio
- Calmar ratio

See [`metrics_engine.py`](metrics_engine.py) for formulas.

## AI Integration

### For AI Code Generators (Gemini, etc.)

1. **Read** [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md) - Complete instructions for AI
2. **Reference** [`API_REFERENCE.md`](API_REFERENCE.md) - Full API documentation
3. **Follow** [`example_strategy.py`](example_strategy.py) - Template pattern

### Key Rules for AI

✅ **DO:**
- Import from `sim_broker`
- Use `create_signal()` helper
- Call `broker.submit_signal()` and `broker.step_to()`
- Check account snapshots for position state

❌ **DON'T:**
- Modify SimBroker internals
- Change canonical schemas
- Alter metric formulas
- Access private methods

### System Prompt Snippet

```
# MUST NOT EDIT SimBroker

All strategies MUST use the stable SimBroker interface.
Do NOT modify SimBroker. Use these functions:
- submit_signal(signal: dict) -> str
- step_to(timestamp: datetime, market_data: dict)
- get_account_snapshot() -> dict
- compute_metrics() -> dict

Strategy code must only produce canonical signal JSON objects.
```

## File Structure

```
Backtest.py/
├── __init__.py                  # Package exports
├── README.md                    # This file
├── API_REFERENCE.md             # Complete API docs
├── SYSTEM_PROMPT.md             # AI code generation guide
│
├── sim_broker.py                # Main SimBroker class
├── config.py                    # Configuration
├── canonical_schema.py          # Data schemas
│
├── order_manager.py             # Order lifecycle
├── execution_simulator.py       # Fill simulation
├── account_manager.py           # Position tracking
├── metrics_engine.py            # Performance metrics
├── validators.py                # Risk guardrails
│
└── example_strategy.py          # Example implementation
```

## Execution Semantics

### Market Orders
- Fill at next bar's open price
- Apply slippage and fees
- Immediate execution (no pending)

### Limit Orders
- Fill when price touches limit
- Fill at limit price or better
- May remain pending

### Stop Orders
- Trigger when stop price touched
- Convert to market order
- Fill at market price after trigger

### Partial Fills
- Based on liquidity constraints
- Configurable via `liquidity_limit_pct`
- Order status becomes `PARTIAL`

### Slippage Models
- **Fixed**: Percentage + constant
- **Volatility**: Based on bar volatility
- **Spread**: Based on bid-ask spread

## Position Sizing

Supported methods:

1. **Fixed Size** - Exact number of shares
2. **Notional** - Dollar amount
3. **Risk %** - Risk percentage of equity
4. **Margin %** - Percentage of available margin
5. **Kelly** - Kelly criterion (advanced)

```python
signal = create_signal(
    timestamp=timestamp,
    symbol="AAPL",
    side=OrderSide.BUY,
    action=OrderAction.ENTRY,
    order_type=OrderType.MARKET,
    size=100,
    size_type=SizeType.SHARES  # or NOTIONAL, RISK_PERCENT, etc.
)
```

## Testing

Run the example strategy:

```bash
python example_strategy.py
```

Expected output:
- Console logs showing trades
- `results/trades.csv` - Trade records
- `results/metrics.json` - Performance metrics
- Summary printed to console

## Deterministic Reproducibility

Same configuration + same data = same results

```python
config = BacktestConfig(
    random_seed=42,  # Fixed seed
    # ... other settings
)
broker = SimBroker(config)
```

## Error Handling

```python
# Signal validation
order_id = broker.submit_signal(signal)
if not order_id:
    print("Signal rejected - check logs")

# Order status
order = broker.get_order(order_id)
if order['status'] == 'PENDING':
    print("Order not filled yet")

# Account checks
snapshot = broker.get_account_snapshot()
if snapshot['equity'] < config.start_cash * 0.8:
    print("Warning: 20% drawdown")
```

## Supported Asset Classes

- **Equities** - Full support
- **Forex** - With spread/pip handling
- **Futures** - With margin/leverage
- **Crypto** - 24/7 trading
- **Options** - Future enhancement

## Roadmap

Future enhancements (non-breaking):
- [ ] Tick-level simulation
- [ ] Order book simulation
- [ ] Portfolio-level allocation
- [ ] HTML report generator
- [ ] Interactive dashboard
- [ ] Multi-currency support
- [ ] Event-driven simulation

## License

MIT License - See LICENSE file

## Contributing

This is a **stable** module. Breaking changes require major version bump.

For new features:
1. Don't modify stable API signatures
2. Add new optional methods only
3. Update API_REFERENCE.md
4. Add tests
5. Update version

## Support

- Documentation: [`API_REFERENCE.md`](API_REFERENCE.md)
- AI Integration: [`SYSTEM_PROMPT.md`](SYSTEM_PROMPT.md)
- Examples: [`example_strategy.py`](example_strategy.py)

---

**Remember:** This is the immutable core. Strategy code should ONLY use the stable API.

**Version:** 1.0.0  
**Last Updated:** 2025-10-16
