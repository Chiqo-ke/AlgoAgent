# Backtesting Data Flow Report

## Executive Summary

This document describes the complete data flow between the **AlgoAgent backend** and the **Algo frontend** for the backtesting functionality. It covers REST API endpoints, WebSocket streaming, data structures, and integration points.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Backend API Endpoints](#2-backend-api-endpoints)
3. [WebSocket Streaming Protocol](#3-websocket-streaming-protocol)
4. [Data Structures](#4-data-structures)
5. [Frontend Components](#5-frontend-components)
6. [Integration Flow](#6-integration-flow)
7. [Database Models](#7-database-models)
8. [Current Issues & Recommendations](#8-current-issues--recommendations)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Algo)                            │
│  ┌─────────────────┐    ┌──────────────────────┐    ┌───────────────┐  │
│  │  Backtesting.tsx │───▶│ RealtimeBacktestChart│───▶│   UI Display  │  │
│  └────────┬────────┘    └──────────┬───────────┘    └───────────────┘  │
│           │                        │                                    │
│           │ HTTP                   │ WebSocket                          │
└───────────┼────────────────────────┼────────────────────────────────────┘
            │                        │
            ▼                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         BACKEND (AlgoAgent)                            │
│  ┌─────────────────────────┐    ┌───────────────────────────────────┐ │
│  │   REST API Endpoints    │    │   WebSocket Consumer              │ │
│  │  - /api/backtests/      │    │  - ws/backtest/stream/            │ │
│  │  - /api/strategies/     │    │  - BacktestStreamConsumer         │ │
│  └──────────┬──────────────┘    └─────────────┬─────────────────────┘ │
│             │                                  │                       │
│             ▼                                  ▼                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    Backtest Execution Engine                     │  │
│  │  ┌─────────────────┐    ┌────────────────┐    ┌──────────────┐  │  │
│  │  │ BacktestingAdapter│   │   SimBroker    │    │ Market Data  │  │  │
│  │  │ (backtesting.py)  │   │   Engine       │    │   Loader     │  │  │
│  │  └─────────────────┘    └────────────────┘    └──────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│             │                                                          │
│             ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                         Database                                 │  │
│  │  - BacktestConfig, BacktestRun, BacktestResult                  │  │
│  │  - Trade, BacktestAlert                                          │  │
│  │  - LatestBacktestResult (per strategy)                          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 2. Backend API Endpoints

### 2.1 Backtest Execution Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/backtests/api/quick_run/` | POST | **Primary endpoint** - Quick backtest execution |
| `/api/backtests/api/run_backtest/` | POST | Full backtest run |
| `/api/backtests/api/status/{id}/` | GET | Get backtest status |
| `/api/backtests/api/monitor/{id}/` | GET | Monitor running backtest |

### 2.2 Configuration Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/backtests/configs/` | GET/POST | List/create configurations |
| `/api/backtests/configs/{id}/` | GET/PUT/DELETE | CRUD for config |
| `/api/backtests/configs/templates/` | GET | Get template configs |

### 2.3 Results & Trades Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/backtests/results/` | GET | List all results |
| `/api/backtests/results/{id}/` | GET | Get specific result |
| `/api/backtests/trades/` | GET | List trades (filterable) |
| `/api/backtests/runs/` | GET | List backtest runs |
| `/api/backtests/runs/{id}/results/` | GET | Get results for a run |

### 2.4 Latest Backtest Results (Per Strategy)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/strategies/latest-backtest/` | GET | List all latest results |
| `/api/strategies/latest-backtest/{id}/get_by_strategy/` | GET | Get by strategy ID |

### 2.5 Strategy Validation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/strategies/validate/` | POST | Validate strategy code |
| `/api/strategies/strategies/{id}/validate/` | POST | Validate by ID |
| `/api/strategies/strategies/{id}/backtest/` | POST | Quick backtest for strategy |

---

## 3. WebSocket Streaming Protocol

### 3.1 Connection

**URL:** `ws://localhost:8000/ws/backtest/stream/`

### 3.2 Client → Server Messages

#### Start Backtest Request
```json
{
  "action": "start_backtest",
  "config": {
    "strategy_code": "<Python code or canonical JSON>",
    "strategy_id": 123,
    "symbol": "AAPL",
    "period": "6mo",
    "interval": "1d",
    "initial_balance": 10000,
    "commission": 0.002,
    "slippage": 0.0005,
    "indicators": {
      "RSI": { "timeperiod": 14 },
      "EMA": { "periods": [9, 21] },
      "SMA": { "periods": [20, 50] }
    }
  }
}
```

### 3.3 Server → Client Messages

#### Metadata Message
```json
{
  "type": "metadata",
  "symbol": "AAPL",
  "period": "6mo",
  "interval": "1d",
  "status": "loading_data|running_backtest|streaming_visualization",
  "total_bars": 126,
  "total_trades": 10
}
```

#### Candle Message (streamed per bar)
```json
{
  "type": "candle",
  "bar_number": 1,
  "progress": 0.79,
  "timestamp": "2024-01-02",
  "open": 150.25,
  "high": 152.00,
  "low": 149.50,
  "close": 151.75,
  "volume": 1234567
}
```

#### Signal Message (trade entry/exit)
```json
{
  "type": "signal",
  "timestamp": "2024-01-15",
  "action": "ENTRY|EXIT",
  "side": "BUY|SELL|CLOSE",
  "price": 155.25,
  "size": 10,
  "pnl": 125.50
}
```

#### Stats Message (periodic updates)
```json
{
  "type": "stats",
  "total_trades": 10,
  "winning_trades": 6,
  "losing_trades": 4,
  "pnl": 1250.00,
  "win_rate": 60.0
}
```

#### Complete Message (final)
```json
{
  "type": "complete",
  "total_bars": 126,
  "metrics": {
    "total_trades": 10,
    "winning_trades": 6,
    "losing_trades": 4,
    "win_rate": 60.0,
    "net_profit": 1250.00,
    "total_return_pct": 12.5,
    "final_equity": 11250.00,
    "max_drawdown": 5.2,
    "sharpe_ratio": 1.45
  }
}
```

#### Error Message
```json
{
  "type": "error",
  "message": "Error description"
}
```

---

## 4. Data Structures

### 4.1 Request Structures (Frontend → Backend)

#### BacktestConfig
```typescript
interface BacktestConfig {
  id?: number;
  name?: string;
  strategy_id?: number;
  strategy_code?: string;           // Python code or canonical JSON
  symbol: string;                    // e.g., "AAPL", "MSFT", "EURUSD"
  start_date: string;                // Format: "yyyy-MM-dd"
  end_date: string;                  // Format: "yyyy-MM-dd"
  timeframe?: string;                // "1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"
  initial_capital?: number;          // Default: 10000
  initial_balance?: number;          // Alias for initial_capital
  lot_size?: number;                 // Default: 1.0
  commission?: number;               // Default: 0.001 (0.1%)
  slippage?: number;                 // Default: 0.0005 (0.05%)
  config?: Record<string, any>;
}
```

### 4.2 Response Structures (Backend → Frontend)

#### BacktestResult
```typescript
interface BacktestResult {
  id?: number;
  run?: number;
  strategy?: string;
  symbol?: string;
  start_date?: string;
  end_date?: string;
  initial_capital?: number;
  final_value?: number;
  total_return?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  win_rate?: number;
  profit_factor?: number;
  total_trades?: number;
  winning_trades?: number;
  losing_trades?: number;
  trades?: Trade[];
  daily_stats?: DailyStat[];
  symbol_stats?: SymbolStat[];
  summary?: {
    totalTrades: number;
    winRate: number;
    totalProfit: number;
    averageTrade: number;
  };
}
```

#### LatestBacktestResult (Persisted per strategy)
```typescript
interface LatestBacktestResult {
  strategy_id: number;
  strategy_name: string;
  symbol: string;
  timeframe: string;
  period: string;
  initial_balance: number;
  commission: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  net_profit: number;
  total_return_pct: number;
  final_equity: number | null;
  max_drawdown: number;
  sharpe_ratio: number | null;
  trades: Trade[];
  equity_curve: EquityPoint[];
  created_at: string;
  updated_at: string;
}
```

#### Trade
```typescript
interface Trade {
  id?: number;
  backtest_run?: number;
  date?: string;
  timestamp?: string;
  entry_time?: string;
  exit_time?: string;
  symbol?: string;
  action?: 'buy' | 'sell' | 'short' | 'cover';
  entry_price?: number;
  exit_price?: number;
  quantity?: number;
  size?: number;
  price?: number;
  profit?: number;
  pnl?: number;
  return_pct?: number;
  commission?: number;
  balance?: number;
}
```

#### Supporting Types
```typescript
interface DailyStat {
  day: string;
  profit: number;
  trades: number;
  balance?: number;
  drawdown?: number;
}

interface SymbolStat {
  symbol: string;
  trades: number;
  profit: number;
  percentage: number;
  win_rate?: number;
}

interface EquityPoint {
  timestamp: string;
  equity: number;
}
```

---

## 5. Frontend Components

### 5.1 Backtesting.tsx (Main Page)

**Location:** `Algo/src/pages/Backtesting.tsx`

**Responsibilities:**
- Displays backtest configuration form
- Fetches strategy details and saved results
- Initiates backtest execution
- Displays final results in summary cards and charts

**Data Dependencies:**
- `strategyId` - From URL params or navigation state
- `symbols` - Fetched from `/api/symbols/`
- `strategy` - Fetched from `/api/strategies/strategies/{id}/`
- `savedResults` - Fetched from `/api/strategies/latest-backtest/{id}/get_by_strategy/`

**UI Elements:**
| Element | Data Source |
|---------|-------------|
| Symbol Input | `symbols` API |
| Period Select | Hardcoded options |
| Timeframe Select | Hardcoded options |
| Total Trades Card | `results.summary.totalTrades` |
| Win Rate Card | `results.summary.winRate` |
| Total Profit Card | `results.summary.totalProfit` |
| Avg Trade Card | `results.summary.averageTrade` |
| Daily Performance Chart | `results.dailyStats[]` |
| Symbol Distribution Chart | `results.symbolStats[]` |

### 5.2 RealtimeBacktestChart.tsx (Streaming Component)

**Location:** `Algo/src/components/RealtimeBacktestChart.tsx`

**Responsibilities:**
- Connects to WebSocket for real-time streaming
- Renders candlestick chart with trade signals
- Updates statistics in real-time
- Passes final results to parent on completion

**WebSocket Message Handling:**
| Message Type | Action |
|--------------|--------|
| `metadata` | Update `totalBars`, status |
| `candle` | Add to `candleData[]`, update `currentBar` |
| `signal` | Add to `signals[]`, render on chart |
| `stats` | Update `stats` state (trades, pnl, win rate) |
| `complete` | Call `onComplete(results)` callback |
| `error` | Log error, show toast |

**UI Elements:**
| Element | Data Source |
|---------|-------------|
| Progress Card | `currentBar / totalBars` |
| Total Trades Card | `stats.totalTrades` |
| Win Rate Card | `(winningTrades / totalTrades) * 100` |
| P&L Card | `stats.pnl` |
| Candlestick Chart | `candleData[]` |
| Signal Markers | `signals[]` |
| Signal Log Table | `signals[]` (last 10) |

---

## 6. Integration Flow

### 6.1 Complete Backtest Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INITIATES BACKTEST                        │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. NAVIGATE TO BACKTEST PAGE                                            │
│    - Extract strategyId from URL/state                                  │
│    - Fetch strategy details: GET /api/strategies/strategies/{id}/       │
│    - Fetch saved results: GET /api/strategies/latest-backtest/{id}/...  │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. USER CONFIGURES PARAMETERS                                           │
│    - Symbol (from dropdown or manual entry)                             │
│    - Period (1week, 1month, 3months, 6months, 1year, 2years, custom)    │
│    - Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)                       │
│    - Initial Balance, Commission, Slippage                              │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. CLICK "RUN BACKTEST"                                                 │
│    - Validate required fields                                           │
│    - Validate strategy: POST /api/strategies/validate/                  │
│    - Set isStreaming = true                                             │
│    - Mount RealtimeBacktestChart component                              │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. WEBSOCKET CONNECTION                                                 │
│    - Connect: ws://localhost:8000/ws/backtest/stream/                   │
│    - Send: { action: "start_backtest", config: {...} }                  │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. BACKEND PROCESSING (BacktestStreamConsumer)                          │
│    ┌─────────────────────────────────────────────────────────────────┐  │
│    │ a. Load market data for symbol/period/interval                  │  │
│    │    → Send: { type: "metadata", status: "loading_data" }         │  │
│    │                                                                  │  │
│    │ b. Execute backtest (SimBroker or backtesting.py)               │  │
│    │    → Send: { type: "metadata", status: "running_backtest" }     │  │
│    │    → Send: { type: "stats", ... } (initial stats)               │  │
│    │                                                                  │  │
│    │ c. Stream visualization                                         │  │
│    │    → Send: { type: "metadata", status: "streaming_visualization"}│  │
│    │    → FOR EACH bar:                                               │  │
│    │        → Send: { type: "candle", ... }                          │  │
│    │        → IF trade at this bar:                                  │  │
│    │            → Send: { type: "signal", ... }                      │  │
│    │        → Every 50 bars:                                         │  │
│    │            → Send: { type: "stats", ... }                       │  │
│    │                                                                  │  │
│    │ d. Complete                                                      │  │
│    │    → Send: { type: "complete", metrics: {...} }                 │  │
│    │    → Save to LatestBacktestResult (replace existing)            │  │
│    └─────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. FRONTEND RECEIVES COMPLETE                                           │
│    - RealtimeBacktestChart calls onComplete(results)                    │
│    - Backtesting.tsx updates results state                              │
│    - Display summary cards and charts                                   │
│    - Set isStreaming = false                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Data Transformation Points

| Source | Transform | Destination |
|--------|-----------|-------------|
| Backend `net_profit` | None | Frontend `totalProfit` |
| Backend `total_trades` | None | Frontend `totalTrades` |
| Backend `win_rate` | `.toFixed(1)` | Frontend display `60.0%` |
| Backend `net_profit` | `.toFixed(2)` | Frontend display `-5215.19 pips` |
| WebSocket `stats` | Direct mapping | `RealtimeBacktestChart.stats` |
| WebSocket `complete.metrics` | Transform | `Backtesting.results` |
| `LatestBacktestResult` | Transform | `Backtesting.results` on page load |

---

## 7. Database Models

### 7.1 LatestBacktestResult (strategy_api/models.py)

**Purpose:** Stores the most recent backtest result for each strategy. Replaced on each new backtest.

```python
class LatestBacktestResult(models.Model):
    strategy = models.OneToOneField(Strategy, on_delete=models.CASCADE, 
                                     primary_key=True, related_name='latest_backtest')
    
    # Configuration
    symbol = models.CharField(max_length=20)
    timeframe = models.CharField(max_length=10, default='1d')
    period = models.CharField(max_length=20, default='1y')
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=10000)
    commission = models.DecimalField(max_digits=10, decimal_places=6, default=0.001)
    
    # Results
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_return_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    final_equity = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    
    # Detailed data
    trades = models.JSONField(default=list)      # List of trade objects
    equity_curve = models.JSONField(default=list) # Equity over time
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 7.2 BacktestRun (backtest/models.py)

**Purpose:** Tracks individual backtest executions with status and timing.

### 7.3 BacktestResult (backtest/models.py)

**Purpose:** Stores detailed results for a BacktestRun including time series data.

### 7.4 Trade (backtest/models.py)

**Purpose:** Stores individual trade records for a BacktestRun.

---

## 8. Current Issues & Recommendations

### 8.1 Issues Identified

| Issue | Description | Status |
|-------|-------------|--------|
| Number Formatting | Raw floats displayed with many decimals | ✅ Fixed |
| Results Not Persisting | Results lost on page refresh | ✅ Fixed |
| Hardcoded Data | Frontend displayed mock data | ✅ Fixed |
| Timestamp Mismatch | Trade signals not matching candles | ✅ Fixed |

### 8.2 Current Integration Status

| Feature | Backend | Frontend | Integration |
|---------|---------|----------|-------------|
| Quick Run API | ✅ | ✅ | ✅ Working |
| WebSocket Streaming | ✅ | ✅ | ✅ Working |
| Strategy Validation | ✅ | ✅ | ✅ Working |
| Save to Database | ✅ | ✅ | ✅ Working |
| Load Saved Results | ✅ | ✅ | ✅ Working |
| Real-time Chart | ✅ | ✅ | ✅ Working |
| Trade Signals | ✅ | ✅ | ✅ Working |
| Stats Display | ✅ | ✅ | ✅ Working |

### 8.3 Recommendations

1. **Add Daily Stats Computation**
   - Currently `dailyStats` is empty
   - Backend should aggregate trades by day and compute daily P&L

2. **Add Equity Curve Chart**
   - Backend sends `equity_curve` data
   - Frontend could add a line chart showing equity over time

3. **Add Multi-Symbol Support**
   - Backend supports multiple symbols
   - Frontend UI only allows single symbol currently

4. **Add Historical Results Comparison**
   - Could store multiple backtest runs instead of just latest
   - Allow comparing results across different configurations

---

## Appendix A: API Examples

### A.1 Quick Run Request
```bash
curl -X POST http://localhost:8000/api/backtests/api/quick_run/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 123,
    "symbol": "AAPL",
    "start_date": "2024-01-01",
    "end_date": "2024-10-31",
    "timeframe": "1d",
    "initial_balance": 10000,
    "commission": 0.001
  }'
```

### A.2 Get Latest Result
```bash
curl http://localhost:8000/api/strategies/latest-backtest/123/get_by_strategy/
```

### A.3 WebSocket Connection (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/backtest/stream/');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'start_backtest',
    config: {
      strategy_id: 123,
      symbol: 'AAPL',
      period: '6mo',
      interval: '1d',
      initial_balance: 10000
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case 'candle': /* render candle */; break;
    case 'signal': /* mark trade */; break;
    case 'stats':  /* update stats */; break;
    case 'complete': /* show results */; break;
  }
};
```

---

*Report generated: December 13, 2025*
