# CLI Test Command - Quick Start Guide

## ✅ Implementation Complete

The `test` command has been added to the CLI. It uses the **Tester Agent** to validate generated strategy artifacts.

## How to Use

### 1. Interactive Mode

```powershell
cd C:\Users\nyaga\Documents\AlgoAgent\multi_agent
python cli.py
```

Then:
```
>>> test wf_a85becffff31
```

### 2. Command-Line Mode

```powershell
python cli.py --test wf_a85becffff31
```

### 3. Full Workflow (Submit → Execute → Test)

```powershell
# Step 1: Submit and execute
python cli.py --request "Create RSI strategy with buy<30 sell>70" --run

# Step 2: Get the workflow ID from output (e.g., wf_abc123)

# Step 3: Test the generated code
python cli.py --test wf_abc123
```

## What the Test Command Does

1. **Finds Generated Strategies**
   - Looks in `Backtest/codes/` for `ai_strategy_*.py` files
   - Matches each strategy with its test file in `tests/`

2. **Runs Tester Agent**
   - Executes each test using the Tester Agent
   - Uses Docker sandbox for isolated testing
   - Validates with SimBroker (if configured)

3. **Shows Results**
   - ✅ **PASSED**: Test succeeded with metrics
   - ❌ **FAILED**: Test failed with error details
   - ⚠️ **SKIPPED**: Test file not found

4. **Generates Report**
   - Summary: Total, Passed, Failed, Success Rate
   - Detailed JSON report saved in `workflows/`
   - Includes test metrics (trades, win rate, PnL, etc.)

## Example Output

```
🧪 Testing workflow: wf_a85becffff31

📁 Found 4 strategy file(s):
   - ai_strategy_data_loading_ema_strategy.py
   - ai_strategy_entry_ema_crossover.py
   - ai_strategy_exit_ema_crossover.py
   - ai_strategy_indicators.py

🧪 Testing: ai_strategy_data_loading_ema_strategy
   Strategy: ai_strategy_data_loading_ema_strategy.py
   Test: test_ai_strategy_data_loading_ema_strategy.py
   ⏳ Running tests...
   ✅ PASSED (3.45s)
      Total Trades: 38
      Win Rate: 52.6%
      Net PnL: $845.32

🧪 Testing: ai_strategy_entry_ema_crossover
   Strategy: ai_strategy_entry_ema_crossover.py
   Test: test_ai_strategy_entry_ema_crossover.py
   ⏳ Running tests...
   ✅ PASSED (2.18s)

======================================================================
📊 TEST SUMMARY
======================================================================
   Total: 4
   Passed: 4 ✅
   Failed: 0 ❌
   Success Rate: 100%

💾 Detailed report saved: test_report_wf_a85becffff31_20251120_143512.json
```

## Test Report Contents

The JSON report includes:
```json
{
  "workflow_id": "wf_a85becffff31",
  "timestamp": "2025-11-20T14:35:12.345678",
  "summary": {
    "total": 4,
    "passed": 4,
    "failed": 0,
    "success_rate": 1.0
  },
  "results": [
    {
      "strategy": "ai_strategy_data_loading_ema_strategy",
      "status": "ready",
      "duration": 3.45,
      "metrics": {
        "total_trades": 38,
        "win_rate": 0.526,
        "net_pnl": 845.32,
        "max_drawdown": 0.08
      },
      "artifacts": {
        "report": "artifacts/.../test_report.json",
        "trades": "artifacts/.../trades.csv",
        "equity": "artifacts/.../equity_curve.csv"
      }
    }
  ]
}
```

## Commands Updated

### Interactive Mode Help
```
Commands:
  submit <request>  - Submit new strategy request
  execute <id>      - Execute workflow tasks
  test <id>         - Test generated strategy artifacts  ← NEW
  status <id>       - Check workflow status
  list              - List all workflows
  help              - Show this help
  exit              - Exit CLI
```

### Command-Line Help
```
python cli.py --help

Options:
  --request, -r   Submit a strategy request
  --execute, -e   Execute workflow tasks
  --test, -t      Test generated strategy artifacts  ← NEW
  --status, -s    Check workflow status
  --list, -l      List all workflows
  --run           Execute workflow immediately after submit
```

## Testing Your Workflow

Try it now with your EMA crossover workflow:

```powershell
cd C:\Users\nyaga\Documents\AlgoAgent\multi_agent
python cli.py --test wf_a85becffff31
```

Or in interactive mode:
```powershell
python cli.py
>>> test wf_a85becffff31
```

## Troubleshooting

### If no test files found:
- The Coder Agent should generate both strategy and test files
- Check `tests/test_ai_strategy_*.py` exists
- If missing, the tester will skip with a warning

### If tests fail:
- Check the error message in output
- Review the detailed JSON report
- Fix issues in the strategy code
- Re-run execute and test

### If Docker not available:
- Tester Agent will attempt to run tests locally
- Some features (SimBroker validation) may be limited
- Consider setting up Docker for full testing capability

## Next Steps

After testing passes:
1. Review the test report metrics
2. Check generated artifacts (trades.csv, equity_curve.csv)
3. Deploy strategy to production (if metrics are good)
4. Monitor live performance

Enjoy testing your strategies! 🚀
