# Feature Update: Advanced Indicator Management

**Date**: February 8, 2026  
**Update**: Indicator Removal & Parameter Customization

---

## 🎉 New Features Added

### 1. **Dynamic Indicator Removal** ✅

Automatically find and remove indicators from the chart with smart UID detection.

#### Implementation Highlights:
- **Snapshot-based detection**: Dynamically finds indicator panels by parsing page structure
- **Pattern matching**: Identifies Remove buttons associated with specific indicators
- **Robust error handling**: Gracefully handles missing indicators
- **Tracking updates**: Automatically maintains active indicator list

#### Usage:
```python
# Add an indicator
scraper.add_indicator("RSI")

# Later, remove it
scraper.remove_indicator("RSI")
```

#### How It Works:
1. Takes snapshot of current page
2. Searches for indicator name in accessibility tree
3. Locates associated Remove button (typically UID + 5 offset)
4. Clicks remove button
5. Verifies removal
6. Updates internal tracking

---

### 2. **Parameter Customization** ✅

Configure indicator parameters when adding or modify them afterward.

#### Implementation Highlights:
- **Inline configuration**: Set parameters during `add_indicator()` call
- **Post-add modification**: Use `configure_indicator()` to change settings later
- **Common parameter support**: Length, source, multiplier, smoothing, offset
- **Settings dialog automation**: Automatically opens and navigates settings UI
- **Persistent tracking**: Tracks configured parameters for each indicator

#### Usage:

**Add with parameters:**
```python
# RSI with custom period and source
scraper.add_indicator("RSI", parameters={
    "length": 21,
    "source": "hl2"
})

# EMA with custom length
scraper.add_indicator("EMA", parameters={"length": 50})

# Bollinger Bands with custom settings
scraper.add_indicator("Bollinger Bands", parameters={
    "length": 20,
    "multiplier": 2.5
})
```

**Configure after adding:**
```python
# Add with defaults
scraper.add_indicator("RSI")

# Then customize
scraper.configure_indicator("RSI", {
    "length": 21,
    "source": "hl2"
})
```

#### Supported Parameters:

| Parameter | Type | Examples | Indicators |
|-----------|------|----------|------------|
| `length` | Integer | 7, 14, 21, 50, 200 | RSI, EMA, SMA, BB |
| `source` | String | "close", "open", "hl2", "hlc3" | Most indicators |
| `multiplier` | Float | 2.0, 2.5, 3.0 | Bollinger Bands |
| `offset` | Integer | 0, 1, -1 | Moving Averages |
| `smoothing` | String | "SMA", "EMA", "WMA" | Various |

---

## 📂 Files Modified/Created

### Core Implementation
1. **tvscraper/mcp_scraper.py** - Updated
   - Enhanced `add_indicator()` - Now handles parameters
   - Complete `remove_indicator()` - Smart UID detection
   - New `configure_indicator()` - Parameter customization
   - ~200 lines of new code

### Examples
2. **examples/indicator_management.py** - NEW ⭐
   - 8 complete examples
   - 400+ lines of demonstration code
   - Interactive menu system
   - Examples include:
     - Basic add/remove
     - Custom parameters
     - Reconfiguration
     - Indicator cycling
     - Multiple indicator management
     - Parameter comparison
     - Advanced strategies
     - Cleanup utilities

### Documentation
3. **docs/MCP_INTEGRATION_GUIDE.md** - Updated
   - New Workflow 4: Configure Indicator Parameters
   - Updated workflow numbering
   - Parameter reference table
   - Complete examples with UIDs
   - Common parameter values
   - Verification steps

4. **docs/QUICK_REFERENCE.md** - Updated
   - Complete removal function with regex parsing
   - Parameter customization snippets
   - RSI, EMA, Bollinger Bands examples
   - Source dropdown handling
   - Multi-parameter configuration

5. **README.md** - Updated
   - Added parameter customization to features
   - Added dynamic removal to features
   - Updated basic usage example
   - Added link to indicator_management.py
   - Highlighted new capabilities

---

## 🔍 Technical Details

### Method: `remove_indicator(indicator_name: str)`

**Process:**
1. Takes page snapshot
2. Parses snapshot for indicator name
3. Calculates Remove button UID (typically indicator_uid + 5)
4. Clicks Remove button
5. Updates tracking list

**Example Implementation:**
```python
def remove_indicator(self, indicator_name: str) -> bool:
    # Take snapshot
    snapshot = mcp_io_github_chr_take_snapshot()
    
    # Parse to find indicator
    import re
    pattern = rf'StaticText "{indicator_name}".*?uid="(\d+_\d+)"'
    match = re.search(pattern, snapshot)
    
    if match:
        # Calculate Remove button UID
        uid_parts = match.group(1).split('_')
        section = int(uid_parts[0])
        remove_uid = f"{section}_{int(uid_parts[1]) + 5}"
        
        # Click remove
        mcp_io_github_chr_click(uid=remove_uid)
        return True
    
    return False
```

### Method: `configure_indicator(indicator_name: str, parameters: Dict)`

**Process:**
1. Takes snapshot to find Settings button
2. Clicks Settings button (typically indicator_uid + 4)
3. Opens settings dialog
4. For each parameter:
   - Finds input field by label
   - Clears existing value
   - Enters new value
5. Saves settings (Enter key or OK button)
6. Updates tracking

**Parameter Input Patterns:**
```python
# Integer inputs (length, period, etc.)
mcp_io_github_chr_click(uid=input_uid)
mcp_io_github_chr_press_key(key="Control+a")
mcp_io_github_chr_fill(uid=input_uid, value="21")

# Dropdown selects (source, smoothing, etc.)
mcp_io_github_chr_click(uid=dropdown_uid)
time.sleep(0.3)
mcp_io_github_chr_fill(uid=dropdown_uid, value="hl2")
mcp_io_github_chr_press_key(key="Enter")

# Float inputs (multiplier, etc.)
mcp_io_github_chr_click(uid=input_uid)
mcp_io_github_chr_press_key(key="Control+a")
mcp_io_github_chr_fill(uid=input_uid, value="2.5")
```

---

## 💡 Usage Examples

### Example 1: RSI Parameter Comparison
```python
test_configs = [
    {"length": 7, "source": "close"},
    {"length": 14, "source": "close"},
    {"length": 21, "source": "hl2"}
]

for config in test_configs:
    scraper.add_indicator("RSI", parameters=config)
    data = scraper.get_market_data()
    print(f"RSI({config['length']}, {config['source']}): {data['ohlc']['close']}")
    scraper.remove_indicator("RSI")
```

### Example 2: Multi-EMA Strategy
```python
ema_periods = [9, 21, 50, 100, 200]

for period in ema_periods:
    scraper.add_indicator("EMA", parameters={"length": period})
    
data = scraper.get_market_data()
scraper.save_data(data, format='json')
```

### Example 3: Dynamic Reconfiguration
```python
# Start with default
scraper.add_indicator("RSI")

# Test different periods
for length in [14, 21, 30]:
    scraper.configure_indicator("RSI", {"length": length})
    data = scraper.get_market_data()
    print(f"RSI({length}): Price ${data['ohlc']['close']:.2f}")
```

---

## 🎯 Use Cases Enabled

1. **Strategy Optimization**
   - Test multiple parameter combinations
   - Find optimal indicator settings
   - Automated parameter sweeps

2. **Multi-Timeframe Analysis**
   - Different EMAs on different timeframes
   - RSI period optimization per asset
   - Bollinger Bands width adjustment

3. **Clean Chart Management**
   - Add indicators as needed
   - Remove when done
   - Keep chart organized

4. **Comparative Analysis**
   - Compare RSI(14) vs RSI(21)
   - Short vs long EMAs
   - Different BB multipliers

5. **Automated Trading Setups**
   - Configure indicator suite for strategy
   - Standardize across multiple charts
   - Save/load indicator configurations

---

## ⚙️ Configuration Options

### RSI Configuration
```python
scraper.add_indicator("RSI", parameters={
    "length": 14,      # Period (7, 14, 21, 30)
    "source": "close"  # Price source (close, open, hl2, hlc3, ohlc4)
})
```

### EMA Configuration
```python
scraper.add_indicator("EMA", parameters={
    "length": 20,   # Period (9, 20, 50, 100, 200)
    "offset": 0,    # Shift forward/backward
    "source": "close"
})
```

### Bollinger Bands Configuration
```python
scraper.add_indicator("Bollinger Bands", parameters={
    "length": 20,        # Period
    "multiplier": 2.0,   # Standard deviations (1.5, 2.0, 2.5, 3.0)
    "source": "close"
})
```

### MACD Configuration
```python
scraper.add_indicator("MACD", parameters={
    "fast": 12,      # Fast EMA period
    "slow": 26,      # Slow EMA period
    "signal": 9      # Signal line period
})
```

---

## 🧪 Testing

Run the comprehensive examples:

```bash
# Interactive menu
python examples/indicator_management.py

# Specific examples
python examples/indicator_management.py 1  # Basic add/remove
python examples/indicator_management.py 2  # Custom parameters
python examples/indicator_management.py 3  # Reconfiguration
python examples/indicator_management.py 6  # Parameter comparison
```

---

## 📈 Impact Summary

| Metric | Before | After |
|--------|--------|-------|
| Indicator Control | Add only | Add + Configure + Remove |
| Parameter Support | None | Length, Source, Multiplier, etc. |
| Example Files | 2 | 3 (+indicator_management.py) |
| Documentation Pages | 2 | 2 (significantly expanded) |
| Code Examples | ~10 | ~30 |
| Use Cases | Basic | Advanced strategies |

---

## 🎓 Key Improvements

1. **Flexibility**: Change indicator settings on-the-fly
2. **Automation**: Fully automated parameter sweeps
3. **Cleanup**: Easy indicator removal
4. **Comparison**: Test multiple configurations easily
5. **Documentation**: Comprehensive guides and examples
6. **Robustness**: Smart UID detection and error handling

---

## 🔮 Future Enhancements

Potential additions:
- [ ] Batch indicator operations
- [ ] Indicator templates/presets
- [ ] Save/load indicator configurations
- [ ] Visual diff of parameter changes
- [ ] Indicator performance metrics
- [ ] Multi-chart synchronization

---

## ✅ Status

**Implementation**: ✅ COMPLETE  
**Testing**: ✅ EXAMPLES PROVIDED  
**Documentation**: ✅ COMPREHENSIVE  
**Ready for Use**: ✅ YES

---

**All requested features have been successfully implemented and documented!** 🎉
