# SimBroker Implementation Checklist

This checklist ensures the coder agent implements SimBroker correctly in new strategies.

---

## ✅ Pre-Implementation

- [ ] Review `README.md` for API documentation
- [ ] Check `INTEGRATION_GUIDE.md` for patterns
- [ ] Verify test fixtures exist in `multi_agent/tests/fixtures/`
- [ ] Ensure dependencies installed: `pandas`, `numpy`, `pytest`

---

## ✅ Strategy Implementation

### 1. Module Structure

```python
# strategy_name.py

import pandas as pd
import numpy as np
from pathlib import Path
from multi_agent.simulator import SimBroker, SimConfig

def calculate_indicators(data):
    """Calculate technical indicators"""
    pass

class StrategyName:
    """Strategy class with signal generation logic"""
    pass

def run_backtest(data_path, output_dir, config=None):
    """Main backtest runner"""
    pass

def main():
    """Entry point"""
    pass

if __name__ == '__main__':
    main()
```

### 2. Configuration

- [ ] Create SimConfig with appropriate settings
- [ ] Use preset from `configs.yaml` if applicable
- [ ] Set `rng_seed` for deterministic results
- [ ] Enable `debug=False` for production runs

```python
config = SimConfig(
    starting_balance=10000.0,
    leverage=100.0,
    slippage={'type': 'fixed', 'value': 2},
    commission={'type': 'per_lot', 'value': 1.5},
    rng_seed=42,
    debug=False
)
```

### 3. Broker Initialization

- [ ] Initialize broker with config
- [ ] Verify no errors during initialization

```python
broker = SimBroker(config)
```

### 4. Data Loading

- [ ] Load OHLCV data with datetime index
- [ ] Ensure columns: `Date`, `Open`, `High`, `Low`, `Close`
- [ ] Validate no missing values in price data
- [ ] Sort by date ascending

```python
data = pd.read_csv(data_path, parse_dates=['Date'])
data = data.sort_values('Date').reset_index(drop=True)
```

### 5. Signal Generation

- [ ] Implement indicator calculations
- [ ] Generate buy/sell signals
- [ ] Calculate SL/TP levels
- [ ] Validate signal logic with unit tests

```python
def generate_signal(data, idx):
    if buy_condition:
        return {
            'type': 'ORDER_TYPE_BUY',
            'sl': calculate_sl(data, idx),
            'tp': calculate_tp(data, idx)
        }
    return None
```

### 6. Order Placement

- [ ] Use MT5-compatible order format
- [ ] Include all required fields: `symbol`, `volume`, `type`
- [ ] Add optional fields: `sl`, `tp`, `magic`, `comment`
- [ ] Check `OrderResponse.success` before assuming order placed

```python
order_request = {
    'action': 'TRADE_ACTION_DEAL',
    'symbol': 'STRATEGY_SYMBOL',
    'volume': 0.1,
    'type': signal['type'],
    'sl': signal['sl'],
    'tp': signal['tp'],
    'magic': 12345,
    'comment': f"Strategy signal at {idx}"
}

response = broker.place_order(order_request)
if response.success:
    # Order accepted
else:
    # Handle rejection
    print(f"Order rejected: {response.message}")
```

### 7. Bar Processing Loop

- [ ] Iterate through all bars
- [ ] Call `broker.step_bar(row)` for each bar
- [ ] Handle events returned from `step_bar()`
- [ ] Track position state if needed

```python
for idx, row in data.iterrows():
    # Generate signal
    signal = generate_signal(data, idx)
    
    if signal:
        broker.place_order({...})
    
    # Process bar
    events = broker.step_bar(row)
    
    # Handle events
    for event in events:
        if event.event_type.value == 'position_closed':
            # React to position closure
            pass
```

### 8. Report Generation

- [ ] Call `broker.generate_report()`
- [ ] Extract metrics for analysis
- [ ] Save artifacts to output directory
- [ ] Print summary statistics

```python
report = broker.generate_report()

# Save artifacts
artifact_paths = broker.save_report(output_dir)

# Print summary
metrics = report['metrics']
print(f"Total Trades: {metrics['total_trades']}")
print(f"Win Rate: {metrics['win_rate']:.1%}")
print(f"Net P&L: ${metrics['total_net_pnl']:.2f}")
```

---

## ✅ Testing

### Unit Tests

- [ ] Test signal generation logic
- [ ] Test indicator calculations
- [ ] Test SL/TP calculation functions
- [ ] Test with zero-cost config first

```python
def test_signal_generation():
    data = load_test_fixture()
    signal = generate_signal(data, idx=50)
    
    assert signal is not None
    assert 'type' in signal
    assert 'sl' in signal
    assert 'tp' in signal
```

### Integration Tests

- [ ] Test complete backtest runs
- [ ] Test with different configurations
- [ ] Test determinism (same seed = same results)
- [ ] Test edge cases (no signals, all losses, etc.)

```python
def test_complete_backtest():
    report = run_backtest(fixture_path, output_dir)
    
    assert report['metrics']['total_trades'] > 0
    assert 'equity_curve' in report
    assert len(report['trades']) == report['metrics']['total_trades']
```

### Validation Tests

- [ ] All trades have valid entry/exit prices
- [ ] SL below entry for longs (above for shorts)
- [ ] TP above entry for longs (below for shorts)
- [ ] No negative volumes
- [ ] Balance increases with profits, decreases with losses

```python
def test_trade_validity():
    trades = broker.get_closed_trades()
    
    for trade in trades:
        assert trade.entry_price > 0
        assert trade.volume > 0
        
        if trade.side == OrderSide.BUY:
            if trade.sl:
                assert trade.sl < trade.entry_price
            if trade.tp:
                assert trade.tp > trade.entry_price
```

---

## ✅ Documentation

- [ ] Docstrings for all public functions
- [ ] Strategy description at module level
- [ ] Parameter explanations
- [ ] Usage examples in comments
- [ ] Expected input/output formats

```python
"""
Strategy: RSI Mean Reversion

Description:
    Buys when RSI < 30 (oversold)
    Sells when RSI > 70 (overbought)
    Uses fixed stop loss and take profit

Parameters:
    rsi_period: int - RSI calculation period (default: 14)
    rsi_oversold: float - Oversold threshold (default: 30)
    rsi_overbought: float - Overbought threshold (default: 70)
    sl_pct: float - Stop loss percentage (default: 2.0)
    tp_pct: float - Take profit percentage (default: 4.0)

Usage:
    python ai_strategy_rsi.py

Expected Input:
    CSV file with columns: Date, Open, High, Low, Close, Volume

Output:
    test_report.json - Full backtest report
    trades.csv - Trade records
    equity_curve.csv - Equity over time
"""
```

---

## ✅ Error Handling

- [ ] Handle missing data files gracefully
- [ ] Catch and report broker errors
- [ ] Validate input parameters
- [ ] Provide helpful error messages

```python
try:
    data = pd.read_csv(data_path)
except FileNotFoundError:
    print(f"Error: Data file not found at {data_path}")
    return None

if data.empty:
    raise ValueError("Data file is empty")

if 'Close' not in data.columns:
    raise ValueError("Data must contain 'Close' column")
```

---

## ✅ Performance Optimization

- [ ] Disable debug mode for production
- [ ] Use vectorized operations for indicators
- [ ] Avoid unnecessary copies of dataframes
- [ ] Pre-calculate indicators before loop
- [ ] Use zero-cost config for strategy logic testing

```python
# Pre-calculate all indicators
data['RSI'] = calculate_rsi(data['Close'])
data['MA'] = data['Close'].rolling(20).mean()

# Then loop through
for idx in range(lookback, len(data)):
    # Access pre-calculated indicators
    signal = check_conditions(data.iloc[idx])
```

---

## ✅ Final Verification

### Before Submission

- [ ] All tests pass: `pytest test_strategy.py -v`
- [ ] Strategy runs without errors on fixtures
- [ ] Report generates correctly
- [ ] Artifacts saved to output directory
- [ ] Code follows style guidelines (PEP 8)
- [ ] No hardcoded paths (use `Path()` and relative paths)
- [ ] Configuration parameters documented
- [ ] README or comments explain strategy logic

### Checklist Summary

```bash
# Run from AlgoAgent/ directory

# 1. Run unit tests
pytest multi_agent/tests/test_simbroker.py -v

# 2. Run strategy
python Trade/Backtest/codes/your_strategy.py

# 3. Check outputs
ls backtest_results/your_strategy/
# Should see: trades.csv, equity_curve.csv, test_report.json

# 4. Validate report
python -c "import json; print(json.load(open('backtest_results/your_strategy/test_report.json'))['metrics'])"
```

### Success Criteria

✅ **Strategy Implementation**
- Code runs without errors
- At least 1 trade executed
- Report generates with all metrics
- Artifacts saved successfully

✅ **Quality Assurance**
- All tests pass
- Win rate between 0-100%
- Max drawdown calculated
- Sharpe ratio present

✅ **Documentation**
- Strategy logic explained
- Parameters documented
- Usage instructions clear

---

## Common Pitfalls to Avoid

❌ **Don't** place orders without calling `step_bar()`
```python
# WRONG
broker.place_order(order)
# position not filled yet!
```

✅ **Do** call `step_bar()` after placing orders
```python
# CORRECT
broker.place_order(order)
broker.step_bar(next_bar)  # Now position opens
```

---

❌ **Don't** assume all orders are accepted
```python
# WRONG
response = broker.place_order(order)
position_id = list(broker.positions.keys())[0]  # May fail if rejected!
```

✅ **Do** check response status
```python
# CORRECT
response = broker.place_order(order)
if response.success:
    # Order accepted, will fill on next step_bar()
else:
    print(f"Order rejected: {response.message}")
```

---

❌ **Don't** modify SL/TP after position opened
```python
# NOT YET SUPPORTED
position.fill.sl = new_sl  # Won't work
```

✅ **Do** close and re-open with new levels (or wait for v1.1)
```python
# WORKAROUND
broker.close_position(position_id, current_price)
broker.place_order(order_with_new_sl_tp)
```

---

❌ **Don't** forget to check margin before large positions
```python
# WRONG
broker.place_order({'volume': 10.0, ...})  # May be rejected
```

✅ **Do** check available margin first
```python
# CORRECT
account = broker.get_account()
required = broker._calculate_required_margin(volume, price)

if required <= account.free_margin:
    broker.place_order({...})
else:
    print("Insufficient margin")
```

---

## Quick Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| `len(positions) == 0` | Order not filled yet | Call `step_bar()` after `place_order()` |
| Order rejected | Insufficient margin | Reduce `volume` or increase `starting_balance` |
| No trades executed | Signal logic never triggers | Add debug prints in signal generation |
| Win rate = 0% | SL too tight | Increase `sl_pct` |
| TP never hit | TP too far | Decrease `tp_pct` |
| Different results each run | Random slippage | Set fixed `rng_seed` |
| Position closes unexpectedly | SL/TP hit intrabar | Check `broker.get_intrabar_log()` |

---

## Ready to Ship?

- [ ] All checkboxes above completed ✅
- [ ] Strategy tested on fixtures ✅
- [ ] Report validates correctly ✅
- [ ] Documentation complete ✅
- [ ] Code reviewed for quality ✅

**If yes → Hand off to Tester Agent for validation!**

---

*Last Updated: November 6, 2025*  
*Version: 1.0.0*
