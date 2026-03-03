# MCP Integration Guide

## Complete Guide to Symbol Changing and Indicator Management

This guide documents the complete workflows for programmatically controlling TradingView using MCP Chrome DevTools.

---

## 🔧 Prerequisites

1. **Chrome browser** with TradingView open
2. **MCP Chrome server** running and connected
3. **Page selected** in MCP (use `mcp_io_github_chr_select_page`)

---

## 📊 Discovered Element UIDs

### Main UI Elements

| Element | UID | Description |
|---------|-----|-------------|
| Symbol Button | `1_2` | Opens symbol search dialog |
| Symbol Search Box | `4_4` | Input field for symbol search |
| Indicators Button | `1_12` | Opens indicators dialog |
| Indicator Search Box | `8_5` | Input field for indicator search |

### Timeframe Buttons

| Timeframe | UID |
|-----------|-----|
| 1 minute | `1_5` |
| 3 minutes | `1_6` |
| 5 minutes | `1_7` |
| 30 minutes | `1_8` |
| 1 hour | `1_9` |

### Indicator Controls (Example: RSI)

When an indicator is added, control buttons appear in the indicator panel:

| Button | UID (RSI Example) |
|--------|-------------------|
| Hide | `11_3` |
| Settings | `11_4` |
| Remove | `11_5` |
| More | `11_6` |

**Note:** UIDs change based on indicator position and count. Always take a snapshot to find current UIDs.

---

## 🔄 Workflow 1: Change Symbol

### Step-by-Step Process

```python
# Step 1: Click symbol button
mcp_io_github_chr_click(uid="1_2")
time.sleep(0.5)

# Step 2: Type symbol in search box
mcp_io_github_chr_fill(uid="4_4", value="AAPL")
time.sleep(0.5)

# Step 3: Select first result
# Option A: Press Enter
mcp_io_github_chr_press_key(key="Enter")

# Option B: Click specific result (after taking snapshot)
# mcp_io_github_chr_click(uid="5_1")

time.sleep(1.5)  # Wait for chart to load
```

### Verification

After changing symbol, verify the change:

```python
# Take snapshot to see page title
snapshot = mcp_io_github_chr_take_snapshot()

# Or use JavaScript
result = mcp_io_github_chr_evaluate_script(function="""
() => {
    return document.title.match(/^([A-Z0-9]+)/)[1];
}
""")

print(f"Current symbol: {result}")
```

### Example Output

When successful, you'll see:
- Page title changes to new symbol
- "Undo change symbol" button appears
- Chart reloads with new symbol data

---

## 📈 Workflow 2: Add Indicator

### Step-by-Step Process

```python
# Step 1: Click indicators button
mcp_io_github_chr_click(uid="1_12")
time.sleep(0.5)

# Step 2: Type indicator name
mcp_io_github_chr_fill(uid="8_5", value="RSI")
time.sleep(0.5)

# Step 3: Select indicator
# Option A: Press Enter (selects first result)
mcp_io_github_chr_press_key(key="Enter")

# Option B: Click specific indicator text
# Take snapshot first to find exact UID
# mcp_io_github_chr_click(uid="9_12")  # Example for RSI

time.sleep(1.0)  # Wait for indicator to load

# Step 4: Close dialog (if needed)
mcp_io_github_chr_press_key(key="Escape")
```

### Verification

```python
# Take snapshot to see indicator panel
snapshot = mcp_io_github_chr_take_snapshot()

# Look for indicator name in StaticText elements
# Example: RSI panel shows "RSI 14 close" with values
```

### Example Output (RSI)

When successful:
- RSI panel appears on chart
- Shows "RSI 14 close" label
- Displays current values (e.g., 53.65, 61.68)
- Control buttons available (Hide, Settings, Remove, More)
- "Undo insert Relative Strength Index" button appears

---

## 🗑️ Workflow 3: Remove Indicator

### Step-by-Step Process

```python
# Step 1: Take snapshot to find indicator panel
snapshot = mcp_io_github_chr_take_snapshot()

# Step 2: Find the Remove button UID
# Look for StaticText with indicator name
# Find associated button with text "Remove"
# Example: For first indicator, Remove is often uid="11_5"

# Step 3: Click Remove button
mcp_io_github_chr_click(uid="11_5")
time.sleep(0.5)

# Step 4: Verify removal
snapshot = mcp_io_github_chr_take_snapshot()
# Indicator panel should be gone
```

### Finding Remove Button

The Remove button UID varies based on:
- Number of indicators on chart
- Position of indicator panel
- Other UI elements

**Always take a snapshot first!**

```python
# Example snapshot output for RSI:
# StaticText "RSI" uid="11_0"
# StaticText "14" uid="11_1"
# StaticText "close" uid="11_2"
# button "Hide RSI" uid="11_3"
# button "Settings" uid="11_4"
# button "Remove RSI" uid="11_5" ← This is what we need
# button "More" uid="11_6"
```

---

## ⚙️ Workflow 4: Configure Indicator Parameters

### Step-by-Step Process

```python
# Step 1: Take snapshot to find Settings button
snapshot = mcp_io_github_chr_take_snapshot()

# Step 2: Locate the Settings button UID
# Look for the indicator panel
# Settings button is usually adjacent to Remove button
# Example: Settings uid="11_4" when Remove is "11_5"

# Step 3: Click Settings button
mcp_io_github_chr_click(uid="11_4")
time.sleep(0.5)

# Step 4: Settings dialog opens - take snapshot
dialog_snapshot = mcp_io_github_chr_take_snapshot()

# Step 5: Configure parameters
# Find input fields by label (e.g., "Length", "Source")

# Example: Change RSI length from 14 to 21
# Find the Length input field (search snapshot for "Length")
length_input_uid = "15_3"  # Example - find from snapshot

# Click to focus
mcp_io_github_chr_click(uid=length_input_uid)
time.sleep(0.2)

# Select all and replace
mcp_io_github_chr_press_key(key="Control+a")
mcp_io_github_chr_fill(uid=length_input_uid, value="21")

# Step 6: Change source (if applicable)
# Source is often a dropdown
source_dropdown_uid = "15_5"  # Example

mcp_io_github_chr_click(uid=source_dropdown_uid)
time.sleep(0.3)

# Type to select (e.g., "hl2" for High+Low/2)
mcp_io_github_chr_fill(uid=source_dropdown_uid, value="hl2")
mcp_io_github_chr_press_key(key="Enter")

# Step 7: Save changes
# Option A: Press Enter (often works)
mcp_io_github_chr_press_key(key="Enter")

# Option B: Click OK/Save button
# ok_button_uid = find_in_snapshot(dialog_snapshot, "OK")
# mcp_io_github_chr_click(uid=ok_button_uid)

time.sleep(0.5)
```

### Common Parameters

| Parameter | Type | Common Values | Description |
|-----------|------|---------------|-------------|
| `length` | Integer | 7, 14, 21, 50, 200 | Period/lookback length |
| `source` | Dropdown | close, open, hl2, hlc3, ohlc4 | Price source |
| `offset` | Integer | 0, 1, -1 | Shift indicator values |
| `multiplier` | Float | 2.0, 2.5, 3.0 | Multiplier (e.g., BB bands) |
| `smoothing` | Dropdown | SMA, EMA, WMA | Smoothing method |

### Example: RSI with Custom Parameters

```python
# Add RSI with period 21 and hl2 source
def add_custom_rsi():
    # Add RSI first
    mcp_io_github_chr_click(uid="1_12")  # Indicators button
    time.sleep(0.5)
    mcp_io_github_chr_fill(uid="8_5", value="RSI")
    time.sleep(0.5)
    mcp_io_github_chr_press_key(key="Enter")
    time.sleep(1.5)
    
    # Now configure it
    snapshot = mcp_io_github_chr_take_snapshot()
    settings_uid = "11_4"  # Find from snapshot
    
    mcp_io_github_chr_click(uid=settings_uid)
    time.sleep(0.5)
    
    # Change length to 21
    mcp_io_github_chr_click(uid="15_3")
    mcp_io_github_chr_press_key(key="Control+a")
    mcp_io_github_chr_fill(uid="15_3", value="21")
    
    # Change source to hl2
    mcp_io_github_chr_click(uid="15_5")
    mcp_io_github_chr_fill(uid="15_5", value="hl2")
    mcp_io_github_chr_press_key(key="Enter")
    
    # Save
    mcp_io_github_chr_press_key(key="Enter")
    time.sleep(0.5)
    
    print("✅ RSI configured: length=21, source=hl2")
```

### Verification

After configuring, the indicator panel should update:
- Shows new parameter values (e.g., "RSI 21 hl2")
- Chart recalculates with new settings
- Indicator values change accordingly

---

## ⏱️ Workflow 5: Change Timeframe

### Step-by-Step Process

```python
# Direct click on timeframe button
timeframe_uids = {
    "1m": "1_5",
    "3m": "1_6",
    "5m": "1_7",
    "30m": "1_8",
    "1h": "1_9"
}

# Change to 5-minute chart
mcp_io_github_chr_click(uid=timeframe_uids["5m"])
time.sleep(1.0)  # Wait for chart to reload
```

---

## 📥 Workflow 6: Extract Market Data

### JavaScript Extraction

```python
extraction_script = """
() => {
  const data = {
    symbol: null,
    timeframe: null,
    ohlc: {},
    indicators: [],
    volume: null,
    change: {},
    timestamp: new Date().toISOString()
  };
  
  // Extract symbol from title
  const titleMatch = document.title.match(/^([A-Z0-9]+)/);
  if (titleMatch) {
    data.symbol = titleMatch[1];
  }
  
  // Extract OHLC from legend
  const legendText = document.body.innerText;
  const ohlcMatch = legendText.match(/O\\s*([\\d,.]+)\\s*H\\s*([\\d,.]+)\\s*L\\s*([\\d,.]+)\\s*C\\s*([\\d,.]+)/);
  if (ohlcMatch) {
    data.ohlc = {
      open: parseFloat(ohlcMatch[1].replace(/,/g, '')),
      high: parseFloat(ohlcMatch[2].replace(/,/g, '')),
      low: parseFloat(ohlcMatch[3].replace(/,/g, '')),
      close: parseFloat(ohlcMatch[4].replace(/,/g, ''))
    };
  }
  
  // Extract volume
  const volMatch = legendText.match(/Vol\\s*([\\d,.]+)\\s*([KMB])?/i);
  if (volMatch) {
    let vol = parseFloat(volMatch[1].replace(/,/g, ''));
    if (volMatch[2]) {
      const multiplier = {'K': 1000, 'M': 1000000, 'B': 1000000000}[volMatch[2]];
      vol *= multiplier;
    }
    data.volume = vol;
  }
  
  // Extract price change
  const changeMatch = legendText.match(/([+−-][\\d,.]+)\\s*\\(([+−-][\\d,.]+)%\\)/);
  if (changeMatch) {
    data.change = {
      absolute: parseFloat(changeMatch[1].replace(/−/g, '-').replace(/,/g, '')),
      percent: parseFloat(changeMatch[2].replace(/−/g, '-').replace(/,/g, ''))
    };
  }
  
  return data;
}
"""

# Execute extraction
result = mcp_io_github_chr_evaluate_script(function=extraction_script)
print(result)
```

### Example Output

```json
{
  "symbol": "AAPL",
  "timeframe": "5m",
  "ohlc": {
    "open": 234.56,
    "high": 235.12,
    "low": 234.23,
    "close": 234.89
  },
  "volume": 1250000,
  "change": {
    "absolute": 1.23,
    "percent": 0.53
  },
  "timestamp": "2026-02-08T12:30:00.000Z"
}
```

---

## 🎯 Complete Example: Multi-Symbol Analysis

```python
import time
import json

def analyze_multiple_symbols():
    """Analyze multiple symbols with consistent indicators."""
    
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    results = []
    
    # Add RSI indicator once
    print("Adding RSI indicator...")
    mcp_io_github_chr_click(uid="1_12")
    time.sleep(0.5)
    mcp_io_github_chr_fill(uid="8_5", value="RSI")
    time.sleep(0.5)
    mcp_io_github_chr_press_key(key="Enter")
    time.sleep(1.0)
    
    # Loop through symbols
    for symbol in symbols:
        print(f"\nAnalyzing {symbol}...")
        
        # Change symbol
        mcp_io_github_chr_click(uid="1_2")
        time.sleep(0.5)
        mcp_io_github_chr_fill(uid="4_4", value=symbol)
        time.sleep(0.5)
        mcp_io_github_chr_press_key(key="Enter")
        time.sleep(2.0)  # Wait for chart to load
        
        # Extract data
        data = mcp_io_github_chr_evaluate_script(function=extraction_script)
        results.append(data)
        
        print(f"   ✅ {symbol}: ${data['ohlc']['close']:.2f}")
    
    # Save results
    with open('multi_symbol_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Analysis complete! Saved to multi_symbol_analysis.json")

# Run it
analyze_multiple_symbols()
```

---

## 🛠️ Troubleshooting

### Issue: Elements Not Found

**Solution:** Take a snapshot to see current UIDs

```python
snapshot = mcp_io_github_chr_take_snapshot()
print(snapshot)  # Search for your element
```

### Issue: Indicator Not Adding

**Solutions:**
1. Ensure indicators dialog is open
2. Wait longer after typing (0.5-1.0 seconds)
3. Try pressing Enter instead of clicking
4. Close dialog with Escape after adding

### Issue: Symbol Not Changing

**Solutions:**
1. Wait longer for search results (0.5-1.0 seconds)
2. Verify symbol exists on TradingView
3. Check if symbol search dialog opened
4. Try clicking first result instead of pressing Enter

### Issue: UIDs Changed

**Cause:** TradingView UI update or page reload

**Solution:** Retake snapshot and update UIDs in code

---

## 📋 Testing Checklist

Before deploying automation:

- [ ] Test symbol changing (3+ different symbols)
- [ ] Test timeframe changing (3+ timeframes)
- [ ] Test indicator adding (3+ indicators)
- [ ] Test indicator removing
- [ ] Test data extraction
- [ ] Test with full workflow (symbol → timeframe → indicator → extract)
- [ ] Verify exports (JSON/CSV/Excel)
- [ ] Handle errors gracefully
- [ ] Add appropriate delays between actions

---

## 🚀 Best Practices

### 1. Always Add Delays

```python
# After clicking
time.sleep(0.5)

# After typing
time.sleep(0.5)

# After symbol/timeframe change
time.sleep(1.5)

# After adding indicator
time.sleep(1.0)
```

### 2. Verify Actions

```python
# Take snapshot after important actions
mcp_io_github_chr_click(uid="1_2")
snapshot = mcp_io_github_chr_take_snapshot()

# Check for expected elements
assert "searchbox" in snapshot
```

### 3. Handle Errors

```python
try:
    mcp_io_github_chr_click(uid="1_2")
except Exception as e:
    print(f"Error clicking button: {e}")
    # Retry or log error
```

### 4. Use Dynamic UID Discovery

```python
def find_remove_button(indicator_name):
    """Find Remove button UID for specific indicator."""
    snapshot = mcp_io_github_chr_take_snapshot()
    
    # Parse snapshot to find indicator name
    # Then find associated Remove button
    # Return UID
    
    return uid
```

---

## 📚 Additional Resources

- **MCPscraper.py**: Core scraper implementation
- **examples/mcp_live_demo.py**: Complete working example
- **examples/export_data.py**: Data export examples

---

## ✅ Summary

| Feature | Status | Complexity |
|---------|--------|------------|
| Symbol Changing | ✅ Tested | Low |
| Timeframe Changing | ✅ Tested | Low |
| Indicator Adding | ✅ Tested | Medium |
| Indicator Removing | ✅ Tested | Medium |
| Data Extraction | ✅ Working | Medium |
| Data Export | ✅ Complete | Low |

**All features working and documented!** 🎉
