# AGENTS.md - AI Agent Integration Guide

## Overview

TVScraper is designed to be integrated into AI agent workflows, automated trading systems, and codebases that require programmatic access to TradingView market data. This guide provides comprehensive instructions for integrating TVScraper into your AI agents and automated systems.

## 🤖 Agent Integration Patterns

### Pattern 1: Data Collection Agent

An agent that continuously monitors and collects market data for specified symbols.

```python
from tvscraper import Scraper
from datetime import datetime, timedelta
import time
import logging

class MarketDataCollectionAgent:
    """
    Agent that collects market data at regular intervals.
    """
    
    def __init__(self, symbols, timeframe="1h", interval_minutes=60):
        self.symbols = symbols
        self.timeframe = timeframe
        self.interval_minutes = interval_minutes
        self.scraper = Scraper()
        self.logger = logging.getLogger(__name__)
        
    def initialize(self):
        """Initialize browser and TradingView."""
        self.logger.info("Initializing Market Data Collection Agent...")
        self.scraper.init_browser()
        self.scraper.navigate_to_tradingview()
        self.logger.info("Agent initialized successfully")
        
    def collect_data(self, symbol):
        """Collect data for a single symbol."""
        try:
            self.scraper.change_symbol(symbol)
            self.scraper.change_timeframe(self.timeframe)
            
            data = self.scraper.get_historical_data(bars_count=100)
            
            if data:
                # Save to database, file, or process
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/{symbol}_{self.timeframe}_{timestamp}.csv"
                
                self.scraper.save_data(
                    data={"historical": data},
                    filepath=filename,
                    format='csv'
                )
                
                self.logger.info(f"Collected {len(data)} bars for {symbol}")
                return data
            else:
                self.logger.warning(f"No data available for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {e}")
            return None
    
    def run(self):
        """Main agent loop."""
        self.initialize()
        
        while True:
            for symbol in self.symbols:
                self.logger.info(f"Collecting data for {symbol}...")
                self.collect_data(symbol)
                time.sleep(5)  # Delay between symbols
            
            self.logger.info(f"Waiting {self.interval_minutes} minutes...")
            time.sleep(self.interval_minutes * 60)
    
    def shutdown(self):
        """Clean shutdown."""
        self.scraper.close_browser()
        self.logger.info("Agent shutdown complete")


# Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    agent = MarketDataCollectionAgent(
        symbols=["AAPL", "MSFT", "GOOGL", "TSLA"],
        timeframe="1h",
        interval_minutes=60
    )
    
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.shutdown()
```

### Pattern 2: Strategy Backtesting Agent

An agent that fetches historical data and runs backtesting strategies.

```python
from tvscraper import Scraper
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class BacktestingAgent:
    """
    Agent that fetches data and runs backtesting strategies.
    """
    
    def __init__(self):
        self.scraper = Scraper()
        self.results = {}
        
    def setup(self):
        """Initialize scraper."""
        self.scraper.init_browser()
        self.scraper.navigate_to_tradingview()
        
    def fetch_historical_data(self, symbol, days_back=30):
        """Fetch historical data for backtesting."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        self.scraper.change_symbol(symbol)
        self.scraper.change_timeframe("1h")
        
        data = self.scraper.get_historical_data(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d")
        )
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def run_sma_crossover_strategy(self, df, short_window=20, long_window=50):
        """
        Simple Moving Average Crossover Strategy.
        """
        # Calculate SMAs
        df['SMA_short'] = df['close'].rolling(window=short_window).mean()
        df['SMA_long'] = df['close'].rolling(window=long_window).mean()
        
        # Generate signals
        df['signal'] = 0
        df.loc[df['SMA_short'] > df['SMA_long'], 'signal'] = 1  # Buy
        df.loc[df['SMA_short'] < df['SMA_long'], 'signal'] = -1  # Sell
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['returns'] * df['signal'].shift(1)
        
        # Performance metrics
        total_return = (1 + df['strategy_returns']).prod() - 1
        sharpe_ratio = df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252)
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'trades': (df['signal'].diff() != 0).sum(),
            'data': df
        }
    
    def backtest_symbol(self, symbol, days_back=30):
        """Run complete backtest for a symbol."""
        print(f"\n{'='*70}")
        print(f"Backtesting {symbol}")
        print(f"{'='*70}")
        
        # Fetch data
        df = self.fetch_historical_data(symbol, days_back)
        print(f"Fetched {len(df)} bars of data")
        
        # Run strategy
        results = self.run_sma_crossover_strategy(df)
        
        # Display results
        print(f"\nStrategy Performance:")
        print(f"  Total Return: {results['total_return']*100:.2f}%")
        print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"  Number of Trades: {results['trades']}")
        
        self.results[symbol] = results
        return results
    
    def compare_symbols(self, symbols, days_back=30):
        """Compare performance across multiple symbols."""
        for symbol in symbols:
            self.backtest_symbol(symbol, days_back)
        
        # Rank by Sharpe ratio
        ranked = sorted(
            self.results.items(),
            key=lambda x: x[1]['sharpe_ratio'],
            reverse=True
        )
        
        print(f"\n{'='*70}")
        print("Symbol Rankings by Sharpe Ratio")
        print(f"{'='*70}")
        for i, (symbol, result) in enumerate(ranked, 1):
            print(f"{i}. {symbol}: {result['sharpe_ratio']:.2f}")
        
        return ranked
    
    def cleanup(self):
        """Close browser."""
        self.scraper.close_browser()


# Usage
if __name__ == "__main__":
    agent = BacktestingAgent()
    agent.setup()
    
    try:
        # Backtest multiple symbols
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        rankings = agent.compare_symbols(symbols, days_back=60)
        
        # Best performer
        best = rankings[0]
        print(f"\nBest Performer: {best[0]}")
        print(f"Total Return: {best[1]['total_return']*100:.2f}%")
        
    finally:
        agent.cleanup()
```

### Pattern 3: Multi-Agent Coordinator

Coordinate multiple specialized agents working together.

```python
from tvscraper import Scraper
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import queue
import threading

class DataFetcherAgent:
    """Specialized agent for fetching data."""
    
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.scraper = Scraper()
        
    def fetch(self, symbol, timeframe, bars):
        """Fetch data for a symbol."""
        print(f"[Agent {self.agent_id}] Fetching {symbol} {timeframe}...")
        
        self.scraper.change_symbol(symbol)
        self.scraper.change_timeframe(timeframe)
        data = self.scraper.get_historical_data(bars_count=bars)
        
        return {
            'agent_id': self.agent_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'data': data,
            'timestamp': datetime.now()
        }


class AnalysisAgent:
    """Specialized agent for data analysis."""
    
    def __init__(self, agent_id):
        self.agent_id = agent_id
        
    def analyze(self, data):
        """Analyze fetched data."""
        print(f"[Analyzer {self.agent_id}] Analyzing {data['symbol']}...")
        
        if not data['data']:
            return None
        
        prices = [bar['close'] for bar in data['data']]
        
        return {
            'symbol': data['symbol'],
            'avg_price': sum(prices) / len(prices),
            'min_price': min(prices),
            'max_price': max(prices),
            'volatility': max(prices) - min(prices),
            'trend': 'up' if prices[-1] > prices[0] else 'down'
        }


class CoordinatorAgent:
    """Main coordinator managing multiple agents."""
    
    def __init__(self, num_fetchers=3, num_analyzers=2):
        self.fetchers = [DataFetcherAgent(i) for i in range(num_fetchers)]
        self.analyzers = [AnalysisAgent(i) for i in range(num_analyzers)]
        self.data_queue = queue.Queue()
        self.results = []
        
    def initialize_fetchers(self):
        """Initialize all fetcher agents."""
        for fetcher in self.fetchers:
            fetcher.scraper.init_browser()
            fetcher.scraper.navigate_to_tradingview()
        print(f"✓ Initialized {len(self.fetchers)} fetcher agents")
        
    def fetch_data_parallel(self, symbols, timeframe="1h", bars=100):
        """Fetch data for multiple symbols in parallel."""
        with ThreadPoolExecutor(max_workers=len(self.fetchers)) as executor:
            futures = []
            
            for i, symbol in enumerate(symbols):
                fetcher = self.fetchers[i % len(self.fetchers)]
                future = executor.submit(fetcher.fetch, symbol, timeframe, bars)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self.data_queue.put(result)
                    print(f"✓ Fetched data for {result['symbol']}")
                except Exception as e:
                    print(f"✗ Error fetching data: {e}")
    
    def analyze_data_parallel(self):
        """Analyze fetched data in parallel."""
        data_items = []
        while not self.data_queue.empty():
            data_items.append(self.data_queue.get())
        
        with ThreadPoolExecutor(max_workers=len(self.analyzers)) as executor:
            futures = []
            
            for i, data in enumerate(data_items):
                analyzer = self.analyzers[i % len(self.analyzers)]
                future = executor.submit(analyzer.analyze, data)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        self.results.append(result)
                        print(f"✓ Analyzed {result['symbol']}")
                except Exception as e:
                    print(f"✗ Error analyzing data: {e}")
    
    def run(self, symbols):
        """Execute complete workflow."""
        print("\n🤖 Multi-Agent Coordinator Starting...")
        print(f"Symbols: {', '.join(symbols)}")
        print()
        
        # Phase 1: Initialize
        print("[Phase 1] Initializing Agents")
        self.initialize_fetchers()
        print()
        
        # Phase 2: Fetch Data
        print("[Phase 2] Fetching Market Data")
        self.fetch_data_parallel(symbols)
        print()
        
        # Phase 3: Analyze Data
        print("[Phase 3] Analyzing Data")
        self.analyze_data_parallel()
        print()
        
        # Phase 4: Report Results
        print("[Phase 4] Results")
        print("="*70)
        for result in sorted(self.results, key=lambda x: x['volatility'], reverse=True):
            print(f"{result['symbol']:6} | "
                  f"Avg: ${result['avg_price']:.2f} | "
                  f"Range: ${result['min_price']:.2f}-${result['max_price']:.2f} | "
                  f"Volatility: ${result['volatility']:.2f} | "
                  f"Trend: {result['trend']}")
        print("="*70)
        
        return self.results
    
    def cleanup(self):
        """Cleanup all agents."""
        for fetcher in self.fetchers:
            fetcher.scraper.close_browser()
        print("✓ All agents cleaned up")


# Usage
if __name__ == "__main__":
    coordinator = CoordinatorAgent(num_fetchers=3, num_analyzers=2)
    
    try:
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META"]
        results = coordinator.run(symbols)
        
        # Find most volatile
        most_volatile = max(results, key=lambda x: x['volatility'])
        print(f"\nMost Volatile: {most_volatile['symbol']}")
        print(f"Volatility: ${most_volatile['volatility']:.2f}")
        
    finally:
        coordinator.cleanup()
```

## 📡 Integration with Existing Codebases

### FastAPI Integration

```python
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from tvscraper import Scraper
from typing import Optional, List
import uvicorn

app = FastAPI(title="TradingView Data API")
scraper = Scraper()

class DataRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    bars_count: Optional[int] = 100
    from_date: Optional[str] = None
    to_date: Optional[str] = None

class SymbolChangeRequest(BaseModel):
    symbol: str

@app.on_event("startup")
async def startup_event():
    """Initialize scraper on startup."""
    scraper.init_browser()
    scraper.navigate_to_tradingview()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    scraper.close_browser()

@app.post("/api/symbol")
async def change_symbol(request: SymbolChangeRequest):
    """Change chart symbol."""
    try:
        scraper.change_symbol(request.symbol)
        return {"status": "success", "symbol": request.symbol}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/historical")
async def get_historical_data(request: DataRequest):
    """Fetch historical data."""
    try:
        # Change symbol and timeframe
        scraper.change_symbol(request.symbol)
        scraper.change_timeframe(request.timeframe)
        
        # Fetch data
        if request.from_date and request.to_date:
            data = scraper.get_historical_data(
                from_date=request.from_date,
                to_date=request.to_date
            )
        else:
            data = scraper.get_historical_data(
                bars_count=request.bars_count
            )
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "bars": len(data) if data else 0,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/symbols/batch")
async def get_batch_data(symbols: str, timeframe: str = "1h", bars: int = 50):
    """Fetch data for multiple symbols."""
    symbol_list = symbols.split(",")
    results = {}
    
    for symbol in symbol_list:
        try:
            scraper.change_symbol(symbol.strip())
            scraper.change_timeframe(timeframe)
            data = scraper.get_historical_data(bars_count=bars)
            results[symbol.strip()] = {
                "status": "success",
                "bars": len(data) if data else 0,
                "data": data
            }
        except Exception as e:
            results[symbol.strip()] = {
                "status": "error",
                "error": str(e)
            }
    
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Django Integration

```python
# views.py
from django.http import JsonResponse
from django.views import View
from tvscraper import Scraper
import json

class MarketDataView(View):
    scraper = None
    
    @classmethod
    def initialize_scraper(cls):
        """Initialize scraper once."""
        if cls.scraper is None:
            cls.scraper = Scraper()
            cls.scraper.init_browser()
            cls.scraper.navigate_to_tradingview()
    
    def get(self, request, symbol):
        """GET /api/market-data/<symbol>/"""
        self.initialize_scraper()
        
        timeframe = request.GET.get('timeframe', '1h')
        bars = int(request.GET.get('bars', 100))
        
        try:
            self.scraper.change_symbol(symbol)
            self.scraper.change_timeframe(timeframe)
            data = self.scraper.get_historical_data(bars_count=bars)
            
            return JsonResponse({
                'status': 'success',
                'symbol': symbol,
                'data': data
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)

# urls.py
from django.urls import path
from .views import MarketDataView

urlpatterns = [
    path('api/market-data/<str:symbol>/', MarketDataView.as_view()),
]
```

### Flask Integration

```python
from flask import Flask, request, jsonify
from tvscraper import Scraper

app = Flask(__name__)
scraper = Scraper()

@app.before_first_request
def initialize():
    """Initialize scraper before first request."""
    scraper.init_browser()
    scraper.navigate_to_tradingview()

@app.route('/api/data/<symbol>', methods=['GET'])
def get_data(symbol):
    """Fetch data for a symbol."""
    timeframe = request.args.get('timeframe', '1h')
    bars = int(request.args.get('bars', 100))
    
    try:
        scraper.change_symbol(symbol)
        scraper.change_timeframe(timeframe)
        data = scraper.get_historical_data(bars_count=bars)
        
        return jsonify({
            'status': 'success',
            'symbol': symbol,
            'bars': len(data) if data else 0,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.teardown_appcontext
def cleanup(exception=None):
    """Cleanup scraper."""
    scraper.close_browser()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## 🔄 Common Agent Use Cases

### 1. Scheduled Data Collection

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from tvscraper import Scraper
from datetime import datetime

scraper = Scraper()
scraper.init_browser()
scraper.navigate_to_tradingview()

def collect_market_data():
    """Scheduled job to collect data."""
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for symbol in symbols:
        scraper.change_symbol(symbol)
        data = scraper.get_historical_data(bars_count=24)  # Last 24 hours
        
        # Save to database
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/{symbol}_{timestamp}.csv"
        scraper.save_data(data, filepath=filename, format='csv')

# Schedule every hour
scheduler = BlockingScheduler()
scheduler.add_job(collect_market_data, 'interval', hours=1)
scheduler.start()
```

### 2. Real-Time Alert System

```python
from tvscraper import Scraper
import time
import smtplib
from email.message import EmailMessage

class PriceAlertAgent:
    def __init__(self, symbol, threshold_price, email_to):
        self.symbol = symbol
        self.threshold = threshold_price
        self.email_to = email_to
        self.scraper = Scraper()
        
    def check_price(self):
        """Check current price."""
        self.scraper.change_symbol(self.symbol)
        data = scraper.get_market_data()
        
        current_price = data.get('price', 0)
        
        if current_price >= self.threshold:
            self.send_alert(current_price)
            
    def send_alert(self, price):
        """Send email alert."""
        msg = EmailMessage()
        msg['Subject'] = f'{self.symbol} Price Alert!'
        msg['From'] = 'alerts@tradingbot.com'
        msg['To'] = self.email_to
        msg.set_content(f'{self.symbol} reached ${price:.2f}')
        
        # Send email (configure SMTP)
        # ...
        
    def run(self, check_interval=60):
        """Run agent."""
        self.scraper.init_browser()
        self.scraper.navigate_to_tradingview()
        
        while True:
            self.check_price()
            time.sleep(check_interval)

# Usage
agent = PriceAlertAgent("AAPL", 200.0, "trader@example.com")
agent.run(check_interval=300)  # Check every 5 minutes
```

### 3. Portfolio Monitoring

```python
from tvscraper import Scraper
import pandas as pd

class PortfolioMonitor:
    def __init__(self, portfolio):
        """
        portfolio: dict like {'AAPL': 100, 'MSFT': 50}
        """
        self.portfolio = portfolio
        self.scraper = Scraper()
        
    def get_portfolio_value(self):
        """Calculate total portfolio value."""
        self.scraper.init_browser()
        self.scraper.navigate_to_tradingview()
        
        total_value = 0
        positions = []
        
        for symbol, shares in self.portfolio.items():
            self.scraper.change_symbol(symbol)
            data = self.scraper.get_market_data()
            
            price = data.get('price', 0)
            value = price * shares
            total_value += value
            
            positions.append({
                'symbol': symbol,
                'shares': shares,
                'price': price,
                'value': value
            })
        
        df = pd.DataFrame(positions)
        df['weight'] = df['value'] / total_value
        
        return {
            'total_value': total_value,
            'positions': df.to_dict('records')
        }

# Usage
portfolio = {'AAPL': 100, 'MSFT': 50, 'GOOGL': 25}
monitor = PortfolioMonitor(portfolio)
status = monitor.get_portfolio_value()

print(f"Total Portfolio Value: ${status['total_value']:,.2f}")
for pos in status['positions']:
    print(f"{pos['symbol']}: {pos['weight']*100:.1f}% (${pos['value']:,.2f})")
```

## ⚠️ Error Handling Best Practices

```python
from tvscraper import Scraper
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustAgent:
    def __init__(self):
        self.scraper = None
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def initialize_with_retry(self):
        """Initialize with automatic retry."""
        try:
            self.scraper = Scraper()
            self.scraper.init_browser()
            self.scraper.navigate_to_tradingview()
            logger.info("Scraper initialized successfully")
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=5)
    )
    def fetch_data_with_retry(self, symbol, bars=100):
        """Fetch data with automatic retry."""
        try:
            self.scraper.change_symbol(symbol)
            data = self.scraper.get_historical_data(bars_count=bars)
            
            if not data:
                raise ValueError("No data returned")
            
            return data
        except Exception as e:
            logger.error(f"Data fetch failed for {symbol}: {e}")
            raise

# Usage
agent = RobustAgent()
agent.initialize_with_retry()

try:
    data = agent.fetch_data_with_retry("AAPL")
    logger.info(f"Successfully fetched {len(data)} bars")
except Exception as e:
    logger.critical(f"Failed after retries: {e}")
```

## 📊 Performance Optimization

### Connection Pooling Pattern

```python
from tvscraper import Scraper
from queue import Queue
import threading

class ScraperPool:
    """Pool of scraper instances for concurrent access."""
    
    def __init__(self, pool_size=3):
        self.pool = Queue(maxsize=pool_size)
        
        for i in range(pool_size):
            scraper = Scraper()
            scraper.init_browser()
            scraper.navigate_to_tradingview()
            self.pool.put(scraper)
    
    def get_scraper(self):
        """Get scraper from pool."""
        return self.pool.get()
    
    def return_scraper(self, scraper):
        """Return scraper to pool."""
        self.pool.put(scraper)
    
    def execute(self, func, *args, **kwargs):
        """Execute function with pooled scraper."""
        scraper = self.get_scraper()
        try:
            return func(scraper, *args, **kwargs)
        finally:
            self.return_scraper(scraper)
    
    def cleanup(self):
        """Close all scrapers."""
        while not self.pool.empty():
            scraper = self.pool.get()
            scraper.close_browser()

# Usage
pool = ScraperPool(pool_size=3)

def fetch_symbol(scraper, symbol):
    scraper.change_symbol(symbol)
    return scraper.get_historical_data(bars_count=100)

# Use pool
symbols = ["AAPL", "MSFT", "GOOGL"]
results = [pool.execute(fetch_symbol, symbol) for symbol in symbols]

pool.cleanup()
```

## 🔐 Security Considerations

```python
import os
from tvscraper import Scraper
from cryptography.fernet import Fernet

class SecureAgent:
    """Agent with security best practices."""
    
    def __init__(self):
        self.scraper = Scraper()
        self.api_key = self._load_api_key()
        
    def _load_api_key(self):
        """Load encrypted API key."""
        # Load from environment or encrypted file
        return os.getenv('TRADING_API_KEY')
    
    def save_data_securely(self, data, filename):
        """Save data with encryption."""
        # Implement encryption
        cipher = Fernet(self.api_key)
        encrypted_data = cipher.encrypt(str(data).encode())
        
        with open(filename, 'wb') as f:
            f.write(encrypted_data)
    
    def audit_log(self, action, details):
        """Log all actions for audit."""
        with open('audit.log', 'a') as f:
            f.write(f"{datetime.now()} | {action} | {details}\n")
```

## 📝 Summary

TVScraper is designed for seamless integration into:
- ✅ AI Agent workflows
- ✅ Automated trading systems
- ✅ Data collection pipelines
- ✅ Backtesting platforms
- ✅ Web APIs (FastAPI, Flask, Django)
- ✅ Multi-agent systems
- ✅ Scheduled tasks
- ✅ Real-time monitoring

**Key Principles:**
1. Initialize once, reuse scraper instance
2. Implement proper error handling and retries
3. Use connection pooling for concurrent access
4. Log all operations for debugging
5. Clean up resources on shutdown
6. Secure sensitive data and credentials

For more examples, see the `examples/` directory in the repository.
