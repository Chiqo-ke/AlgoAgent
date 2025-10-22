# Quick Reference - Pattern & Signal Logging

## Quick Start

```python
from Backtest.pattern_logger import PatternLogger
from Backtest.signal_logger import SignalLogger

class MyStrategy:
    def __init__(self, broker, symbol, strategy_id):
        # Initialize loggers
        self.pattern_logger = PatternLogger(strategy_id)
        self.signal_logger = SignalLogger(strategy_id)
    
    def on_bar(self, timestamp, data):
        # 1. Extract data
        market_data = {'open': ..., 'close': ..., ...}
        indicators = {'EMA_30': ..., 'EMA_50': ...}
        
        # 2. Log pattern (EVERY ROW)
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=self.symbol,
            step_id="entry",
            step_title="Check Entry",
            pattern_condition="EMA_30 > EMA_50",
            pattern_found=True,  # Your condition
            market_data=market_data,
            indicator_values=indicators
        )
        
        # 3. If pattern found, log signal
        if pattern_found:
            self.signal_logger.log_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side="BUY",
                action="ENTRY",
                order_type="MARKET",
                size=100,
                price=market_data['close'],
                reason="Pattern detected",
                market_data=market_data,
                indicator_values=indicators
            )
    
    def finalize(self):
        self.pattern_logger.close()
        self.signal_logger.close()
```

## Pattern Logger API

```python
pattern_logger.log_pattern(
    timestamp=datetime,           # Required: Current time
    symbol=str,                   # Required: e.g., "AAPL"
    step_id=str,                  # Required: e.g., "entry_check"
    step_title=str,               # Required: e.g., "EMA Entry Check"
    pattern_condition=str,        # Required: e.g., "EMA_30 > EMA_50"
    pattern_found=bool,           # Required: True or False
    market_data=dict,             # Required: OHLCV data
    indicator_values=dict,        # Optional: Indicator values
    notes=str                     # Optional: Additional notes
)
```

## Signal Logger API

```python
signal_logger.log_signal(
    timestamp=datetime,           # Required: Signal time
    symbol=str,                   # Required: e.g., "AAPL"
    side=str,                     # Required: "BUY" or "SELL"
    action=str,                   # Required: "ENTRY" or "EXIT"
    order_type=str,               # Required: "MARKET", "LIMIT", "STOP"
    size=int,                     # Required: Position size
    price=float,                  # Required: Current price
    reason=str,                   # Required: Why signal generated
    market_data=dict,             # Required: OHLCV data
    indicator_values=dict,        # Optional: Indicator values
    strategy_state=dict,          # Optional: Strategy state
    limit_price=float,            # Optional: For limit orders
    stop_price=float,             # Optional: For stop orders
    order_id=str,                 # Optional: From broker
    notes=str                     # Optional: Additional notes
)
```

## Output Files

```
signals/
├── {strategy_id}_patterns_{timestamp}.csv   # Pattern logs
├── {strategy_id}_signals_{timestamp}.csv    # Signal logs (CSV)
└── {strategy_id}_signals_{timestamp}.json   # Signal logs (JSON)
```

## Pattern Log Columns

| Column | Description |
|--------|-------------|
| timestamp | Bar timestamp |
| symbol | Trading symbol |
| step_id | Strategy step identifier |
| step_title | Human-readable step name |
| pattern_condition | Condition being checked |
| **pattern_found** | **True or False** |
| close | Close price |
| open | Open price |
| high | High price |
| low | Low price |
| volume | Volume |
| indicator_values | JSON string of indicators |
| notes | Additional notes |

## Signal Log Columns

| Column | Description |
|--------|-------------|
| signal_id | Unique signal ID |
| timestamp | Signal timestamp |
| symbol | Trading symbol |
| side | BUY or SELL |
| action | ENTRY or EXIT |
| order_type | MARKET, LIMIT, STOP |
| size | Position size |
| price | Market price |
| reason | Why signal generated |
| indicator_values | JSON string |
| market_data | JSON string |
| strategy_state | JSON string |
| order_id | Broker order ID |
| notes | Additional notes |

## Sequential Processing Pattern

```python
# Load data with indicators
df = load_market_data(
    ticker="AAPL",
    period="6mo",
    interval="1d",
    indicators=[
        {"name": "EMA", "params": {"period": 30}},
        {"name": "EMA", "params": {"period": 50}}
    ]
)

# Process row by row
for idx, row in df.iterrows():
    timestamp = idx
    
    market_data = {
        "AAPL": {
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume'],
            'EMA_30': row['EMA_30'],
            'EMA_50': row['EMA_50']
        }
    }
    
    # Strategy processes row and logs patterns
    strategy.on_bar(timestamp, market_data)
    
    # Broker executes signals
    broker.step_to(timestamp, market_data)

# Finalize
strategy.finalize()
```

## Common Patterns

### Entry Pattern Logging
```python
def _check_entry(self, timestamp, market_data, indicators):
    pattern_found = indicators['EMA_30'] > indicators['EMA_50']
    
    self.pattern_logger.log_pattern(
        timestamp=timestamp,
        symbol=self.symbol,
        step_id="entry",
        step_title="EMA Crossover Entry",
        pattern_condition="EMA_30 > EMA_50",
        pattern_found=pattern_found,
        market_data=market_data,
        indicator_values=indicators
    )
    
    if pattern_found and not self.in_position:
        self._generate_entry_signal(timestamp, market_data, indicators)
```

### Exit Pattern Logging
```python
def _check_exit(self, timestamp, market_data, indicators):
    stop_loss_hit = market_data['close'] <= self.entry_price * 0.95
    take_profit_hit = market_data['close'] >= self.entry_price * 1.10
    pattern_found = stop_loss_hit or take_profit_hit
    
    self.pattern_logger.log_pattern(
        timestamp=timestamp,
        symbol=self.symbol,
        step_id="exit",
        step_title="Stop Loss / Take Profit Check",
        pattern_condition="SL or TP hit",
        pattern_found=pattern_found,
        market_data=market_data,
        indicator_values=indicators,
        notes=f"Entry: {self.entry_price}, Current: {market_data['close']}"
    )
    
    if pattern_found:
        reason = "Stop loss hit" if stop_loss_hit else "Take profit hit"
        self._generate_exit_signal(timestamp, market_data, indicators, reason)
```

### Signal Generation with Logging
```python
def _generate_entry_signal(self, timestamp, market_data, indicators):
    size = 100
    price = market_data['close']
    
    # Log signal
    self.signal_logger.log_signal(
        timestamp=timestamp,
        symbol=self.symbol,
        side="BUY",
        action="ENTRY",
        order_type="MARKET",
        size=size,
        price=price,
        reason="EMA crossover detected",
        market_data=market_data,
        indicator_values=indicators,
        strategy_state={'in_position': False}
    )
    
    # Submit to broker
    signal = create_signal(...)
    order_id = self.broker.submit_signal(signal.to_dict())
    
    # Update state
    self.in_position = True
    self.entry_price = price
```

## Testing

```bash
# Run test
python Backtest/test_logging_system.py

# Check outputs
ls Backtest/signals/
```

## Summary Statistics

```python
# Get pattern summary
pattern_summary = strategy.pattern_logger.get_pattern_summary()
print(f"Patterns found: {pattern_summary['patterns_found']}")
print(f"Detection rate: {pattern_summary['detection_rate']:.2f}%")

# Get signal summary
signal_summary = strategy.signal_logger.get_signal_summary()
print(f"Total signals: {signal_summary['total_signals']}")
print(f"Entry signals: {signal_summary['entry_signals']}")
print(f"Exit signals: {signal_summary['exit_signals']}")
```

## Tips

1. **Log EVERY row** for patterns - this helps debug missed opportunities
2. **Log ALL signals** - even if broker rejects them
3. **Include meaningful notes** - future you will thank you
4. **Check log files** in `signals/` folder after each run
5. **Use pattern logs** to debug step execution
6. **Use signal logs** for trade simulation and analysis
