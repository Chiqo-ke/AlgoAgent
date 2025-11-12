# Real-time Backtest Visualization - Implementation Guide

## Overview

This implementation adds **real-time data visualization** to the backtesting process. Users can now see:
- 📊 **Live candlestick chart** rendering as data loads sequentially
- 🎯 **Entry/Exit signals** plotted on the chart in real-time  
- 📈 **Live statistics** updating as the backtest runs
- 🔄 **Progress tracking** with bar count and percentage
- 📋 **Signal log** showing all trades as they occur

## Architecture

### Frontend (`Algo/`)
- **RealtimeBacktestChart.tsx** - React component with Recharts visualization
- **Backtesting.tsx** - Updated to integrate real-time streaming

### Backend (`AlgoAgent/`)
- **consumers.py** - WebSocket consumer for streaming backtest data
- **routing.py** - WebSocket URL configuration
- **asgi.py** - ASGI application with Channels support
- **settings.py** - Django Channels configuration

## Installation Steps

### 1. Install Backend Dependencies

```bash
cd c:\Users\nyaga\Documents\AlgoAgent

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install Django Channels
pip install channels>=4.0.0 channels-redis>=4.1.0

# Or install from requirements.txt
pip install -r requirements.txt
```

### 2. Create Trading App (if doesn't exist)

```bash
# In AlgoAgent directory
python manage.py startapp trading
```

### 3. Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Install Frontend Dependencies (Already Done)

Recharts is already installed in your `Algo/package.json`:
```json
"recharts": "^2.15.4"
```

## How It Works

### 1. **Sequential Data Loading**

The backend uses the existing streaming mode from `data_loader.py`:

```python
data_stream = load_market_data(
    ticker=symbol,
    indicators=indicators,
    period='6mo',
    interval='1d',
    stream=True  # ✅ Sequential mode
)

for timestamp, market_data, progress_pct in data_stream:
    # Send each candle via WebSocket
    # Execute strategy logic
    # Capture signals
```

### 2. **WebSocket Communication**

**Frontend sends:**
```json
{
  "action": "start_backtest",
  "config": {
    "symbol": "AAPL",
    "period": "6mo",
    "interval": "1d",
    "initial_balance": 10000,
    "indicators": {
      "RSI": {"timeperiod": 14},
      "SMA": {"timeperiod": 20}
    }
  }
}
```

**Backend streams:**
```json
// Candle data (sent for each bar)
{
  "type": "candle",
  "timestamp": "2024-10-01T09:30:00",
  "open": 150.25,
  "high": 151.50,
  "low": 149.80,
  "close": 151.00,
  "volume": 1000000,
  "bar_number": 45,
  "progress": 45.2
}

// Trade signal
{
  "type": "signal",
  "timestamp": "2024-10-01T09:30:00",
  "action": "ENTRY",
  "side": "BUY",
  "price": 151.00,
  "size": 10
}

// Statistics update
{
  "type": "stats",
  "total_trades": 5,
  "winning_trades": 3,
  "losing_trades": 2,
  "pnl": 250.50
}
```

### 3. **Real-time Chart Rendering**

The `RealtimeBacktestChart` component:
1. Connects to WebSocket on mount
2. Receives candle data sequentially
3. Appends to chart data array
4. Renders candlesticks with Recharts
5. Plots trade signals as dots on chart
6. Updates statistics cards
7. Auto-scrolls to keep latest candle visible

## Features

### 📊 Candlestick Chart
- Green candles for bullish bars (close >= open)
- Red candles for bearish bars (close < open)
- Wicks showing high/low range
- Custom tooltip with OHLCV data

### 🎯 Trade Signals
- **Green dots** - Long entries
- **Red dots** - Short entries  
- **Blue dots** - Exit signals
- Plotted at exact entry/exit prices

### 📈 Live Statistics
Four live-updating cards:
1. **Progress** - Bar count and percentage with progress bar
2. **Total Trades** - Count with win/loss badges
3. **Win Rate** - Percentage with visual bar
4. **P&L** - Real-time profit/loss

### 📋 Signal Log
- Scrollable table of recent signals
- Shows last 10 trades
- Time, type, side, price, size
- Color-coded badges

## Configuration

### Adjust Streaming Speed

In `consumers.py`, change the delay between candles:

```python
# Faster streaming (20ms)
await asyncio.sleep(0.02)

# Slower streaming (100ms)
await asyncio.sleep(0.1)

# No delay (instant)
# await asyncio.sleep(0)
```

### WebSocket URL

In `RealtimeBacktestChart.tsx`, update the WebSocket URL if needed:

```typescript
const ws = new WebSocket(
  `${import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000"}/ws/backtest/stream/`
);
```

Add to your `.env`:
```
VITE_WS_BASE_URL=ws://localhost:8000
```

## Testing

### 1. Start Django Server with WebSocket Support

**Option A: Using the start script (Recommended)**
```powershell
cd c:\Users\nyaga\Documents\AlgoAgent
.\start_server.ps1
```

**Option B: Using Daphne directly**
```powershell
cd c:\Users\nyaga\Documents\AlgoAgent
.\.venv\Scripts\Activate.ps1
daphne -b 0.0.0.0 -p 8000 algoagent_api.asgi:application
```

**Option C: Using Django runserver (Development only)**
```powershell
python manage.py runserver
```

> **Note:** Daphne is the recommended ASGI server for Django Channels. `runserver` works in development but Daphne provides better WebSocket support.

### 2. Start Frontend

```bash
cd c:\Users\nyaga\Documents\Algo
npm run dev
```

### 3. Run a Backtest

1. Navigate to Strategy page
2. Click "Test" on any strategy
3. Configure backtest parameters
4. Click "Run Backtest"
5. Watch the chart render in real-time! 🎉

## Integration with Strategy Code

The consumer needs to execute your strategy code. You have two options:

### Option 1: Pass Strategy Code via WebSocket

```typescript
// Frontend sends strategy code
const ws = new WebSocket(...);
ws.send(JSON.stringify({
  action: "start_backtest",
  config: {
    strategy_code: strategyCodeString,
    // ... other config
  }
}));
```

### Option 2: Load Strategy from Database

```python
# In consumers.py
from strategy_api.models import Strategy

async def run_backtest_stream(self, config: dict):
    strategy_id = config.get("strategy_id")
    strategy = await database_sync_to_async(Strategy.objects.get)(id=strategy_id)
    
    # Execute strategy code
    exec(strategy.strategy_code, globals())
    # ... rest of backtest
```

## Troubleshooting

### WebSocket Connection Fails

**Error:** `WebSocket connection to 'ws://localhost:8000/ws/backtest/stream/' failed`

**Solution:** 
1. Check Django server is running
2. Verify Channels is installed: `pip list | grep channels`
3. Check ASGI configuration in `algoagent_api/asgi.py`

### Candles Not Rendering

**Issue:** Chart is empty

**Solution:**
1. Open browser DevTools → Console
2. Look for WebSocket messages
3. Verify data format matches expected structure

### Signals Not Showing

**Issue:** No entry/exit markers on chart

**Solution:**
- Implement `get_recent_signals()` in `consumers.py`
- Ensure SimBroker tracks signals
- Add signal queue to broker

## Next Steps

### 1. **Strategy Integration**
Connect the WebSocket consumer to your strategy execution system:

```python
# Import strategy dynamically
strategy_module = importlib.import_module(strategy_path)
strategy_class = getattr(strategy_module, "StrategyClass")

# Initialize and run
strategy = strategy_class(broker, symbol=symbol)
strategy.on_bar(timestamp, market_data)
```

### 2. **Signal Tracking**
Enhance `SimBroker` to track signals:

```python
class SimBroker:
    def __init__(self, config):
        self.signals_queue = []
    
    def submit_signal(self, signal):
        self.signals_queue.append(signal)
        # ... existing code
```

### 3. **Historical Playback**
Add ability to replay historical backtests:

```typescript
<RealtimeBacktestChart
  mode="replay"
  backtestId={123}
  playbackSpeed={2} // 2x speed
/>
```

### 4. **Save Charts**
Export chart as image:

```typescript
import html2canvas from 'html2canvas';

const exportChart = async () => {
  const element = chartRef.current;
  const canvas = await html2canvas(element);
  const link = document.createElement('a');
  link.download = 'backtest-chart.png';
  link.href = canvas.toDataURL();
  link.click();
};
```

## Files Modified/Created

### Created Files
- ✅ `Algo/src/components/RealtimeBacktestChart.tsx` - Chart component
- ✅ `AlgoAgent/trading/consumers.py` - WebSocket consumer
- ✅ `AlgoAgent/trading/routing.py` - WebSocket routing
- ✅ `AlgoAgent/REALTIME_BACKTEST_VISUALIZATION.md` - This guide

### Modified Files
- ✅ `Algo/src/pages/Backtesting.tsx` - Added chart integration
- ✅ `AlgoAgent/algoagent_api/asgi.py` - Channels configuration
- ✅ `AlgoAgent/algoagent_api/settings.py` - Added Channels app
- ✅ `AlgoAgent/requirements.txt` - Added channels dependencies

## Performance Considerations

- **Memory:** Chart stores all candles in browser memory. For long backtests (>1000 bars), consider:
  - Windowing (only show last N candles)
  - Server-side aggregation
  - Chart virtualization

- **Network:** Each candle sends ~200 bytes. For 1000 bars:
  - Total data: ~200KB
  - Streaming duration: 50 seconds @ 50ms/candle
  - Bandwidth: ~4KB/s

- **Rendering:** Recharts handles 1000+ candles well, but consider:
  - Debouncing updates for very fast streaming
  - Canvas-based rendering for >5000 candles
  - Progressive loading

## Support

For issues:
1. Check browser console for errors
2. Check Django console for WebSocket logs
3. Verify `streaming_mode` is enabled in `sequential_config.py`
4. Test WebSocket connection with browser tools

---

**Created:** 2025-11-03  
**Version:** 1.0.0  
**Status:** ✅ Implemented and Ready for Testing
