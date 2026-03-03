# Quick Reference Guide

## Essential MCP Chrome Tool Calls for TradingView

Use this as a quick reference for common operations.

---

## 🔄 Change Symbol

### AAPL (Apple Stock)
```python
mcp_io_github_chr_click(uid="1_2")
time.sleep(0.5)
mcp_io_github_chr_fill(uid="4_4", value="AAPL")
time.sleep(0.5)
mcp_io_github_chr_press_key(key="Enter")
time.sleep(1.5)
```

### EURUSD (Forex)
```python
mcp_io_github_chr_click(uid="1_2")
time.sleep(0.5)
mcp_io_github_chr_fill(uid="4_4", value="EURUSD")
time.sleep(0.5)
mcp_io_github_chr_press_key(key="Enter")
time.sleep(1.5)
```

### BTCUSD (Crypto)
```python
mcp_io_github_chr_click(uid="1_2")
time.sleep(0.5)
mcp_io_github_chr_fill(uid="4_4", value="BTCUSD")
time.sleep(0.5)
mcp_io_github_chr_press_key(key="Enter")
time.sleep(1.5)
```

---

## ⏱️ Change Timeframe

### 5-Minute Chart
```python
mcp_io_github_chr_click(uid="1_7")
time.sleep(1.0)
```

### 1-Hour Chart
```python
mcp_io_github_chr_click(uid="1_9")
time.sleep(1.0)
```

### 30-Minute Chart
```python
mcp_io_github_chr_click(uid="1_8")
time.sleep(1.0)
```

---

## 📈 Add Indicators

### RSI (Relative Strength Index)
```python
mcp_io_github_chr_click(uid="1_12")
time.sleep(0.5)
mcp_io_github_chr_fill(uid="8_5", value="RSI")
time.sleep(0.5)
mcp_io_github_chr_press_key(key="Enter")
time.sleep(1.0)
mcp_io_github_chr_press_key(key="Escape")  # Close dialog
```

### MACD
```python
mcp_io_github_chr_click(uid="1_12")
time.sleep(0.5)
mcp_io_github_chr_fill(uid="8_5", value="MACD")
time.sleep(0.5)
mcp_io_github_chr_press_key(key="Enter")
time.sleep(1.0)
mcp_io_github_chr_press_key(key="Escape")
```

### EMA (Exponential Moving Average)
```python
mcp_io_github_chr_click(uid="1_12")
time.sleep(0.5)
mcp_io_github_chr_fill(uid="8_5", value="EMA")
time.sleep(0.5)
mcp_io_github_chr_press_key(key="Enter")
time.sleep(1.0)
mcp_io_github_chr_press_key(key="Escape")
```

### Bollinger Bands
```python
mcp_io_github_chr_click(uid="1_12")
time.sleep(0.5)
mcp_io_github_chr_fill(uid="8_5", value="Bollinger Bands")
time.sleep(0.5)
mcp_io_github_chr_press_key(key="Enter")
time.sleep(1.0)
mcp_io_github_chr_press_key(key="Escape")
```

---

## 🗑️ Remove Indicator

### Step 1: Find Remove Button UID
```python
# Take snapshot
snapshot = mcp_io_github_chr_take_snapshot()

# Search snapshot for:
# - StaticText matching indicator name
# - Button with "Remove" text
# - Note the UID (e.g., "11_5")
```

### Step 2: Click Remove
```python
# Example for first indicator (RSI)
mcp_io_github_chr_click(uid="11_5")
time.sleep(0.5)
```

### Complete Removal Function
```python
def remove_indicator_by_name(indicator_name):
    """
    Find and remove an indicator by parsing snapshot.
    """
    import re
    
    # Take snapshot
    snapshot = mcp_io_github_chr_take_snapshot()
    
    # Find indicator and remove button
    # Pattern: Find "RSI" text, then look for nearby Remove button
    pattern = rf'StaticText "{indicator_name}".*?uid="(\d+_\d+)"'
    match = re.search(pattern, snapshot)
    
    if match:
        uid_parts = match.group(1).split('_')
        section = int(uid_parts[0])
        
        # Remove button typically at offset +5
        remove_uid = f"{section}_{int(uid_parts[1]) + 5}"
        
        # Click remove
        mcp_io_github_chr_click(uid=remove_uid)
        time.sleep(0.5)
        print(f"Removed {indicator_name}")
        return True
    
    print(f"Could not find {indicator_name}")
    return False

# Usage
remove_indicator_by_name("RSI")
```

---

## ⚙️ Configure Indicator Parameters

### Basic Parameter Change
```python
# Step 1: Find and click Settings button
snapshot = mcp_io_github_chr_take_snapshot()
# Look for Settings button (usually uid="11_4" for first indicator)
settings_uid = "11_4"

mcp_io_github_chr_click(uid=settings_uid)
time.sleep(0.5)

# Step 2: Modify parameter (e.g., Length)
# Take snapshot of settings dialog
dialog_snapshot = mcp_io_github_chr_take_snapshot()
# Find "Length" input field

length_input_uid = "15_3"  # Find from snapshot

# Change value
mcp_io_github_chr_click(uid=length_input_uid)
time.sleep(0.2)
mcp_io_github_chr_press_key(key="Control+a")
mcp_io_github_chr_fill(uid=length_input_uid, value="21")

# Step 3: Save
mcp_io_github_chr_press_key(key="Enter")
time.sleep(0.5)
```

### RSI: Change Length to 21
```python
# After adding RSI, configure it
mcp_io_github_chr_click(uid="11_4")  # Settings
time.sleep(0.5)

mcp_io_github_chr_click(uid="15_3")  # Length input
mcp_io_github_chr_press_key(key="Control+a")
mcp_io_github_chr_fill(uid="15_3", value="21")

mcp_io_github_chr_press_key(key="Enter")  # Save
time.sleep(0.5)
```

### EMA: Change Length to 50
```python
mcp_io_github_chr_click(uid="11_4")  # Settings
time.sleep(0.5)

mcp_io_github_chr_click(uid="15_3")  # Length input
mcp_io_github_chr_press_key(key="Control+a")
mcp_io_github_chr_fill(uid="15_3", value="50")

mcp_io_github_chr_press_key(key="Enter")
time.sleep(0.5)
```

### RSI: Change Source to hl2
```python
mcp_io_github_chr_click(uid="11_4")  # Settings
time.sleep(0.5)

# Source dropdown
mcp_io_github_chr_click(uid="15_5")
time.sleep(0.3)
mcp_io_github_chr_fill(uid="15_5", value="hl2")
mcp_io_github_chr_press_key(key="Enter")

mcp_io_github_chr_press_key(key="Enter")  # Save settings
time.sleep(0.5)
```

### Bollinger Bands: Custom Parameters
```python
# Add BB first, then configure
mcp_io_github_chr_click(uid="1_12")
time.sleep(0.5)
mcp_io_github_chr_fill(uid="8_5", value="Bollinger Bands")
time.sleep(0.5)
mcp_io_github_chr_press_key(key="Enter")
time.sleep(1.5)

# Open settings
mcp_io_github_chr_click(uid="11_4")
time.sleep(0.5)

# Length = 20
mcp_io_github_chr_click(uid="15_3")
mcp_io_github_chr_press_key(key="Control+a")
mcp_io_github_chr_fill(uid="15_3", value="20")

# Multiplier = 2.5
mcp_io_github_chr_click(uid="15_7")
mcp_io_github_chr_press_key(key="Control+a")
mcp_io_github_chr_fill(uid="15_7", value="2.5")

# Save
mcp_io_github_chr_press_key(key="Enter")
time.sleep(0.5)
```

---

## 📊 Extract Data

### Complete Data Extraction
```python
extraction_script = """
() => {
  const data = {
    symbol: document.title.match(/^([A-Z0-9]+)/)?.[1] || null,
    timestamp: new Date().toISOString(),
    ohlc: {},
    volume: null,
    change: {}
  };
  
  const text = document.body.innerText;
  
  // OHLC
  const ohlc = text.match(/O\\s*([\\d,.]+)\\s*H\\s*([\\d,.]+)\\s*L\\s*([\\d,.]+)\\s*C\\s*([\\d,.]+)/);
  if (ohlc) {
    data.ohlc = {
      open: parseFloat(ohlc[1].replace(/,/g, '')),
      high: parseFloat(ohlc[2].replace(/,/g, '')),
      low: parseFloat(ohlc[3].replace(/,/g, '')),
      close: parseFloat(ohlc[4].replace(/,/g, ''))
    };
  }
  
  // Volume
  const vol = text.match(/Vol\\s*([\\d,.]+)\\s*([KMB])?/i);
  if (vol) {
    let v = parseFloat(vol[1].replace(/,/g, ''));
    if (vol[2]) {
      const m = {'K': 1000, 'M': 1000000, 'B': 1000000000}[vol[2]];
      v *= m;
    }
    data.volume = v;
  }
  
  // Change
  const chg = text.match(/([+−-][\\d,.]+)\\s*\\(([+−-][\\d,.]+)%\\)/);
  if (chg) {
    data.change = {
      absolute: parseFloat(chg[1].replace(/−/g, '-').replace(/,/g, '')),
      percent: parseFloat(chg[2].replace(/−/g, '-').replace(/,/g, ''))
    };
  }
  
  return data;
}
"""

result = mcp_io_github_chr_evaluate_script(function=extraction_script)
print(result)
```

### Just Get Symbol
```python
result = mcp_io_github_chr_evaluate_script(function="""
() => document.title.match(/^([A-Z0-9]+)/)?.[1]
""")
```

### Just Get Current Price
```python
result = mcp_io_github_chr_evaluate_script(function="""
() => {
  const match = document.body.innerText.match(/C\\s*([\\d,.]+)/);
  return match ? parseFloat(match[1].replace(/,/g, '')) : null;
}
""")
```

---

## 📸 Take Snapshot

### Full Snapshot
```python
snapshot = mcp_io_github_chr_take_snapshot()
print(snapshot)
```

### Search Snapshot for Element
```python
snapshot = mcp_io_github_chr_take_snapshot()

# Look for specific text
if "RSI" in snapshot:
    print("RSI indicator is visible")

# Parse to find UID
import re
matches = re.findall(r'uid="(\d+_\d+)".*?Remove', snapshot)
print(f"Remove button UID: {matches[0]}")
```

---

## 🔄 Common Workflows

### Workflow 1: Quick Analysis
```python
# Change symbol
mcp_io_github_chr_click(uid="1_2")
time.sleep(0.5)
mcp_io_github_chr_fill(uid="4_4", value="AAPL")
time.sleep(0.5)
mcp_io_github_chr_press_key(key="Enter")
time.sleep(1.5)

# Change timeframe to 5m
mcp_io_github_chr_click(uid="1_7")
time.sleep(1.0)

# Add RSI
mcp_io_github_chr_click(uid="1_12")
time.sleep(0.5)
mcp_io_github_chr_fill(uid="8_5", value="RSI")
time.sleep(0.5)
mcp_io_github_chr_press_key(key="Enter")
time.sleep(1.0)
mcp_io_github_chr_press_key(key="Escape")

# Extract data
data = mcp_io_github_chr_evaluate_script(function=extraction_script)
print(data)
```

### Workflow 2: Multi-Symbol Scan
```python
import time

symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]
results = []

for symbol in symbols:
    # Change symbol
    mcp_io_github_chr_click(uid="1_2")
    time.sleep(0.5)
    mcp_io_github_chr_fill(uid="4_4", value=symbol)
    time.sleep(0.5)
    mcp_io_github_chr_press_key(key="Enter")
    time.sleep(2.0)
    
    # Extract
    data = mcp_io_github_chr_evaluate_script(function=extraction_script)
    results.append(data)
    
    print(f"{symbol}: ${data['ohlc']['close']:.2f}")

# Save results
import json
with open('scan_results.json', 'w') as f:
    json.dump(results, f, indent=2)
```

### Workflow 3: Indicator Comparison
```python
# Add multiple indicators
indicators = ["RSI", "MACD", "EMA"]

for ind in indicators:
    mcp_io_github_chr_click(uid="1_12")
    time.sleep(0.5)
    mcp_io_github_chr_fill(uid="8_5", value=ind)
    time.sleep(0.5)
    mcp_io_github_chr_press_key(key="Enter")
    time.sleep(1.0)
    mcp_io_github_chr_press_key(key="Escape")
    print(f"Added {ind}")

# Take snapshot to see all indicators
snapshot = mcp_io_github_chr_take_snapshot()
print(snapshot)
```

---

## 🎯 Element UID Reference

| Element | UID | Type |
|---------|-----|------|
| Symbol Button | `1_2` | button |
| Symbol Search Input | `4_4` | searchbox |
| Timeframe 1m | `1_5` | radio button |
| Timeframe 3m | `1_6` | radio button |
| Timeframe 5m | `1_7` | radio button |
| Timeframe 30m | `1_8` | radio button |
| Timeframe 1h | `1_9` | radio button |
| Indicators Button | `1_12` | button |
| Indicator Search Input | `8_5` | searchbox |

**Note:** Indicator control button UIDs (Hide, Settings, Remove) vary based on position. Always take a snapshot to find current UIDs.

---

## ⚠️ Important Notes

### Timing Guidelines
- After click: **0.5 seconds**
- After fill: **0.5 seconds**
- After symbol change: **1.5-2.0 seconds**
- After timeframe change: **1.0 second**
- After indicator add: **1.0 second**

### Error Prevention
1. Always wait after actions
2. Verify elements exist before clicking
3. Handle connection errors
4. Use try/except blocks
5. Log all actions for debugging

### Best Practices
1. Take snapshots to verify state
2. Use descriptive variable names
3. Add comments explaining UIDs
4. Test each step individually
5. Save results incrementally

---

## 🔍 Debugging Commands

### Check Current Page
```python
result = mcp_io_github_chr_evaluate_script(function="""
() => ({
  title: document.title,
  url: window.location.href,
  loaded: document.readyState
})
""")
```

### List All Buttons
```python
result = mcp_io_github_chr_evaluate_script(function="""
() => {
  const buttons = Array.from(document.querySelectorAll('button'));
  return buttons.map(b => b.textContent.trim()).filter(t => t);
}
""")
```

### Find Element by Text
```python
result = mcp_io_github_chr_evaluate_script(function="""
() => {
  const el = Array.from(document.querySelectorAll('*'))
    .find(e => e.textContent.includes('Indicators'));
  return el ? el.outerHTML : null;
}
""")
```

---

## 📝 Template Script

```python
#!/usr/bin/env python3
"""
TradingView MCP Automation Template
"""

import time


def main():
    # 1. Change symbol
    print("Changing symbol...")
    mcp_io_github_chr_click(uid="1_2")
    time.sleep(0.5)
    mcp_io_github_chr_fill(uid="4_4", value="AAPL")
    time.sleep(0.5)
    mcp_io_github_chr_press_key(key="Enter")
    time.sleep(1.5)
    
    # 2. Change timeframe
    print("Changing timeframe...")
    mcp_io_github_chr_click(uid="1_7")  # 5m
    time.sleep(1.0)
    
    # 3. Add indicator
    print("Adding RSI...")
    mcp_io_github_chr_click(uid="1_12")
    time.sleep(0.5)
    mcp_io_github_chr_fill(uid="8_5", value="RSI")
    time.sleep(0.5)
    mcp_io_github_chr_press_key(key="Enter")
    time.sleep(1.0)
    mcp_io_github_chr_press_key(key="Escape")
    
    # 4. Extract data
    print("Extracting data...")
    extraction_script = """
    () => {
      return {
        symbol: document.title.match(/^([A-Z0-9]+)/)?.[1],
        timestamp: new Date().toISOString()
      };
    }
    """
    data = mcp_io_github_chr_evaluate_script(function=extraction_script)
    
    # 5. Print results
    print(f"\n✅ Complete!")
    print(f"Symbol: {data['symbol']}")
    print(f"Time: {data['timestamp']}")


if __name__ == "__main__":
    main()
```

---

**Last Updated:** 2026-02-08  
**Status:** All workflows tested and verified ✅
