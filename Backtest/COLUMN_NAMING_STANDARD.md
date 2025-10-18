# Column Naming Standard for AlgoAgent

**Version:** 1.0.0  
**Date:** October 17, 2025  
**Status:** ✅ Mandatory for all strategies

---

## Overview

This document defines the **standardized column naming convention** for all DataFrames in the AlgoAgent backtesting system. This standard ensures consistency across all AI-generated strategies and makes debugging easier.

---

## The Standard

### Rule #1: OHLCV Columns (Always Capitalized)

```python
'Open', 'High', 'Low', 'Close', 'Volume'
```

These are the base columns from yfinance and are **always capitalized**.

### Rule #2: Indicator Columns (Include Parameters)

Indicator columns are **automatically named** by the indicator calculator using this pattern:

```
INDICATOR_PARAM1_PARAM2_...
```

**Examples:**

| Indicator Request | Parameters | Resulting Column Name(s) |
|------------------|------------|-------------------------|
| `'RSI': {'timeperiod': 14}` | timeperiod=14 | `RSI_14` |
| `'SMA': {'timeperiod': 20}` | timeperiod=20 | `SMA_20` |
| `'EMA': {'timeperiod': 50}` | timeperiod=50 | `EMA_50` |
| `'ATR': {'timeperiod': 14}` | timeperiod=14 | `ATR_14` |
| `'ADX': {'timeperiod': 14}` | timeperiod=14 | `ADX_14` |
| `'CCI': {'timeperiod': 14}` | timeperiod=14 | `CCI_14` |

### Rule #3: Multi-Output Indicators (Descriptive Suffixes)

Some indicators produce multiple columns with descriptive suffixes:

| Indicator | Columns Produced |
|-----------|------------------|
| **MACD** | `MACD`, `MACD_SIGNAL`, `MACD_HIST` |
| **BOLLINGER** | `BBANDS_UPPER`, `BBANDS_MIDDLE`, `BBANDS_LOWER` |
| **STOCH** | `STOCH_K`, `STOCH_D` |
| **SAR** | `SAR` |

### Rule #4: Parameter-Free Indicators

Indicators without parameters use just the indicator name:

```python
'OBV', 'VWAP'
```

---

## Why This Standard?

### Problem Before

```python
# Loading RSI with timeperiod=14
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={'RSI': {'timeperiod': 14}}
)

# ERROR: Which RSI is this? 14? 21? 30?
rsi = row['RSI']  # ❌ Ambiguous!
```

### Solution Now

```python
# Loading RSI with timeperiod=14
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={'RSI': {'timeperiod': 14}}
)

# CLEAR: This is RSI with 14-period
rsi = row['RSI_14']  # ✅ Explicit and clear!
```

**Benefits:**
1. **No ambiguity** - Column name tells you exact parameters
2. **Multiple indicators** - Can have RSI_14 and RSI_21 in same DataFrame
3. **Debugging** - Easy to spot parameter mismatches
4. **Documentation** - Code is self-documenting
5. **AI consistency** - All generated strategies follow same pattern

---

## Usage Examples

### Example 1: Basic RSI Strategy

```python
def run_backtest():
    # Load data with RSI
    df, metadata = load_market_data(
        ticker='AAPL',
        indicators={'RSI': {'timeperiod': 14}},
        period='3mo',
        interval='1d'
    )
    
    # Print to verify column names
    print(f"Columns: {list(df.columns)}")
    # Output: ['Open', 'High', 'Low', 'Close', 'Volume', 'RSI_14']
    
    # Use exact column name
    for timestamp, row in df.iterrows():
        rsi_value = row['RSI_14']  # ✅ Correct
        
        if rsi_value < 30:
            # Buy signal
            pass
```

### Example 2: Multiple Moving Averages

```python
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={
        'SMA': {'timeperiod': 20},
        'EMA': {'timeperiod': 50}
    }
)

# Columns: [..., 'SMA_20', 'EMA_50']

for timestamp, row in df.iterrows():
    sma_20 = row['SMA_20']
    ema_50 = row['EMA_50']
    
    # Golden cross strategy
    if sma_20 > ema_50:
        # Bullish signal
        pass
```

### Example 3: MACD Strategy

```python
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={
        'MACD': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}
    }
)

# Columns: [..., 'MACD', 'MACD_SIGNAL', 'MACD_HIST']

for timestamp, row in df.iterrows():
    macd_line = row['MACD']
    macd_signal = row['MACD_SIGNAL']
    macd_hist = row['MACD_HIST']
    
    # MACD crossover
    if macd_line > macd_signal:
        # Bullish signal
        pass
```

### Example 4: Bollinger Bands

```python
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={
        'BOLLINGER': {'timeperiod': 20, 'nbdevup': 2, 'nbdevdn': 2}
    }
)

# Columns: [..., 'BBANDS_UPPER', 'BBANDS_MIDDLE', 'BBANDS_LOWER']

for timestamp, row in df.iterrows():
    close = row['Close']
    upper = row['BBANDS_UPPER']
    middle = row['BBANDS_MIDDLE']
    lower = row['BBANDS_LOWER']
    
    # Bollinger breakout
    if close > upper:
        # Overbought signal
        pass
```

---

## Best Practices

### ✅ DO: Always Print Columns

```python
df, metadata = load_market_data(ticker='AAPL', indicators={'RSI': {'timeperiod': 14}})
print(f"Columns: {list(df.columns)}")  # ✅ Good practice
```

### ✅ DO: Use Exact Column Names

```python
rsi_14 = row['RSI_14']  # ✅ Explicit
macd = row['MACD']      # ✅ Clear
```

### ✅ DO: Handle Missing Values

```python
rsi_value = row.get('RSI_14', None)
if rsi_value is None or pd.isna(rsi_value):
    return  # Skip this bar
```

### ✅ DO: Document Column Mapping

```python
# Load data
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={'RSI': {'timeperiod': 14}}
)

# Column mapping:
# RSI with timeperiod=14 → RSI_14
```

### ❌ DON'T: Assume Generic Names

```python
rsi = row['RSI']  # ❌ Wrong! Column is 'RSI_14'
sma = row['SMA']  # ❌ Wrong! Column is 'SMA_20'
```

### ❌ DON'T: Hard-Code Without Checking

```python
# ❌ Bad: Assumes column name without checking
for timestamp, row in df.iterrows():
    rsi = row['RSI']  # Will crash if column is 'RSI_14'
```

---

## Column Renaming (Optional)

If you prefer cleaner names in your strategy logic, you can rename columns after loading:

```python
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={
        'RSI': {'timeperiod': 14},
        'SMA': {'timeperiod': 20}
    }
)

# Optional: Rename for cleaner access
df = df.rename(columns={
    'RSI_14': 'rsi',
    'SMA_20': 'sma'
})

print(f"Renamed columns: {list(df.columns)}")
# Output: ['Open', 'High', 'Low', 'Close', 'Volume', 'rsi', 'sma']

# Now you can use cleaner names
for timestamp, row in df.iterrows():
    rsi = row['rsi']  # ✅ Works after renaming
    sma = row['sma']  # ✅ Works after renaming
```

**Note:** Renaming is optional but must be done explicitly and documented.

---

## Complete Indicator Reference

| Indicator | Parameters | Column Name Pattern | Example |
|-----------|-----------|---------------------|---------|
| RSI | timeperiod | `RSI_{timeperiod}` | RSI_14 |
| SMA | timeperiod | `SMA_{timeperiod}` | SMA_20 |
| EMA | timeperiod | `EMA_{timeperiod}` | EMA_50 |
| MACD | fast, slow, signal | `MACD`, `MACD_SIGNAL`, `MACD_HIST` | MACD, MACD_SIGNAL, MACD_HIST |
| BOLLINGER | timeperiod, nbdevup, nbdevdn | `BBANDS_UPPER`, `BBANDS_MIDDLE`, `BBANDS_LOWER` | BBANDS_UPPER, BBANDS_MIDDLE, BBANDS_LOWER |
| STOCH | fastk, slowk, slowd | `STOCH_K`, `STOCH_D` | STOCH_K, STOCH_D |
| ATR | timeperiod | `ATR_{timeperiod}` | ATR_14 |
| ADX | timeperiod | `ADX_{timeperiod}` | ADX_14 |
| CCI | timeperiod | `CCI_{timeperiod}` | CCI_14 |
| OBV | (none) | `OBV` | OBV |
| VWAP | (none) | `VWAP` | VWAP |
| SAR | acceleration, maximum | `SAR` | SAR |

---

## Testing Your Strategy

Always test with a simple print to verify column names:

```python
def test_column_names():
    """Test to verify indicator column names"""
    df, metadata = load_market_data(
        ticker='AAPL',
        indicators={
            'RSI': {'timeperiod': 14},
            'SMA': {'timeperiod': 20},
            'MACD': None
        }
    )
    
    print("=" * 50)
    print("COLUMN VERIFICATION TEST")
    print("=" * 50)
    print(f"Total columns: {len(df.columns)}")
    print(f"Column names: {list(df.columns)}")
    print("=" * 50)
    
    # Expected output:
    # ['Open', 'High', 'Low', 'Close', 'Volume', 'RSI_14', 'SMA_20', 'MACD', 'MACD_SIGNAL', 'MACD_HIST']
    
    # Verify specific columns exist
    assert 'RSI_14' in df.columns, "RSI_14 column missing!"
    assert 'SMA_20' in df.columns, "SMA_20 column missing!"
    assert 'MACD' in df.columns, "MACD column missing!"
    
    print("✅ All column names verified!")

if __name__ == "__main__":
    test_column_names()
```

---

## Summary

**The Golden Rules:**

1. ✅ OHLCV columns are capitalized: `Open`, `High`, `Low`, `Close`, `Volume`
2. ✅ Indicator columns include parameters: `RSI_14`, `SMA_20`, `EMA_50`
3. ✅ Multi-output indicators have suffixes: `MACD_SIGNAL`, `BBANDS_UPPER`
4. ✅ Always print `df.columns` after loading data
5. ✅ Use `.get()` for safe access: `row.get('RSI_14', None)`
6. ✅ Check for NaN values: `if pd.notna(value):`
7. ✅ Document column mappings in comments
8. ✅ Test your strategy with real data before deployment

**Remember:** When in doubt, print the columns and use the exact names!

```python
print(f"Available columns: {list(df.columns)}")
```

---

**Status:** ✅ Standard Active  
**Applies To:** All AI-generated strategies  
**Enforced By:** data_loader.py + indicator_calculator.py  
**Last Updated:** October 17, 2025
