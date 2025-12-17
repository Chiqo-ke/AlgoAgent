# Manual Backtest Testing Plan
## Testing Lot Size, Commission, and Initial Balance

### Strategy to Test
**Name:** Algo9999999888877 - Price Action Strategy  
**Strategy ID:** 37

---

## Test Scenarios

### Test 1: Baseline Configuration
**Purpose:** Establish baseline results

| Parameter | Value |
|-----------|-------|
| Strategy | Algo9999999888877 - Price Action Strategy (ID: 37) |
| Symbol | AAPL |
| Period | 3 months |
| Initial Balance | $10,000 |
| Lot Size | 1.0 |
| Commission | 0.001 (0.1%) |
| Slippage | 0.0005 (0.05%) |

**Expected Outcome:**
- Backend logs show: `Initial Balance: 10000.0`
- Backend logs show: `Lot Size: 1.0`
- Backend logs show: `Commission: 0.001`
- Trades are executed
- P&L is calculated correctly
- Final Equity = Initial Balance + Net P&L

---

### Test 2: Higher Initial Balance
**Purpose:** Verify initial balance affects buying power

| Parameter | Value |
|-----------|-------|
| Strategy | Algo9999999888877 - Price Action Strategy (ID: 37) |
| Symbol | AAPL |
| Period | 3 months |
| Initial Balance | $50,000 ⭐ |
| Lot Size | 1.0 |
| Commission | 0.001 (0.1%) |
| Slippage | 0.0005 (0.05%) |

**Expected Outcome:**
- Backend logs show: `Initial Balance: 50000.0` ⭐
- Same trades as Test 1 but larger position sizes (more buying power)
- Final Equity = $50,000 + Net P&L
- P&L should be DIFFERENT from Test 1 (larger positions = larger gains/losses)

---

### Test 3: Larger Lot Size
**Purpose:** Verify lot size affects position sizing

| Parameter | Value |
|-----------|-------|
| Strategy | Algo9999999888877 - Price Action Strategy (ID: 37) |
| Symbol | AAPL |
| Period | 3 months |
| Initial Balance | $10,000 |
| Lot Size | 2.5 ⭐ |
| Commission | 0.001 (0.1%) |
| Slippage | 0.0005 (0.05%) |

**Expected Outcome:**
- Backend logs show: `Lot Size: 2.5` ⭐
- Same entry/exit signals as Test 1
- Position sizes are 2.5x larger
- P&L magnitude is approximately 2.5x Test 1 (before costs)
- More commission paid due to larger trades

---

### Test 4: Higher Commission
**Purpose:** Verify commission reduces profitability

| Parameter | Value |
|-----------|-------|
| Strategy | Algo9999999888877 - Price Action Strategy (ID: 37) |
| Symbol | AAPL |
| Period | 3 months |
| Initial Balance | $10,000 |
| Lot Size | 1.0 |
| Commission | 0.01 (1%) ⭐ |
| Slippage | 0.0005 (0.05%) |

**Expected Outcome:**
- Backend logs show: `Commission: 0.01` ⭐
- Same trades as Test 1
- Net P&L is LOWER than Test 1 (higher costs)
- Each trade costs 10x more in commission

---

## What to Observe in Backend Logs

Look for these log messages in the Django console:

```
📋 Backtest Configuration:
   Initial Balance: 10000.0
   Lot Size: 1.0
   Commission: 0.001
   Slippage: 0.0005
```

```
📊 Extracting trades from backtesting.py results...
   Trades found: X
   Total PnL from trades: $XXX.XX
```

```
💰 SimBroker Execution Results:
   Starting Balance: $10,000.00
   Final Equity: $X,XXX.XX
   Total Fills: X
   P&L: $XXX.XX
```

```
📈 Final Backtest Results:
   Initial Balance: $10,000.00
   Total PnL: $XXX.XX
   Final Equity: $X,XXX.XX
   Return: X.XX%
```

---

## Validation Checklist

For each test, verify:

- [ ] Backend logs show correct configuration values
- [ ] Initial Balance matches input
- [ ] Lot Size matches input
- [ ] Commission matches input
- [ ] Trades are generated (Total Trades > 0)
- [ ] P&L is non-zero (unless no winning trades)
- [ ] Final Equity = Initial Balance + Net P&L
- [ ] Frontend displays same values as backend logs

---

## How to Run Tests

1. **Open Frontend:** http://localhost:5173/backtesting
2. **Select Strategy:** Choose "Algo9999999888877 - Price Action Strategy" from dropdown
3. **Configure Parameters:** Set values according to test scenario
4. **Monitor Backend:** Watch Django console for log messages
5. **Run Backtest:** Click "Run Backtest" button
6. **Record Results:** Note down P&L, equity, and trade count
7. **Repeat:** Run all 4 test scenarios

---

## Expected Results Summary

| Test | Initial Balance | Lot Size | Commission | Expected Behavior |
|------|----------------|----------|------------|-------------------|
| 1 (Baseline) | $10,000 | 1.0 | 0.1% | Baseline results |
| 2 (High Balance) | $50,000 | 1.0 | 0.1% | Larger positions, different P&L |
| 3 (Large Lot) | $10,000 | 2.5 | 0.1% | 2.5x position sizes, ~2.5x P&L |
| 4 (High Commission) | $10,000 | 1.0 | 1.0% | Same trades, lower net P&L |

---

## Success Criteria

✅ **PASS** if:
- Backend logs show correct configuration for all tests
- Test 2 produces different results than Test 1 (due to higher balance)
- Test 3 shows proportionally larger P&L than Test 1
- Test 4 shows lower net P&L than Test 1 (due to higher commission)
- Final Equity calculation is always correct: `Initial Balance + Net P&L = Final Equity`

❌ **FAIL** if:
- Configuration values in logs don't match inputs
- All tests produce identical results (means config not being used)
- Final Equity doesn't match formula
- P&L is always the same fixed value

---

## Notes

- The logging we added to [consumers.py](../monolithic_agent/trading/consumers.py#L324-L332) will show configuration usage
- Watch the Django console output while running backtests
- If you don't see logs, the Django server may need to be restarted
- Strategy ID 37 is confirmed in database as "Algo9999999888877 - Price Action Strategy"
