# SimBroker Integration Guide for Agents

This document provides integration instructions for coder, tester, and debugger agents working with SimBroker.

---

## For CODER Agent

### Task Pattern

When asked to implement a trading strategy:

1. **Import SimBroker**
   ```python
   from multi_agent.simulator import SimBroker, SimConfig
   ```

2. **Initialize Broker**
   ```python
   config = SimConfig(
       starting_balance=10000.0,
       leverage=100.0,
       slippage={'type': 'fixed', 'value': 2},
       commission={'type': 'per_lot', 'value': 1.5}
   )
   broker = SimBroker(config)
   ```

3. **Strategy Logic Loop**
   ```python
   for idx, row in data.iterrows():
       # Generate signal
       if buy_condition:
           broker.place_order({
               'symbol': 'TEST',
               'volume': 0.1,
               'type': 'ORDER_TYPE_BUY',
               'sl': row['Close'] * 0.98,
               'tp': row['Close'] * 1.04
           })
       
       # Process bar
       events = broker.step_bar(row)
   ```

4. **Generate Report**
   ```python
   report = broker.generate_report()
   return report
   ```

### Order Request Template

```python
order_request = {
    'action': 'TRADE_ACTION_DEAL',
    'symbol': str,              # Required
    'volume': float,            # Required (lots)
    'type': str,                # Required: 'ORDER_TYPE_BUY' or 'ORDER_TYPE_SELL'
    'price': float,             # Optional (None = market)
    'sl': float,                # Optional (stop loss price)
    'tp': float,                # Optional (take profit price)
    'deviation': float,         # Optional (default: 10.0)
    'magic': int,               # Optional (strategy ID)
    'comment': str              # Optional
}
```

---

## For TESTER Agent

### Validation Checklist

When validating a strategy implementation:

1. **Load Strategy and Data**
   ```python
   from strategy_module import run_strategy
   
   report = run_strategy(data_path, config)
   ```

2. **Assert Basic Metrics**
   ```python
   metrics = report['metrics']
   
   # Trades executed
   assert metrics['total_trades'] > 0, "No trades executed"
   
   # Reasonable win rate
   assert 0 <= metrics['win_rate'] <= 1, "Invalid win rate"
   
   # Risk metrics present
   assert 'max_drawdown' in metrics
   assert 'sharpe_ratio' in metrics
   ```

3. **Validate Trade Records**
   ```python
   trades = report['trades']
   
   for trade in trades:
       # All required fields present
       assert 'entry_price' in trade
       assert 'close_price' in trade
       assert 'profit' in trade
       
       # Valid SL/TP if specified
       if trade['side'] == 'buy':
           if trade['sl']:
               assert trade['sl'] < trade['entry_price']
           if trade['tp']:
               assert trade['tp'] > trade['entry_price']
   ```

4. **Check Determinism** (important!)
   ```python
   # Run twice with same seed
   config1 = SimConfig(rng_seed=42)
   report1 = run_strategy(data, config1)
   
   config2 = SimConfig(rng_seed=42)
   report2 = run_strategy(data, config2)
   
   # Results must match
   assert report1['metrics']['total_net_pnl'] == report2['metrics']['total_net_pnl']
   ```

### Test Report Format

```python
test_report = {
    'task_id': str,
    'success': bool,
    'metrics': {
        'total_trades': int,
        'net_pnl': float,
        'win_rate': float,
        'max_drawdown': float
    },
    'validation_results': [
        {'check': str, 'passed': bool, 'message': str}
    ],
    'artifacts': {
        'trades': Path,
        'equity_curve': Path,
        'report': Path
    }
}
```

---

## For DEBUGGER Agent

### Debugging Workflow

When investigating strategy issues:

1. **Enable Debug Mode**
   ```python
   config = SimConfig(debug=True)
   broker = SimBroker(config)
   ```

2. **Analyze Event Log**
   ```python
   events = broker.get_events()
   
   # Filter by type
   order_events = [e for e in events if e.event_type.value == 'order_filled']
   close_events = [e for e in events if e.event_type.value == 'position_closed']
   
   # Check rejection reasons
   rejected = [e for e in events if e.event_type.value == 'order_rejected']
   for event in rejected:
       print(f"Rejection: {event.data}")
   ```

3. **Inspect Intrabar Logic** (SL/TP issues)
   ```python
   intrabar_log = broker.get_intrabar_log()
   
   for entry in intrabar_log:
       print(f"Bar {entry['timestamp']}: {entry['side']} position")
       print(f"  Exit point: {entry['exit_point']}")
       print(f"  Exit reason: {entry['exit_reason']}")
       print(f"  Exit price: {entry['exit_price']}")
       print(f"  Bar OHLC: {entry['bar_ohlc']}")
   ```

4. **Trace Individual Trade**
   ```python
   trades = broker.get_closed_trades()
   
   # Find losing trades
   losers = [t for t in trades if t.net_profit < 0]
   
   for trade in losers:
       print(f"Trade {trade.trade_id}:")
       print(f"  Entry: {trade.entry_price} @ {trade.open_time}")
       print(f"  Exit: {trade.close_price} @ {trade.close_time}")
       print(f"  Reason: {trade.reason_close.value}")
       print(f"  P&L: {trade.net_profit}")
       print(f"  Commission: {trade.total_commission}")
   ```

5. **Diagnose Common Issues**

   **Issue: Too many SL hits**
   ```python
   sl_hits = [t for t in trades if t.reason_close.value == 'sl']
   print(f"SL hit rate: {len(sl_hits) / len(trades):.1%}")
   
   # Check if SL too tight
   avg_sl_distance = sum(
       abs(t.entry_price - t.sl) / t.entry_price 
       for t in trades if t.sl
   ) / len(trades)
   print(f"Avg SL distance: {avg_sl_distance:.1%}")
   ```

   **Issue: Low win rate**
   ```python
   # Check if TP too far
   tp_hits = [t for t in trades if t.reason_close.value == 'tp']
   print(f"TP hit rate: {len(tp_hits) / len(trades):.1%}")
   
   # Compare SL vs TP distances
   avg_sl = sum(abs(t.entry_price - t.sl) for t in trades if t.sl) / len(trades)
   avg_tp = sum(abs(t.tp - t.entry_price) for t in trades if t.tp) / len(trades)
   print(f"Risk:Reward = 1:{avg_tp/avg_sl:.2f}")
   ```

   **Issue: Margin rejections**
   ```python
   margin_events = [e for e in events if 'margin' in str(e.data).lower()]
   print(f"Margin issues: {len(margin_events)}")
   
   # Check max simultaneous positions
   max_positions = max(
       sum(1 for _ in broker.positions) 
       for _ in range(len(data))
   )
   print(f"Max positions: {max_positions}")
   ```

---

## Common Integration Patterns

### Pattern 1: Signal-Based Strategy

```python
def signal_based_strategy(data, broker):
    """Strategy that generates buy/sell signals"""
    
    for idx, row in data.iterrows():
        # Calculate indicators
        signal = generate_signal(data, idx)
        
        # Place order on signal
        if signal == 'BUY' and not broker.positions:
            broker.place_order({
                'symbol': 'TEST',
                'volume': 0.1,
                'type': 'ORDER_TYPE_BUY',
                'sl': calculate_sl(row),
                'tp': calculate_tp(row)
            })
        
        # Process bar
        broker.step_bar(row)
    
    return broker.generate_report()
```

### Pattern 2: Position Management Strategy

```python
def position_management_strategy(data, broker):
    """Strategy with active position management"""
    
    for idx, row in data.iterrows():
        # Process bar first
        events = broker.step_bar(row)
        
        # On position close, check for re-entry
        for event in events:
            if event.event_type.value == 'position_closed':
                if should_reenter(data, idx):
                    broker.place_order(generate_order(row))
    
    return broker.generate_report()
```

### Pattern 3: Multi-Timeframe Strategy

```python
def multi_timeframe_strategy(daily_data, hourly_data, broker):
    """Strategy using multiple timeframes"""
    
    # Get daily trend
    daily_trend = calculate_trend(daily_data)
    
    # Trade on hourly
    for idx, row in hourly_data.iterrows():
        # Only trade in direction of daily trend
        if daily_trend == 'up' and hourly_signal == 'buy':
            broker.place_order({...})
        
        broker.step_bar(row)
    
    return broker.generate_report()
```

---

## Quick Reference

### Essential Methods

```python
# Order management
broker.place_order(order_dict) -> OrderResponse
broker.cancel_order(order_id) -> bool
broker.close_position(position_id, price) -> CloseResult

# Simulation
broker.step_bar(bar_series) -> List[Event]
broker.reset()

# Queries
broker.get_positions() -> List[Position]
broker.get_account() -> AccountSnapshot
broker.get_trades() -> List[Fill]
broker.get_events() -> List[Event]

# Reporting
broker.generate_report() -> Dict
broker.save_report(output_dir) -> Dict[str, Path]
```

### Event Types

```python
EventType.ORDER_ACCEPTED
EventType.ORDER_REJECTED
EventType.ORDER_FILLED
EventType.POSITION_OPENED
EventType.POSITION_CLOSED
EventType.MARGIN_CALL
```

### Close Reasons

```python
CloseReason.TP       # Take profit hit
CloseReason.SL       # Stop loss hit
CloseReason.MANUAL   # Manual close
CloseReason.TIMEOUT  # Time-based exit
CloseReason.MARGIN   # Margin call
```

---

## Tips for Agents

### For Efficient Coding

1. **Use presets** from `configs.yaml` instead of creating SimConfig from scratch
2. **Enable debug mode** during development, disable for final runs
3. **Use fixtures** from `multi_agent/tests/fixtures/` for quick testing
4. **Fixed RNG seed** (42 or 12345) for reproducible development

### For Reliable Testing

1. **Always test with zero-cost config first** to validate strategy logic
2. **Then add realistic costs** to check robustness
3. **Run determinism test** (same seed = same results)
4. **Validate all trade records** have required fields

### For Effective Debugging

1. **Check event log first** for order rejections
2. **Use intrabar log** to understand SL/TP behavior
3. **Compare equity curve** to expected trajectory
4. **Analyze trade distribution** (SL vs TP vs manual closes)

---

## Example Integration Test

```python
def test_agent_integration():
    """Test that agent can use SimBroker correctly"""
    
    # Setup
    from multi_agent.simulator import SimBroker, SimConfig
    import pandas as pd
    
    config = SimConfig(
        starting_balance=10000,
        slippage={'type': 'fixed', 'value': 0},
        commission={'type': 'per_lot', 'value': 0},
        rng_seed=42
    )
    
    broker = SimBroker(config)
    
    # Load test data
    data = pd.read_csv('multi_agent/tests/fixtures/bar_simple_long.csv', 
                       parse_dates=['Date'])
    
    # Simple strategy: buy first bar, hold
    broker.place_order({
        'symbol': 'TEST',
        'volume': 0.1,
        'type': 'ORDER_TYPE_BUY',
        'tp': 103.0
    })
    
    # Process all bars
    for idx, row in data.iterrows():
        events = broker.step_bar(row)
    
    # Generate report
    report = broker.generate_report()
    
    # Validate
    assert report['metrics']['total_trades'] == 1
    assert report['summary']['ending_balance'] > 10000  # Profit
    
    print("✓ Agent integration test passed")

if __name__ == '__main__':
    test_agent_integration()
```

---

## Questions & Answers

**Q: Can I use SimBroker for live trading?**  
A: No, SimBroker is for backtesting only. For paper trading, see v2.0 roadmap.

**Q: Does it support multiple symbols?**  
A: Yes, use different `symbol` strings. Positions tracked independently.

**Q: Can I implement custom slippage models?**  
A: Yes, extend `_compute_entry_slippage()` in `simbroker.py`.

**Q: How do I handle spread?**  
A: Use slippage to simulate spread: `slippage = spread / 2`.

**Q: Can I test on tick data?**  
A: Tick mode is not yet implemented (v1.1 feature). Use bar data for now.

---

## Support

For questions or issues:
1. Check `README.md` in `multi_agent/simulator/`
2. Review unit tests in `test_simbroker.py`
3. Run example: `python Trade/Backtest/codes/ai_strategy_rsi.py`
4. Open GitHub issue with minimal reproducible example
