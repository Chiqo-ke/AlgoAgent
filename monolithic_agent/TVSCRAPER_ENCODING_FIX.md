# TVScraper Backend Integration - Encoding Fix

## Problem Summary

**Error**: `'charmap' codec can't encode character '\u274c' in position 3`

**Root Cause**: 
- TVScraper outputs emoji characters (✅, ❌, ⚠️, 📊) via print statements
- Windows Python uses 'charmap' codec by default for stdout/stderr
- 'charmap' codec cannot handle Unicode emoji characters
- When Django backend calls TVScraper, these emojis cause encoding errors

## Solution Implemented

### 1. **UTF-8 Encoding in Django (`manage.py`)**

```python
# Force UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set environment variable
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

**Effect**: All Django output now uses UTF-8, handling emoji and Unicode characters properly.

### 2. **Suppress TVScraper Output (`data_loader.py`)**

```python
import contextlib
import io

# Suppress stdout/stderr when using TVScraper as library
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    scraper = MCPTradingViewScraper()
    scraper.init_browser()
    scraper.navigate_to_tradingview()
    # ... rest of the scraper calls
```

**Effect**: TVScraper emoji output is suppressed when used programmatically (not affecting CLI usage).

### 3. **Error Message Sanitization (`data_loader.py`)**

```python
except Exception as e:
    # Remove emoji characters from error messages
    error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
    logger.error(f"TVscraper fetch failed: {error_msg}")
    raise RuntimeError(f"TVscraper fetch failed: {error_msg}") from e
```

**Effect**: Error messages are ASCII-safe, preventing encoding issues in logs.

## Files Modified

1. **`AlgoAgent/monolithic_agent/manage.py`**
   - Added UTF-8 encoding setup for Windows
   - Added PYTHONIOENCODING environment variable

2. **`AlgoAgent/monolithic_agent/Backtest/data_loader.py`**
   - Added stdout/stderr suppression for TVScraper calls
   - Added error message sanitization
   - Removed emoji characters from logged errors

## Testing

### Quick Test
```bash
cd C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
python manage.py shell
```

```python
from Backtest.data_loader import fetch_market_data

# Test TVScraper integration
data = fetch_market_data("AAPL", period="1mo", interval="1h")
print(f"Fetched {len(data)} rows")
print(data.head())
```

### Full Strategy Test
1. Create a new strategy in the frontend
2. Click "Confirm and Proceed"
3. TVScraper should fetch data without encoding errors
4. Check logs for clean output (no emoji encoding warnings)

## Benefits

✅ **Windows Compatibility**: Full UTF-8 support on Windows  
✅ **Clean Logs**: No encoding errors in Django logs  
✅ **Library Mode**: TVScraper works silently when used programmatically  
✅ **CLI Mode**: TVScraper still shows emoji when used interactively  
✅ **Error Handling**: Safe error messages without encoding issues  

## Additional Recommendations

### 1. Add to Django settings.py
```python
# settings.py
import sys
import io

# Ensure UTF-8 encoding globally
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

### 2. Update TVScraper for Library Mode

Consider adding a `silent` parameter to TVScraper:

```python
# tvscraper/mcp_scraper.py
class MCPTradingViewScraper:
    def __init__(self, silent=False):
        self.silent = silent
    
    def _print(self, message):
        """Print only if not in silent mode"""
        if not self.silent:
            print(message)
    
    # Replace all print() calls with self._print()
```

Then use it as:
```python
scraper = MCPTradingViewScraper(silent=True)  # No emoji output
```

### 3. Environment Variable Alternative

Set in PowerShell before running Django:
```powershell
$env:PYTHONIOENCODING = "utf-8"
python manage.py runserver
```

Or in `.env` file:
```
PYTHONIOENCODING=utf-8
```

## Verification

After applying the fix, you should see:
- ✅ No 'charmap' codec errors
- ✅ TVScraper data fetches successfully
- ✅ Clean log output in Django
- ✅ Strategies execute without encoding failures

## Rollback (if needed)

If issues occur, revert with:
```bash
cd C:\Users\nyaga\Documents\AlgoAgent
git checkout manage.py
git checkout monolithic_agent/Backtest/data_loader.py
```

---

**Status**: ✅ Fixed  
**Date**: February 11, 2026  
**Impact**: Windows encoding compatibility  
**Breaking Changes**: None
