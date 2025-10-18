# Import Fix Summary

## Problem Solved ✅

Fixed import errors that prevented AI-generated strategies from working with the Live trading module.

## Root Cause

**The Issue:**
- Strategies in `Backtest/codes/` were using absolute imports: `from sim_broker import SimBroker`
- Backtest internal modules were using relative imports: `from .canonical_schema import ...`
- When Live module loaded a strategy dynamically, the imports failed with:
  ```
  ImportError: attempted relative import with no known parent package
  ```

## Solution Applied

### 1. Updated All Strategy Templates and Examples

**Files Updated:**
- ✅ `Backtest/gemini_strategy_generator.py` - Generator template
- ✅ `Backtest/example_strategy.py` - Example reference
- ✅ `Backtest/rsi_strategy.py` - RSI example
- ✅ `Backtest/ema_strategy.py` - EMA example
- ✅ `Backtest/example_gemini_strategy.py` - Gemini example
- ✅ `Backtest/codes/my_strategy.py` - Your strategy

**New Import Pattern:**
```python
# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
```

### 2. Fixed Backtest Internal Modules

**Files Updated:**
- ✅ `Backtest/sim_broker.py`
- ✅ `Backtest/account_manager.py`
- ✅ `Backtest/execution_simulator.py`
- ✅ `Backtest/order_manager.py`
- ✅ `Backtest/metrics_engine.py`
- ✅ `Backtest/validators.py`

**Changed to relative imports:**
```python
# Before (broken)
from canonical_schema import Signal, Order
from config import BacktestConfig

# After (working)
from .canonical_schema import Signal, Order
from .config import BacktestConfig
```

### 3. Fixed Package Exports

**File Updated:**
- ✅ `Backtest/__init__.py` - Removed non-existent `parse_filename` import

### 4. Created Documentation

**New Files:**
- ✅ `Backtest/STRATEGY_TEMPLATE.md` - Complete template guide with examples
- ✅ Updated `Backtest/README.md` - Added strategy development section

## Verification

All components now work correctly:

### ✅ Backtest Mode
```bash
cd Backtest
python rsi_strategy.py
```

### ✅ Live Trading Mode (Dry-Run)
```bash
cd Live
python live_trader.py --strategy ..\Backtest\codes\my_strategy.py --dry-run
```

**Test Results:**
- Live trader successfully initialized
- Connected to MT5 (demo account)
- Strategy loaded: AIGeneratedStrategy
- Trading loop started
- Graceful shutdown working

## For Future Strategy Generation

### When Using Gemini Generator

The generator is already updated. Just run:
```bash
cd Backtest
python gemini_strategy_generator.py
```

Generated strategies will automatically have the correct imports.

### When Creating Manual Strategies

Use the template from `STRATEGY_TEMPLATE.md`:

```python
# MUST NOT EDIT SimBroker
"""
Strategy: YourStrategyName
Description: Your description
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
from datetime import datetime
import pandas as pd

# Your strategy class here...
```

### Validation Checklist

Before running a strategy in Live mode, verify:

- [ ] Strategy has path setup code (parent_dir)
- [ ] Imports use `from Backtest.module import ...` format
- [ ] Strategy runs successfully in backtest mode
- [ ] Strategy loads without errors in dry-run mode

## Why This Works

The new pattern ensures:

1. **Path Resolution:** The parent directory (AlgoAgent) is added to sys.path
2. **Package Import:** `from Backtest.module` tells Python to import from the Backtest package
3. **Relative Imports Work:** Internal Backtest modules can use relative imports (`.canonical_schema`)
4. **Dynamic Loading:** Live module can load strategies from any location
5. **No Conflicts:** No ambiguity about which module to import

## Backward Compatibility

The validator accepts both patterns temporarily:
```python
# Both are accepted
"from Backtest.sim_broker import SimBroker"  # New (preferred)
"from sim_broker import SimBroker"           # Old (deprecated)
```

But **only the new pattern works with Live trading**.

## Summary

✅ **Problem:** Import errors when loading strategies in Live mode  
✅ **Root Cause:** Mixed absolute/relative imports  
✅ **Solution:** Standardized to package imports with path setup  
✅ **Status:** All templates and examples updated  
✅ **Future:** New strategies will automatically use correct pattern  

**No more import errors!** 🎉
