# Signals Directory

This directory contains pattern detection logs and signal generation logs from backtests.

## File Types

### Pattern Logs
- **Filename**: `{strategy_id}_patterns_{timestamp}.csv`
- **Purpose**: Logs every row of data with pattern detection results (True/False)
- **Use for**: Debugging step execution, verifying pattern detection logic

### Signal Logs (CSV)
- **Filename**: `{strategy_id}_signals_{timestamp}.csv`
- **Purpose**: Logs all trading signals with market context
- **Use for**: Trade simulation, signal verification, performance analysis

### Signal Logs (JSON)
- **Filename**: `{strategy_id}_signals_{timestamp}.json`
- **Purpose**: Full signal details in structured format
- **Use for**: Programmatic signal replay, detailed analysis

## Example Files

After running a backtest, you'll see files like:
```
ema_strategy_001_patterns_20251022_143022.csv
ema_strategy_001_signals_20251022_143022.csv
ema_strategy_001_signals_20251022_143022.json
```

## How Logs Help

1. **Pattern Logs** show you EVERY row analyzed with True/False for pattern detection
2. **Signal Logs** capture all actual trading signals for later simulation
3. Both logs help debug strategy logic and improve performance

## Cleaning Up

These files can be deleted to free up space, but keep them if you want to:
- Review historical pattern detection
- Replay signals for trade simulation
- Analyze strategy behavior over time
