# SimBroker - Portable Trading Simulator

**Version 1.0.0**

A portable, deterministic, testable trading simulator for backtesting strategies with MT5-compatible order interface.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Deterministic Intrabar Resolution](#deterministic-intrabar-resolution)
- [Slippage & Commission Models](#slippage--commission-models)
- [Testing](#testing)
- [Integration with Agents](#integration-with-agents)
- [Examples](#examples)
- [Performance Considerations](#performance-considerations)

---

## Overview

SimBroker is a **self-contained, deterministic backtesting engine** designed for:

- **Strategy Development**: Test trading strategies without live market connection
- **Agent-Based Systems**: Provides tool interface for AI coder/tester agents
- **Reproducible Testing**: Fixed random seeds ensure identical results across runs
- **MT5 Compatibility**: Accepts MetaTrader 5 order request format

### Goals

1. Accept MT5-like order requests from strategies
2. Simulate realistic fills with configurable slippage and commissions
3. Track open positions with SL/TP management
4. Produce structured trade records and equity curves
5. Be independent, deterministic, and fully testable

---

## Key Features

### ✅ Implemented

- **MT5-Compatible Order Interface** - Send orders using familiar MT5 request format
- **Deterministic Bar-Based Execution** - Reproducible fills and SL/TP resolution
- **Configurable Slippage Models** - Fixed, random, or percentage-based
- **Flexible Commission Models** - Per-lot, percentage, or flat fee
- **Intrabar SL/TP Resolution** - Documented sequence logic (Open→High→Low→Close)
- **Margin Management** - Leverage, margin calls, and stop-outs
- **Position Tracking** - Multiple simultaneous positions
- **Comprehensive Metrics** - Win rate, Sharpe ratio, max drawdown, etc.
- **Event System** - Track order fills, position closures, margin calls
- **Artifact Export** - CSV/JSON reports for CI/CD integration

### 🚧 Future Enhancements

- Tick-by-tick simulation mode
- Partial fills
- Advanced order types (limit, stop-limit, trailing stops)
- Multi-symbol portfolio simulation
- Spread modeling

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Trading Strategy                     │
│             (Generates MT5 Order Requests)               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │      SimBroker API         │
        │   place_order()            │
        │   step_bar()               │
        │   get_positions()          │
        │   generate_report()        │
        └────────────┬───────────────┘
                     │
         ┌───────────┴───────────┐
         │   Order Engine         │
         │   - Order validation   │
         │   - Order matching     │
         │   - Fill execution     │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │  Position Manager      │
         │  - SL/TP monitoring    │
         │  - Intrabar resolution │
         │  - Position tracking   │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │  Risk & Accounting     │
         │  - Slippage calc       │
         │  - Commission calc     │
         │  - Margin calc         │
         │  - P&L tracking        │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │    Event Logger        │
         │    Reporter            │
         └───────────────────────┘
                     │
                     ▼
     ┌────────────────────────────────┐
     │  Artifacts                     │
     │  - trades.csv                  │
     │  - equity_curve.csv            │
     │  - test_report.json            │
     └────────────────────────────────┘
```

---

## Installation

### Requirements

- Python 3.8+
- pandas
- numpy (for strategy indicators)
- pytest (for testing)
- pyyaml (for config loading)

### Install

```bash
# From AlgoAgent root directory
cd AlgoAgent

# Install dependencies
pip install pandas numpy pytest pyyaml

# Verify installation
python -m pytest multi_agent/tests/test_simbroker.py -v
```

### Module Location

```
AlgoAgent/
├── multi_agent/
│   ├── simulator/
│   │   ├── __init__.py
│   │   ├── simbroker.py      # Main module
│   │   └── configs.yaml       # Configuration presets
│   └── tests/
│       ├── test_simbroker.py  # Unit tests
│       └── fixtures/          # Test data
```

---

## Quick Start

### Basic Usage

```python
from multi_agent.simulator import SimBroker, SimConfig
import pandas as pd

# 1. Configure broker
config = SimConfig(
    starting_balance=10000.0,
    leverage=100.0,
    slippage={'type': 'fixed', 'value': 2},
    commission={'type': 'per_lot', 'value': 1.5}
)

broker = SimBroker(config)

# 2. Place order (MT5 format)
order_request = {
    'action': 'TRADE_ACTION_DEAL',
    'symbol': 'EURUSD',
    'volume': 0.1,
    'type': 'ORDER_TYPE_BUY',
    'sl': 1.0950,
    'tp': 1.1050
}

response = broker.place_order(order_request)
print(f"Order {response.order_id}: {response.status}")

# 3. Feed price bars
bar = pd.Series({
    'Date': pd.Timestamp('2024-01-01'),
    'Open': 1.1000,
    'High': 1.1020,
    'Low': 1.0980,
    'Close': 1.1010
})

events = broker.step_bar(bar)

# 4. Generate report
report = broker.generate_report()
print(f"Total P&L: ${report['metrics']['total_net_pnl']:.2f}")
print(f"Win Rate: {report['metrics']['win_rate']:.1%}")
```

### Complete Example

See [`Trade/Backtest/codes/ai_strategy_rsi.py`](../../Trade/Backtest/codes/ai_strategy_rsi.py) for a complete RSI strategy implementation.

---

## API Reference

### SimBroker Class

#### Initialization

```python
broker = SimBroker(config: SimConfig)
```

Creates a new broker instance with specified configuration.

**Raises:** `ValueError` if configuration is invalid

---

#### Order Management

##### `place_order(order_request: Dict) -> OrderResponse`

Place a new market order.

**Parameters:**

```python
order_request = {
    'action': 'TRADE_ACTION_DEAL',       # Order action (only DEAL supported)
    'symbol': str,                        # Trading symbol
    'volume': float,                      # Position size in lots
    'type': str,                          # 'ORDER_TYPE_BUY' or 'ORDER_TYPE_SELL'
    'price': float (optional),            # Limit price (None = market)
    'sl': float (optional),               # Stop loss price
    'tp': float (optional),               # Take profit price
    'deviation': float (optional),        # Max slippage points
    'magic': int (optional),              # Magic number
    'comment': str (optional),            # Order comment
    'type_time': str (optional),          # Time in force
    'type_filling': str (optional)        # Fill policy
}
```

**Returns:** `OrderResponse` with `order_id`, `status`, `message`

**Example:**

```python
response = broker.place_order({
    'symbol': 'AAPL',
    'volume': 0.5,
    'type': 'ORDER_TYPE_BUY',
    'sl': 149.0,
    'tp': 155.0
})

if response.success:
    print(f"Order placed: {response.order_id}")
else:
    print(f"Order rejected: {response.message}")
```

---

##### `cancel_order(order_id: str) -> bool`

Cancel a pending order.

**Returns:** `True` if cancelled, `False` if not found or already filled

---

##### `close_position(position_id: str, price: float = None) -> CloseResult`

Manually close an open position.

**Parameters:**
- `position_id`: Position ID (trade_id)
- `price`: Close price (required for manual close)

**Returns:** `CloseResult` with `success`, `profit`, `message`

---

#### Simulation Stepping

##### `step_bar(bar: pd.Series) -> List[Event]`

Process one OHLCV bar through the simulation.

**Parameters:**

```python
bar = pd.Series({
    'Date': pd.Timestamp,  # Bar timestamp
    'Open': float,         # Opening price
    'High': float,         # High price
    'Low': float,          # Low price
    'Close': float,        # Closing price
    'Volume': float        # Volume (optional)
})
```

**Returns:** List of `Event` objects (fills, closures, margin calls)

**Execution Sequence:**
1. Fill pending orders at bar Open
2. Check SL/TP for open positions (intrabar logic)
3. Check margin levels
4. Record equity point

**Example:**

```python
for idx, row in data.iterrows():
    events = broker.step_bar(row)
    
    for event in events:
        if event.event_type == EventType.POSITION_CLOSED:
            print(f"Position closed: {event.data['reason']}")
```

---

##### `step_tick(tick: Dict) -> List[Event]`

Process one tick (future feature - not yet implemented).

---

#### Query Methods

##### `get_positions() -> List[Position]`

Get all open positions.

---

##### `get_account() -> AccountSnapshot`

Get current account state.

**Returns:**

```python
AccountSnapshot(
    balance=float,
    equity=float,
    floating_pnl=float,
    used_margin=float,
    free_margin=float,
    margin_level=float,
    total_positions=int,
    total_orders=int
)
```

---

##### `get_trades() -> List[Fill]`

Get all trade records (both open and closed).

---

##### `get_closed_trades() -> List[Fill]`

Get only closed trade records.

---

##### `get_events() -> List[Event]`

Get event log.

---

#### Reporting

##### `generate_report() -> Dict`

Generate comprehensive backtest report.

**Returns:**

```python
{
    'metrics': {
        'total_trades': int,
        'winning_trades': int,
        'losing_trades': int,
        'win_rate': float,
        'avg_profit': float,
        'avg_loss': float,
        'expectancy': float,
        'total_gross_pnl': float,
        'total_commissions': float,
        'total_net_pnl': float,
        'return_pct': float,
        'max_drawdown': float,
        'max_drawdown_pct': float,
        'sharpe_ratio': float,
        'profit_factor': float
    },
    'trades': List[Dict],
    'equity_curve': List[Dict],
    'config': Dict,
    'summary': Dict
}
```

---

##### `save_report(output_dir: Path) -> Dict[str, Path]`

Save report artifacts to files.

**Returns:** Dictionary mapping artifact names to file paths

**Files Created:**
- `trades.csv` - All trade records
- `equity_curve.csv` - Equity curve data points
- `test_report.json` - Full report JSON

---

#### Utilities

##### `reset() -> None`

Reset broker state to initial conditions. Useful for running multiple test scenarios.

---

## Configuration

### SimConfig Parameters

```python
config = SimConfig(
    starting_balance=10000.0,      # Initial account balance
    leverage=100.0,                 # Trading leverage (100:1)
    lot_size=100000.0,             # Units per lot (standard forex lot)
    point=0.0001,                  # Minimum price increment (pip)
    slippage={},                   # Slippage model (see below)
    commission={},                 # Commission model (see below)
    margin_call_level=50.0,        # Margin call threshold (%)
    stop_out_level=20.0,           # Stop-out level (%)
    allow_hedging=False,           # Allow opposing positions
    rng_seed=12345,                # Random seed for determinism
    debug=False                    # Enable debug logging
)
```

### Configuration Presets

Load from `configs.yaml`:

```python
import yaml
from pathlib import Path

with open('multi_agent/simulator/configs.yaml') as f:
    configs = yaml.safe_load(f)

# Use preset
config_dict = configs['conservative']
config = SimConfig(**config_dict)
```

**Available Presets:**
- `default` - Balanced settings
- `conservative` - Higher costs, lower leverage
- `aggressive` - Lower costs, higher leverage
- `zero_cost` - No slippage/commission (ideal testing)
- `random_slippage` - Variable execution quality
- `percent_costs` - Scales with trade size
- `debug` - Verbose logging
- `stocks` - Stock market settings
- `crypto` - Cryptocurrency settings
- `testing` - Deterministic for unit tests

---

## Deterministic Intrabar Resolution

SimBroker uses **documented intrabar price sequences** to ensure deterministic SL/TP resolution.

### Problem

Given OHLC bar, we don't know the exact order prices were hit. Did High come before Low?

### Solution

**Fixed sequence assumptions:**

#### Long Positions
```
Open → High → Low → Close
```

**Example:**
- Entry: 100.0
- SL: 95.0
- TP: 105.0
- Bar: O=100, H=105, L=95, C=102

**Sequence Check:**
1. Open (100) - Position enters
2. High (105) - **TP hit** ✓
3. Low (95) - SL not checked (already exited)
4. Close (102) - N/A

**Result:** Position closes at TP = 105.0

---

#### Short Positions
```
Open → Low → High → Close
```

**Example:**
- Entry: 100.0
- SL: 105.0
- TP: 95.0
- Bar: O=100, H=105, L=95, C=102

**Sequence Check:**
1. Open (100) - Position enters
2. Low (95) - **TP hit** ✓
3. High (105) - SL not checked (already exited)
4. Close (102) - N/A

**Result:** Position closes at TP = 95.0

---

### Why This Matters

✅ **Deterministic** - Same bar data always produces same result  
✅ **Reproducible** - Critical for CI/CD testing  
✅ **Documented** - Clear rules for validation  
✅ **Conservative** - Tends toward realistic worst-case

⚠️ **Limitation:** Not tick-perfect (use tick data for higher precision)

---

## Slippage & Commission Models

### Slippage Models

Slippage simulates execution degradation (always adverse to trader).

#### 1. Fixed Slippage

```python
slippage = {'type': 'fixed', 'value': 2}  # 2 points
```

- Buy orders: `fill_price = market_price + (points * point_size)`
- Sell orders: `fill_price = market_price - (points * point_size)`

**Use case:** Stable instruments, predictable execution

---

#### 2. Random Slippage

```python
slippage = {'type': 'random', 'value': 5}  # Max 5 points
```

- Uniformly random between 0 and max points
- Always adverse (never improves fill)

**Use case:** Volatile markets, variable liquidity

---

#### 3. Percent Slippage

```python
slippage = {'type': 'percent', 'value': 0.05}  # 0.05%
```

- Scales with price
- `slippage = market_price * (pct / 100)`

**Use case:** Percentage-based spread markets

---

### Commission Models

Commission is applied on both entry and exit.

#### 1. Per-Lot Commission

```python
commission = {'type': 'per_lot', 'value': 1.5}  # $1.50 per lot
```

- `commission = volume * rate`

**Use case:** Forex, futures

---

#### 2. Percent Commission

```python
commission = {'type': 'percent', 'value': 0.1}  # 0.1%
```

- `notional = volume * lot_size * price`
- `commission = notional * (pct / 100)`

**Use case:** Stocks, crypto exchanges

---

#### 3. Flat Commission

```python
commission = {'type': 'flat', 'value': 5.0}  # $5 per trade
```

**Use case:** Fixed-fee brokers

---

## Testing

### Run Unit Tests

```bash
# All tests
pytest multi_agent/tests/test_simbroker.py -v

# Specific test
pytest multi_agent/tests/test_simbroker.py::test_simple_entry_at_next_open -v

# With coverage
pytest multi_agent/tests/test_simbroker.py --cov=multi_agent.simulator --cov-report=html
```

### Test Categories

✅ **Order Management** (5 tests)
- Valid order acceptance
- Missing field rejection
- Invalid volume rejection
- Buy/sell side detection

✅ **Position Execution** (3 tests)
- Entry at next bar open
- Entry with commission
- Commission recording

✅ **SL/TP Resolution** (3 tests)
- TP hit before SL (long)
- SL hit before TP (long)
- Both hit same bar (sequence logic)
- Short position intrabar logic

✅ **Cost Models** (4 tests)
- Fixed slippage
- Random slippage
- Per-lot commission
- Percent commission

✅ **Account Management** (2 tests)
- Balance updates on close
- Equity curve recording

✅ **Multiple Positions** (2 tests)
- Simultaneous positions
- Partial position close

✅ **Margin** (2 tests)
- Order rejection on insufficient margin
- Margin level calculation

✅ **Integration** (5 tests)
- Full backtest workflow
- Manual position close
- Order cancellation
- Reset state
- Report generation

✅ **Edge Cases** (4 tests)
- Invalid config
- Close non-existent position
- Cancel non-existent order
- Step bar with no positions

**Total: 30+ tests covering all critical paths**

---

## Integration with Agents

SimBroker is designed to be a **tool interface** for AI agents (coder, tester, debugger).

### For Coder Agent

**Task:** Implement trading strategy

**SimBroker provides:**
- Clear order interface (MT5 format)
- Predictable execution rules
- Immediate feedback via events

**Example Task:**

```
"Implement a moving average crossover strategy that:
1. Buys when MA(10) crosses above MA(50)
2. Sells when MA(10) crosses below MA(50)
3. Uses 2% stop loss and 4% take profit
4. Position size: 0.1 lots

Use SimBroker to backtest on bar_extended.csv fixture."
```

**Coder Agent Response:**

```python
from multi_agent.simulator import SimBroker, SimConfig

def ma_crossover_strategy(data):
    broker = SimBroker(SimConfig())
    
    # Calculate MAs
    data['MA10'] = data['Close'].rolling(10).mean()
    data['MA50'] = data['Close'].rolling(50).mean()
    
    for idx in range(50, len(data)):
        row = data.iloc[idx]
        
        # Buy signal
        if data.iloc[idx-1]['MA10'] <= data.iloc[idx-1]['MA50'] and \
           row['MA10'] > row['MA50']:
            broker.place_order({
                'symbol': 'TEST',
                'volume': 0.1,
                'type': 'ORDER_TYPE_BUY',
                'sl': row['Close'] * 0.98,
                'tp': row['Close'] * 1.04
            })
        
        broker.step_bar(row)
    
    return broker.generate_report()
```

---

### For Tester Agent

**Task:** Validate strategy implementation

**SimBroker provides:**
- Deterministic results (fixed RNG seed)
- Detailed event log
- Structured reports for assertions

**Example Task:**

```
"Test that the RSI strategy in ai_strategy_rsi.py:
1. Opens at least 1 position
2. Has win rate > 40%
3. Max drawdown < 20%
4. All positions have valid SL/TP"
```

**Tester Agent Response:**

```python
def test_rsi_strategy_meets_criteria():
    from ai_strategy_rsi import run_rsi_backtest
    
    report = run_rsi_backtest(data_path, output_dir, config)
    
    metrics = report['metrics']
    trades = report['trades']
    
    # Assert criteria
    assert metrics['total_trades'] >= 1, "No trades executed"
    assert metrics['win_rate'] > 0.4, f"Win rate {metrics['win_rate']} < 40%"
    assert metrics['max_drawdown_pct'] < 20, f"Drawdown {metrics['max_drawdown_pct']}% >= 20%"
    
    # Validate all trades have SL/TP
    for trade in trades:
        assert trade['sl'] is not None, f"Trade {trade['trade_id']} missing SL"
        assert trade['tp'] is not None, f"Trade {trade['trade_id']} missing TP"
```

---

### For Debugger Agent

**Task:** Diagnose why strategy underperforms

**SimBroker provides:**
- Event log (order flow)
- Intrabar log (SL/TP hit details)
- Trade-by-trade P&L breakdown

**Example Task:**

```
"Debug why the RSI strategy has 30% win rate (expected 50%+).
Analyze if SL is too tight or TP is too far."
```

**Debugger Agent Response:**

```python
def analyze_sl_tp_ratio(broker):
    trades = broker.get_closed_trades()
    
    sl_hits = [t for t in trades if t.reason_close == CloseReason.SL]
    tp_hits = [t for t in trades if t.reason_close == CloseReason.TP]
    
    print(f"SL hits: {len(sl_hits)} ({len(sl_hits)/len(trades):.1%})")
    print(f"TP hits: {len(tp_hits)} ({len(tp_hits)/len(trades):.1%})")
    
    # Analyze intrabar log for premature SL hits
    intrabar_log = broker.get_intrabar_log()
    
    for entry in intrabar_log:
        if entry['exit_reason'] == 'sl':
            print(f"SL hit at {entry['exit_point']} on bar {entry['bar_ohlc']}")
            # Check if High was very close to entry (tight SL)
```

---

## Examples

### Example 1: Simple Buy and Hold

```python
from multi_agent.simulator import SimBroker, SimConfig
import pandas as pd

config = SimConfig(
    slippage={'type': 'fixed', 'value': 0},
    commission={'type': 'per_lot', 'value': 0}
)

broker = SimBroker(config)

# Buy at start
broker.place_order({
    'symbol': 'TEST',
    'volume': 1.0,
    'type': 'ORDER_TYPE_BUY'
})

# Load data
data = pd.read_csv('fixtures/bar_extended.csv', parse_dates=['Date'])

# Process all bars
for idx, row in data.iterrows():
    broker.step_bar(row)

# Close at end
position_id = list(broker.positions.keys())[0]
broker.close_position(position_id, price=data.iloc[-1]['Close'])

# Report
report = broker.generate_report()
print(f"Buy & Hold Return: {report['summary']['return_pct']:.2f}%")
```

---

### Example 2: Daily Rebalancing

```python
# Rebalance position daily
target_size = 0.5  # lots

for idx, row in data.iterrows():
    broker.step_bar(row)
    
    current_size = sum(p.fill.volume for p in broker.get_positions())
    
    if current_size < target_size:
        # Add to position
        broker.place_order({
            'symbol': 'TEST',
            'volume': target_size - current_size,
            'type': 'ORDER_TYPE_BUY'
        })
```

---

### Example 3: Parameter Sweep

```python
# Test different SL/TP ratios
results = []

for sl_pct in [1.0, 2.0, 3.0]:
    for tp_pct in [2.0, 4.0, 6.0]:
        broker = SimBroker(SimConfig(rng_seed=42))
        
        # Run strategy with parameters
        run_strategy(broker, data, sl_pct, tp_pct)
        
        report = broker.generate_report()
        results.append({
            'sl_pct': sl_pct,
            'tp_pct': tp_pct,
            'sharpe': report['metrics']['sharpe_ratio'],
            'return': report['summary']['return_pct']
        })

# Find best parameters
best = max(results, key=lambda x: x['sharpe'])
print(f"Best: SL={best['sl_pct']}%, TP={best['tp_pct']}%, Sharpe={best['sharpe']:.2f}")
```

---

## Performance Considerations

### Optimization Tips

1. **Use Zero-Cost Config for Strategy Logic Testing**
   ```python
   config = SimConfig(
       slippage={'type': 'fixed', 'value': 0},
       commission={'type': 'per_lot', 'value': 0}
   )
   ```

2. **Batch Process Bars** (if you have many backtests)
   ```python
   # Process multiple strategies in parallel
   from multiprocessing import Pool
   
   def run_backtest(strategy_params):
       broker = SimBroker(SimConfig(rng_seed=42))
       # ...
       return broker.generate_report()
   
   with Pool(8) as p:
       results = p.map(run_backtest, strategy_list)
   ```

3. **Use `debug=False` in Production**
   - Debug mode prints every order/fill
   - Disable for faster execution

4. **Limit Equity Curve Points**
   - Each bar adds equity point
   - For multi-year backtests, consider downsampling

### Scalability

- **Small Backtests** (< 1000 bars): Instant
- **Medium Backtests** (1K-10K bars): Seconds
- **Large Backtests** (10K-100K bars): Minutes
- **Massive Backtests** (> 100K bars): Consider vectorized approach or Cython

---

## Troubleshooting

### Common Issues

#### 1. Order Rejected: Insufficient Margin

**Symptom:** `OrderResponse.status = REJECTED`, message contains "margin"

**Solution:**
- Reduce position size
- Increase starting balance
- Increase leverage (cautiously)

```python
config = SimConfig(
    starting_balance=50000,  # Increase capital
    leverage=200             # Or increase leverage
)
```

---

#### 2. No Positions Opened

**Symptom:** `len(broker.get_positions()) == 0` after placing orders

**Cause:** Orders not filled yet (need to call `step_bar()`)

**Solution:**
```python
# Place order
broker.place_order(order_request)

# Orders fill on next step_bar() call
broker.step_bar(next_bar)  # NOW position opens
```

---

#### 3. Unexpected SL/TP Behavior

**Symptom:** Position closes at "wrong" price

**Cause:** Intrabar sequence logic

**Debug:**
```python
config = SimConfig(debug=True)
broker = SimBroker(config)

# ... run backtest ...

# Check intrabar log
log = broker.get_intrabar_log()
for entry in log:
    print(entry)
```

---

#### 4. Different Results on Each Run

**Symptom:** Random slippage produces varying P&L

**Solution:** Use fixed seed for reproducibility
```python
config = SimConfig(
    rng_seed=42,  # Fixed seed
    slippage={'type': 'random', 'value': 5}
)
```

---

## Contributing

### Code Style

- Follow PEP 8
- Type hints for public methods
- Docstrings for all public APIs

### Adding Tests

1. Add fixture data to `fixtures/`
2. Write test in `test_simbroker.py`
3. Run: `pytest multi_agent/tests/test_simbroker.py::test_new_feature -v`

### Extending Slippage/Commission Models

```python
# In simbroker.py, extend _compute_entry_slippage()

def _compute_entry_slippage(self, order, market_price):
    slip_type = self.cfg.slippage.get('type')
    
    if slip_type == 'custom_model':
        # Your custom logic
        return custom_slippage_calc(order, market_price)
    
    # ... existing models ...
```

---

## Roadmap

### v1.1 (Q1 2025)
- ✅ Tick-mode simulation
- ✅ Partial fills
- ✅ Limit orders

### v1.2 (Q2 2025)
- ✅ Multi-symbol portfolio
- ✅ Spread modeling
- ✅ Trailing stops

### v2.0 (Q3 2025)
- ✅ Vectorized bar processing
- ✅ Cython optimization
- ✅ Real-time mode (paper trading)

---

## License

MIT License - See LICENSE file

---

## Contact & Support

- **Issues:** [GitHub Issues](https://github.com/Chiqo-ke/AlgoAgent/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Chiqo-ke/AlgoAgent/discussions)
- **Email:** support@algoagent.com

---

## Acknowledgments

Designed for the AlgoAgent multi-agent trading system.

Special thanks to:
- MT5 API design inspiration
- Community feedback on deterministic backtesting
- Open-source backtesting frameworks (backtrader, zipline)

---

**📖 Last Updated:** November 6, 2025  
**🏷️ Version:** 1.0.0  
**👨‍💻 Maintainer:** AlgoAgent Team
