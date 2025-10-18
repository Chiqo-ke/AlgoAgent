# Quick Reference: Indicator Column Names

**Version:** 1.0.0  
**For:** AI Strategy Code Generation  
**Date:** October 17, 2025

---

## 🎯 The Rule

**Indicator columns are ALWAYS named with their parameters:**

```
INDICATOR_PARAM1_PARAM2_...
```

---

## 📋 Common Indicators

| You Request | You Get Column(s) |
|-------------|-------------------|
| `'RSI': {'timeperiod': 14}` | `RSI_14` |
| `'RSI': {'timeperiod': 21}` | `RSI_21` |
| `'SMA': {'timeperiod': 20}` | `SMA_20` |
| `'EMA': {'timeperiod': 50}` | `EMA_50` |
| `'ATR': {'timeperiod': 14}` | `ATR_14` |
| `'ADX': {'timeperiod': 14}` | `ADX_14` |
| `'CCI': {'timeperiod': 14}` | `CCI_14` |
| `'MACD': {defaults}` | `MACD`, `MACD_SIGNAL`, `MACD_HIST` |
| `'BOLLINGER': {defaults}` | `BBANDS_UPPER`, `BBANDS_MIDDLE`, `BBANDS_LOWER` |
| `'STOCH': {defaults}` | `STOCH_K`, `STOCH_D` |
| `'OBV': None` | `OBV` |
| `'VWAP': None` | `VWAP` |

---

## ✅ Correct Code Pattern

```python
# 1. Load data
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={'RSI': {'timeperiod': 14}},
    period='1mo',
    interval='1d'
)

# 2. ALWAYS print columns
print(f"Columns: {list(df.columns)}")
# Output: ['Open', 'High', 'Low', 'Close', 'Volume', 'RSI_14']

# 3. Use exact column name
for timestamp, row in df.iterrows():
    rsi_value = row['RSI_14']  # ✅ CORRECT
```

---

## ❌ Wrong Code Pattern

```python
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={'RSI': {'timeperiod': 14}}
)

for timestamp, row in df.iterrows():
    rsi_value = row['RSI']  # ❌ WRONG! Will crash with KeyError
```

---

## 🔧 Strategy Template

```python
def run_backtest():
    # Load data
    df, metadata = load_market_data(
        ticker='AAPL',
        indicators={
            'RSI': {'timeperiod': 14},
            'SMA': {'timeperiod': 20}
        },
        period='3mo',
        interval='1d'
    )
    
    # Verify columns (MANDATORY)
    print(f"Loaded columns: {list(df.columns)}")
    
    # Optional: Rename for cleaner code
    df = df.rename(columns={'RSI_14': 'rsi', 'SMA_20': 'sma'})
    
    # Run simulation
    for timestamp, row in df.iterrows():
        market_data = {
            'AAPL': {
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume'],
                'rsi': row['rsi'],      # After renaming
                'sma': row['sma']       # After renaming
            }
        }
        
        strategy.on_bar(timestamp, market_data)
        broker.step_to(timestamp, market_data)
```

---

## 🎓 Key Takeaways

1. **Never assume** - Always print `df.columns` first
2. **Use exact names** - `RSI_14` not `RSI`
3. **Include parameters** - Column names have parameters in them
4. **Multi-output aware** - Some indicators produce multiple columns
5. **Optional renaming** - Can rename after loading if preferred
6. **Document mapping** - Add comments showing column mappings

---

## 🚨 Pre-Flight Checklist

Before generating strategy code:

- [ ] Loaded data with `load_market_data()`
- [ ] Printed `df.columns` to verify names
- [ ] Used exact column names with parameters
- [ ] Handled multi-output indicators correctly
- [ ] Added NaN checks for indicator values
- [ ] Documented column name mappings
- [ ] Tested with actual data

---

**Remember:** When in doubt, print the columns!

```python
print(f"Available columns: {list(df.columns)}")
```
