# System Prompt Update Summary

**Date:** October 17, 2025  
**Update Version:** 2.0.0  
**Status:** ✅ Complete

---

## What Was Updated

The `SYSTEM_PROMPT.md` has been significantly enhanced with **standardized column naming conventions** for all AI-generated strategies.

---

## Key Changes

### 1. Standardized Column Naming Convention

**Rule:** All indicator columns MUST include their parameters in the name.

**Examples:**
- `RSI` with `timeperiod=14` → Column name: `RSI_14`
- `SMA` with `timeperiod=20` → Column name: `SMA_20`
- `MACD` with defaults → Column names: `MACD`, `MACD_SIGNAL`, `MACD_HIST`

### 2. New Documentation Sections Added

#### Section: "Column Naming Convention ⚠️ CRITICAL"
- Comprehensive table of all indicators and their column names
- Rules for single-output vs multi-output indicators
- Examples of parameter-free indicators

#### Section: "Handling Indicator Columns (MANDATORY PRACTICE)"
- ❌ Wrong patterns that will fail
- ✅ Correct patterns that work
- Best practices for checking columns
- Dynamic column name detection
- Summary table of all rules

#### Section: "AI Code Generation Guidelines"
- Step-by-step guide for generating strategies
- Mandatory column inspection workflow
- Column mapping documentation requirements
- Common mistakes to avoid
- Complete example with proper handling
- Pre-submission checklist

### 3. Updated Strategy Template

The main strategy template now includes:
- Explicit period and interval parameters
- Mandatory column verification with `print()`
- Exact column names in comments
- Proper handling of parameterized column names

### 4. Enhanced Examples Throughout

All code examples updated to:
- Show actual column names produced
- Include verification steps
- Demonstrate proper access patterns
- Handle NaN values correctly

---

## New Supporting Documents

### 1. `COLUMN_NAMING_STANDARD.md`
Comprehensive reference document covering:
- The complete standard
- Why it exists
- Usage examples for all indicators
- Best practices
- Testing strategies
- Complete indicator reference table

### 2. `QUICK_REFERENCE_COLUMNS.md`
Quick reference card for AI agents:
- One-page cheat sheet
- Common indicators table
- Correct vs wrong patterns
- Strategy template
- Pre-flight checklist

---

## Benefits

### For AI Code Generation
1. **Consistency** - All generated strategies follow same pattern
2. **Self-documenting** - Column names show parameters
3. **Debugging** - Easy to spot parameter mismatches
4. **Flexibility** - Can have multiple versions of same indicator

### For Developers
1. **Clear intent** - `RSI_14` vs `RSI_21` is explicit
2. **No confusion** - Always know which parameters were used
3. **Easy maintenance** - Column names match indicator configs
4. **Better testing** - Can verify exact indicator versions

### For System Reliability
1. **No KeyErrors** - Column names match what's in DataFrame
2. **Type safety** - Parameters are part of the contract
3. **Version control** - Changes to parameters visible in column names
4. **Audit trail** - Can trace back to exact indicator configuration

---

## Migration Path

### For Existing Strategies

**Option 1: Update column access (Recommended)**
```python
# Old
rsi = row['RSI']

# New
rsi = row['RSI_14']
```

**Option 2: Use column renaming**
```python
# After loading data
df = df.rename(columns={'RSI_14': 'RSI'})

# Then old code works
rsi = row['RSI']
```

### For New Strategies

All new strategies MUST:
1. Print `df.columns` after loading
2. Use exact parameterized column names
3. Document column mappings in comments
4. Pass the pre-flight checklist

---

## Testing

The update has been tested with:
- ✅ `rsi_strategy.py` - Updated and working
- ✅ `test_dynamic_data_loader.py` - All tests pass
- ✅ `data_loader.py` - Module verified

**Test command:**
```powershell
.\.venv\Scripts\python.exe Backtest\rsi_strategy.py
```

**Expected output:**
```
Loaded columns: ['Open', 'High', 'Low', 'Close', 'Volume', 'RSI_14']
```

---

## Documentation Structure

```
Backtest/
├── SYSTEM_PROMPT.md              ← Main AI prompt (UPDATED v2.0.0)
├── COLUMN_NAMING_STANDARD.md     ← Complete standard reference (NEW)
├── QUICK_REFERENCE_COLUMNS.md    ← Quick reference card (NEW)
├── data_loader.py                 ← Dynamic data loading (v2.0.0)
└── rsi_strategy.py                ← Example strategy (UPDATED)

Root/
├── DATA_LOADER_UPGRADE.md         ← Data loader changes
└── test_dynamic_data_loader.py    ← Test script
```

---

## Example: Before vs After

### Before (Ambiguous)

```python
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={'RSI': {'timeperiod': 14}}
)

# Which RSI? 14? 21? 30?
for timestamp, row in df.iterrows():
    rsi = row['RSI']  # ❌ Could be anything
```

### After (Explicit)

```python
df, metadata = load_market_data(
    ticker='AAPL',
    indicators={'RSI': {'timeperiod': 14}},
    period='1mo',
    interval='1d'
)

# Clear verification
print(f"Columns: {list(df.columns)}")
# Output: ['Open', 'High', 'Low', 'Close', 'Volume', 'RSI_14']

# Explicit and clear
for timestamp, row in df.iterrows():
    rsi_14 = row['RSI_14']  # ✅ Exactly RSI with 14-period
```

---

## Checklist for AI Agents

When generating strategy code, ensure:

- [ ] ✅ Used `load_market_data()` from data_loader
- [ ] ✅ Specified `period` and `interval` parameters
- [ ] ✅ Printed `df.columns` to verify names
- [ ] ✅ Used exact column names with parameters (e.g., `RSI_14`)
- [ ] ✅ Handled multi-output indicators (e.g., MACD → 3 columns)
- [ ] ✅ Added NaN checks for indicator values
- [ ] ✅ Used `.get()` for safe dictionary access
- [ ] ✅ Included column name comments
- [ ] ✅ Documented any renaming operations
- [ ] ✅ Tested with complete backtest run

---

## Implementation Timeline

- **Phase 1:** ✅ Update SYSTEM_PROMPT.md (Complete)
- **Phase 2:** ✅ Create supporting documentation (Complete)
- **Phase 3:** ✅ Update example strategies (Complete)
- **Phase 4:** ✅ Test with AI generation (Complete)
- **Phase 5:** 🔄 Roll out to all new strategies (Ongoing)

---

## Key Files Modified

1. **Backtest/SYSTEM_PROMPT.md**
   - Version updated to 2.0.0
   - Added column naming convention section
   - Enhanced all examples
   - Added AI generation guidelines

2. **Backtest/rsi_strategy.py**
   - Added column renaming after load
   - Now uses standardized approach

3. **New Documentation:**
   - `COLUMN_NAMING_STANDARD.md`
   - `QUICK_REFERENCE_COLUMNS.md`
   - `SYSTEM_PROMPT_UPDATE_SUMMARY.md` (this file)

---

## Next Steps

### For AI Strategy Generation
1. Use updated SYSTEM_PROMPT.md v2.0.0
2. Always include column verification
3. Follow the checklist
4. Test generated strategies

### For Human Developers
1. Review `COLUMN_NAMING_STANDARD.md`
2. Update existing strategies if needed
3. Use `QUICK_REFERENCE_COLUMNS.md` as guide
4. Report any issues or edge cases

---

## Support Resources

- **Main Documentation:** `Backtest/SYSTEM_PROMPT.md`
- **Standard Reference:** `Backtest/COLUMN_NAMING_STANDARD.md`
- **Quick Reference:** `Backtest/QUICK_REFERENCE_COLUMNS.md`
- **Example Strategy:** `Backtest/rsi_strategy.py`
- **Test Script:** `test_dynamic_data_loader.py`

---

## Conclusion

The SYSTEM_PROMPT.md has been successfully updated to version 2.0.0 with comprehensive **standardized column naming conventions**. This ensures:

✅ **Consistency** across all AI-generated strategies  
✅ **Clarity** in indicator parameter usage  
✅ **Reliability** with no ambiguous column names  
✅ **Maintainability** with self-documenting code  
✅ **Scalability** for future indicator additions  

All AI agents generating strategy code should now use the updated prompt and follow the established conventions.

---

**Status:** ✅ Update Complete  
**Version:** 2.0.0  
**Effective Date:** October 17, 2025  
**Last Updated:** October 17, 2025
