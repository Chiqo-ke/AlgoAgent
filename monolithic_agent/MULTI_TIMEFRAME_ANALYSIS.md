# Multi-Timeframe/Multi-Period Testing Analysis
**Date:** December 5, 2025  
**Status:** ⚠️ PARTIAL - Parameters exist but not fully integrated

---

## Executive Summary

**Finding:** The system **DOES support** multi-timeframe/multi-period testing, but there's a disconnect between:
1. ✅ Frontend UI (collects symbol, period, interval)
2. ❌ Backend API (doesn't receive or use these parameters)
3. ✅ Generated code (has configurable parameters)
4. ❌ API execution (uses hardcoded defaults)

**Result:** Strategies are always tested with **hardcoded defaults** (`AAPL`, `6mo`, `1d`) regardless of user selections.

---

## Current Implementation Status

### ✅ What's Working

#### 1. Generated Code Supports All Parameters

**File:** `algo676545676567.py` lines 216-218, 342-343

```python
def run_backtest(
    symbol: str = "AAPL",    # ✅ Configurable
    period: str = "6mo",     # ✅ Configurable  
    interval: str = "1d",    # ✅ Configurable
    start_cash: float = 100000,
    fee_flat: float = 1.0,
    fee_pct: float = 0.001,
    slippage_pct: float = 0.0005
):
```

**Supported Values:**
- **Symbols:** Any valid ticker (AAPL, MSFT, TSLA, etc.)
- **Periods:** `'1mo'`, `'3mo'`, `'6mo'`, `'1y'`, `'2y'`, `'5y'`, `'max'`
- **Intervals:** `'1m'`, `'5m'`, `'15m'`, `'1h'`, `'1d'`, `'1wk'`, `'1mo'`

#### 2. Frontend UI Collects Parameters

**File:** `Algo/src/pages/Dashboard.tsx` lines 105-107, 1419-1445

```tsx
const [backtestSymbol, setBacktestSymbol] = useState("AAPL");
const [backtestPeriod, setBacktestPeriod] = useState("1y");
const [backtestInterval, setBacktestInterval] = useState("1d");
```

**UI Elements:**
- ✅ Symbol dropdown (populated from API)
- ✅ Period selector ('1mo', '3mo', '6mo', '1y', '2y', '5y')
- ✅ Interval selector ('1m', '5m', '15m', '1h', '1d')

**Data Flow to Navigation:**
```tsx
navigate(`/backtesting/${confirmationData.strategyId}`, { 
  state: { 
    backtestConfig: {
      symbol: backtestSymbol,      // ✅ Passed
      period: backtestPeriod,      // ✅ Passed
      interval: backtestInterval   // ✅ Passed
    }
  } 
});
```

#### 3. Documentation Exists

**File:** `docs/implementation/BOT_EXECUTION_INTEGRATION_GUIDE.md`

```markdown
- `test_symbol` - Trading symbol (default: AAPL)
- `test_period_days` - Historical data period (default: 365)
```

---

### ❌ What's Missing

#### 1. API Doesn't Accept Parameters

**File:** `strategy_api/views.py` line 1044 (generate_executable_code)

**Current API Call:**
```python
executor = BotExecutor()
execution_result = executor.execute_bot(
    strategy_file=str(python_file),
    save_results=True
    # ❌ NO symbol, period, interval parameters!
)
```

**BotExecutor.execute_bot() Signature:**
```python
def execute_bot(
    self,
    strategy_file: str,
    strategy_name: str = None,
    description: str = None,
    parameters: Dict[str, Any] = None,
    test_symbol: str = "AAPL",        # ⚠️ Default only
    test_period_days: int = 365,      # ⚠️ Default only
    save_results: bool = True
) -> BotExecutionResult:
```

**Problem:** API doesn't receive or pass user-selected parameters to executor.

#### 2. Frontend Doesn't Send Parameters to API

**File:** `Algo/src/pages/Dashboard.tsx` line 793+

**Current API Request:**
```tsx
const codeGenResponse = await fetch(
  `http://localhost:8000/api/strategies/api/generate_executable_code/`,
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      canonical_json: confirmationData.canonicalJson,
      strategy_name: editedStrategyName.trim(),
      strategy_id: confirmationData.strategyId,
      // ❌ Missing: symbol, period, interval
    }),
  }
);
```

**What Should Be Sent:**
```tsx
body: JSON.stringify({
  canonical_json: confirmationData.canonicalJson,
  strategy_name: editedStrategyName.trim(),
  strategy_id: confirmationData.strategyId,
  // ✅ Add these:
  test_symbol: backtestSymbol,
  test_period: backtestPeriod,      // or test_period_days
  test_interval: backtestInterval,
}),
```

#### 3. Generated Code Uses Hardcoded Defaults

**File:** `algo676545676567.py` line 342

```python
if __name__ == "__main__":
    metrics = run_backtest(
        symbol="AAPL",   # ❌ Hardcoded
        period="6mo",    # ❌ Hardcoded
        interval="1d",   # ❌ Hardcoded
        start_cash=100000,
        fee_flat=1.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )
```

**Problem:** When API executes the strategy, it runs this hardcoded `if __name__ == "__main__"` block with fixed parameters.

---

## Why No Trades Were Executed

### Root Cause Analysis

**Strategy:** RSI-based entry (RSI < 30)  
**Test Period:** 6 months (hardcoded)  
**Test Symbol:** AAPL (hardcoded)  
**Test Interval:** 1 day (hardcoded)

**Result:** 0 trades

**Possible Reasons:**

1. **Market Conditions** - AAPL may not have had RSI < 30 in past 6 months
   - Tech stocks have been strong
   - RSI < 30 is rare in bull markets
   - Need longer period or different symbol

2. **Short Test Period** - 6 months may be insufficient
   - RSI signals are infrequent
   - Need 1-2 years for meaningful results
   - User selected "1y" but got "6mo"

3. **Wrong Symbol** - AAPL may not suit this strategy
   - Large cap tech less volatile
   - User may want to test on TSLA, smaller caps
   - User selected symbol ignored

4. **Timeframe Mismatch** - Daily bars may miss opportunities
   - User may want hourly or 4H bars
   - Different timeframes show different patterns
   - User selected interval ignored

---

## Impact Assessment

### User Experience Impact

| Issue | User Expectation | Actual Behavior | Impact |
|-------|-----------------|-----------------|--------|
| Symbol Selection | Test on selected symbol | Always tests on AAPL | **HIGH** - Can't test strategy on desired assets |
| Period Selection | Test selected period (1y) | Always tests 6 months | **HIGH** - Insufficient data for validation |
| Interval Selection | Test selected timeframe | Always tests daily | **MEDIUM** - Can't validate intraday strategies |
| Trade Generation | See trades based on parameters | 0 trades with fixed params | **CRITICAL** - Can't evaluate strategy |

### Business Logic Issues

1. **Cannot validate multi-asset strategies** - Stocks behave differently
2. **Cannot test timeframe robustness** - Strategy may work on 1H but not 1D
3. **Insufficient historical data** - 6 months inadequate for most strategies
4. **User selections ignored** - Breaks trust in system

---

## Technical Solution

### Phase 1: Quick Fix (30 minutes)

#### A. Update Frontend API Call

**File:** `Algo/src/pages/Dashboard.tsx` line 793

```tsx
// BEFORE
body: JSON.stringify({
  canonical_json: confirmationData.canonicalJson,
  strategy_name: editedStrategyName.trim(),
  strategy_id: confirmationData.strategyId,
}),

// AFTER
body: JSON.stringify({
  canonical_json: confirmationData.canonicalJson,
  strategy_name: editedStrategyName.trim(),
  strategy_id: confirmationData.strategyId,
  test_config: {
    symbol: backtestSymbol,
    period: backtestPeriod,
    interval: backtestInterval,
  },
}),
```

#### B. Update Backend API Handler

**File:** `strategy_api/views.py` line 1044

```python
# BEFORE
execution_result = executor.execute_bot(
    strategy_file=str(python_file),
    save_results=True
)

# AFTER
test_config = data.get('test_config', {})
test_symbol = test_config.get('symbol', 'AAPL')
test_period = test_config.get('period', '1y')
test_interval = test_config.get('interval', '1d')

# Convert period to days
period_to_days = {
    '1mo': 30, '3mo': 90, '6mo': 180,
    '1y': 365, '2y': 730, '5y': 1825
}
test_period_days = period_to_days.get(test_period, 365)

execution_result = executor.execute_bot(
    strategy_file=str(python_file),
    test_symbol=test_symbol,
    test_period_days=test_period_days,
    save_results=True,
    parameters={'test_interval': test_interval}  # Pass interval in parameters
)
```

#### C. Update Executor to Pass Parameters to Script

**File:** `Backtest/bot_executor.py` line 270

```python
# BEFORE
cmd = [sys.executable, str(strategy_file)]

# AFTER  
cmd = [
    sys.executable, str(strategy_file),
    '--symbol', test_symbol,
    '--period', self._days_to_period_string(test_period_days),
    '--interval', parameters.get('test_interval', '1d')
]
```

#### D. Update Generated Code Template

**File:** `Backtest/SYSTEM_PROMPT.md` - Add argument parsing

```python
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', default='AAPL')
    parser.add_argument('--period', default='6mo')
    parser.add_argument('--interval', default='1d')
    parser.add_argument('--cash', type=float, default=100000)
    args = parser.parse_args()
    
    metrics = run_backtest(
        symbol=args.symbol,
        period=args.period,
        interval=args.interval,
        start_cash=args.cash,
        fee_flat=1.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )
```

### Phase 2: Robust Solution (2-3 hours)

#### 1. Create Backtest Configuration Schema

**New File:** `strategy_api/schemas.py`

```python
from pydantic import BaseModel, Field

class BacktestConfig(BaseModel):
    symbol: str = Field(default="AAPL", description="Trading symbol")
    period: str = Field(default="1y", pattern="^(1mo|3mo|6mo|1y|2y|5y)$")
    interval: str = Field(default="1d", pattern="^(1m|5m|15m|1h|1d|1wk|1mo)$")
    start_cash: float = Field(default=100000, gt=0)
    commission: float = Field(default=0.001, ge=0, le=0.1)
    slippage: float = Field(default=0.0005, ge=0, le=0.01)
```

#### 2. Store Config in Database

**Migration:** Add backtest_config JSONField to Strategy model

```python
class Strategy(models.Model):
    # ... existing fields ...
    backtest_config = models.JSONField(
        default=dict,
        help_text="Default backtest configuration"
    )
```

#### 3. API Endpoint for Multi-Period Testing

**New Endpoint:** `/api/strategies/{id}/test-multiple/`

```python
@action(detail=True, methods=['post'])
def test_multiple(self, request, pk=None):
    """
    Test strategy across multiple configurations
    
    Request:
    {
        "symbols": ["AAPL", "MSFT", "TSLA"],
        "periods": ["6mo", "1y", "2y"],
        "intervals": ["1h", "1d"]
    }
    
    Returns: Comparison matrix of results
    """
    pass
```

#### 4. Frontend: Multi-Period Comparison View

**New Component:** `MultiPeriodBacktest.tsx`
- Test across multiple symbols simultaneously
- Compare performance across timeframes
- Heatmap visualization of best configurations

---

## Immediate Action Plan

### Priority 1: Fix Current Test (1 hour)

**Objective:** Get trades showing in current strategy

**Steps:**
1. ✅ Manually test with longer period and different symbol
   ```python
   # Edit algo676545676567.py line 342
   metrics = run_backtest(
       symbol="TSLA",   # More volatile
       period="2y",     # Longer history
       interval="1d",
       ...
   )
   ```

2. ✅ Run manually to verify trades occur
   ```bash
   cd C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
   python Backtest\codes\algo676545676567.py
   ```

3. ✅ Document which configurations produce trades

### Priority 2: Implement Parameter Passing (2 hours)

**Tasks:**
- [ ] Update Dashboard.tsx to send test_config
- [ ] Update views.py to receive and use test_config
- [ ] Update bot_executor.py to pass CLI arguments
- [ ] Update SYSTEM_PROMPT.md to generate argparse code
- [ ] Test end-to-end with user-selected parameters

### Priority 3: Multi-Configuration Testing (4 hours)

**Tasks:**
- [ ] Create BacktestConfig schema
- [ ] Add backtest_config to Strategy model
- [ ] Create multi-test API endpoint
- [ ] Build comparison UI component
- [ ] Add result visualization

---

## Testing Checklist

```
□ Test RSI strategy on TSLA with 2y period - expect trades
□ Test same strategy on AAPL with 1y period - compare
□ Test with 1h interval vs 1d interval - verify different results
□ Verify frontend sends selected parameters
□ Verify backend receives and uses parameters
□ Verify generated code respects CLI arguments
□ Test multi-symbol comparison endpoint
□ Verify results stored with configuration used
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| User-selected params used | 0% | 100% |
| Trades generated (RSI on TSLA 2y) | 0 | 5-15 |
| Configuration flexibility | Fixed | Full |
| Multi-symbol testing | No | Yes |
| Multi-period comparison | No | Yes |

---

## Conclusion

**The feature exists but is disconnected.** The system has all the pieces:
- ✅ UI collects parameters
- ✅ Generated code supports parameters
- ✅ Executor can accept parameters
- ❌ API doesn't connect them

**Fix Priority:** HIGH - This is blocking strategy validation

**Estimated Fix Time:** 2-3 hours for full integration

**Expected Outcome:** Users can test strategies on any symbol, period, and interval they select, resulting in meaningful trade generation and performance metrics.
