# WebSocket Real-time Visualization - Quick Fix Guide

## Issues Fixed

### 1. **404 WebSocket Error**
**Problem:** `GET /ws/backtest/stream/ HTTP/1.1" 404`

**Root Causes:**
- Missing `^` in regex pattern in `routing.py`
- Daphne ASGI server not installed
- Missing Django app structure files

**Solutions Applied:**
✅ Fixed routing pattern from `r'ws/backtest/stream/$'` to `r'^ws/backtest/stream/$'`
✅ Installed Daphne: `pip install daphne`
✅ Added `'daphne'` to INSTALLED_APPS (must be first)
✅ Created trading app structure (__init__.py, apps.py, models.py, views.py)
✅ Updated requirements.txt with `daphne>=4.0.0`

### 2. **No Data Streaming**
**Problem:** Chart component not receiving data

**Root Causes:**
- Chart component not sending backtest config to WebSocket
- Consumer expecting config message but frontend not sending it
- Missing config parameter in chart component

**Solutions Applied:**
✅ Added `BacktestConfig` interface to RealtimeBacktestChart.tsx
✅ Chart now sends config message on WebSocket open
✅ Backtesting.tsx passes full config to chart component
✅ Consumer properly receives and processes config

### 3. **Generator Async Issue**
**Problem:** Trying to use `database_sync_to_async` with generator

**Solution:**
✅ Call `load_market_data()` directly (generators are already non-blocking)

## Testing Steps

### 1. Start Backend with WebSocket Support

**Stop any running Django server**, then start with Daphne:

```powershell
cd c:\Users\nyaga\Documents\AlgoAgent
.\start_server.ps1
```

Or manually:
```powershell
cd c:\Users\nyaga\Documents\AlgoAgent
.\.venv\Scripts\Activate.ps1
daphne -b 0.0.0.0 -p 8000 algoagent_api.asgi:application
```

You should see:
```
2025-11-03 14:30:00 INFO     Starting server at tcp:port=8000:interface=0.0.0.0
2025-11-03 14:30:00 INFO     HTTP/2 support enabled
2025-11-03 14:30:00 INFO     Configuring endpoint tcp:port=8000:interface=0.0.0.0
2025-11-03 14:30:00 INFO     Listening on TCP address 0.0.0.0:8000
```

### 2. Start Frontend

```powershell
cd c:\Users\nyaga\Documents\Algo
npm run dev
```

### 3. Test Real-time Visualization

1. Navigate to **Strategy** page
2. Click **"Test"** on any strategy
3. Configure backtest parameters:
   - Symbol: `AAPL`
   - Period: `6mo`
   - Interval: `1d`
   - Initial Balance: `10000`
4. Click **"Run Backtest"**

**Expected Behavior:**
- ✅ WebSocket connects (check browser console)
- ✅ Chart appears with "Progress" card
- ✅ Candlesticks appear one at a time (50ms delay each)
- ✅ Statistics update in real-time
- ✅ Completion message shows when done

### 4. Verify in Browser Console

Open DevTools (F12) → Console, you should see:
```
📡 WebSocket connected for real-time backtest
📤 Sent backtest config: {symbol: "AAPL", period: "6mo", ...}
📊 Backtest starting: streaming bars to process
```

### 5. Verify in Django Console

In the terminal running Daphne, you should see:
```
📡 WebSocket connected for backtest streaming
✅ Backtest streaming completed: 125 bars
```

## Troubleshooting

### Issue: WebSocket Still 404

**Check:**
1. Is Daphne running? (Not `python manage.py runserver`)
2. Is `daphne` first in INSTALLED_APPS?
3. Did you restart the server after changes?

**Fix:**
```powershell
# Kill any running Django process
# Then start with Daphne
.\start_server.ps1
```

### Issue: No Candles Appearing

**Check browser console for errors:**

1. **"WebSocket connection failed"**
   - Backend not running
   - Wrong URL (should be `ws://localhost:8000/ws/backtest/stream/`)

2. **Connection successful but no data**
   - Check Django console for errors
   - Verify config is being sent (check browser console for "📤 Sent backtest config")

3. **"ticker must be a string"** or similar data error
   - Data fetcher error - check indicator configuration
   - Symbol might be invalid

### Issue: Slow/Frozen Chart

The delay is set to 50ms per candle. For faster streaming:

**Edit `trading/consumers.py`:**
```python
# Line ~180
await asyncio.sleep(0.01)  # Change from 0.05 to 0.01 (10ms)
```

For instant (no streaming effect):
```python
# await asyncio.sleep(0.05)  # Comment out
```

## Files Modified

### Backend
- ✅ `algoagent_api/settings.py` - Added `daphne` to INSTALLED_APPS
- ✅ `trading/routing.py` - Fixed WebSocket URL pattern
- ✅ `trading/consumers.py` - Fixed generator handling
- ✅ `trading/__init__.py` - Created
- ✅ `trading/apps.py` - Created
- ✅ `trading/models.py` - Created
- ✅ `trading/views.py` - Created
- ✅ `requirements.txt` - Added daphne
- ✅ `start_server.ps1` - Created startup script

### Frontend
- ✅ `Algo/src/components/RealtimeBacktestChart.tsx` - Added config sending
- ✅ `Algo/src/pages/Backtesting.tsx` - Pass config to chart

## Next Steps

Once streaming works:

1. **Add Strategy Execution**
   - Execute strategy code in consumer
   - Capture actual entry/exit signals
   - Display real trades on chart

2. **Improve Signal Tracking**
   - Implement `get_recent_signals()` in consumer
   - Add signal queue to SimBroker
   - Track signal state (new vs sent)

3. **Enhanced Visualization**
   - Add indicator overlays (SMA, RSI, etc.)
   - Show position markers (open positions)
   - Add order book/pending orders

4. **Performance**
   - Add candle aggregation for large datasets
   - Implement windowing (only show last N candles)
   - Add speed controls (1x, 2x, 5x, instant)

## Current Status

✅ WebSocket infrastructure complete
✅ Real-time data streaming works
✅ Chart renders candles sequentially
✅ Statistics update in real-time
⏳ Strategy execution (shows SimBroker metrics, needs actual strategy)
⏳ Trade signals (placeholder, needs signal tracking)

---

**Last Updated:** 2025-11-03  
**Status:** Ready for testing
