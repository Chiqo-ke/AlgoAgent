"""
WebSocket Consumer for Real-time Backtest Streaming
Sends candle data and trade signals sequentially as the backtest runs
"""

import json
import asyncio
import pandas as pd
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import sys
from pathlib import Path

# Add parent directory to path for Backtest imports
BACKTEST_DIR = Path(__file__).parent.parent.parent / "Backtest"
sys.path.insert(0, str(BACKTEST_DIR))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.data_loader import load_market_data
from Backtest.backtesting_adapter import (
    fetch_and_prepare_data,
    create_strategy_from_canonical,
    BacktestingAdapter
)

# Import the LatestBacktestResult model for database storage
try:
    from strategy_api.models import LatestBacktestResult, Strategy
except ImportError:
    LatestBacktestResult = None
    Strategy = None


class BacktestStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that streams backtest progress in real-time
    """

    async def connect(self):
        """Accept WebSocket connection"""
        self.is_connected = True
        await self.accept()
        print("📡 WebSocket connected for backtest streaming")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        self.is_connected = False
        print(f"📡 WebSocket disconnected: {close_code}")

    def normalize_timestamp(self, ts) -> str:
        """
        Normalize timestamp to a consistent format for comparison.
        Handles datetime objects, pandas Timestamps, and strings.
        Returns format: 'YYYY-MM-DD' for daily data or 'YYYY-MM-DD HH:MM:SS' for intraday
        """
        from datetime import datetime
        import pandas as pd
        
        if ts is None:
            return ''
        
        if isinstance(ts, str):
            # Replace 'T' with space for consistency
            ts = ts.replace('T', ' ')
            # Remove timezone info if present
            if '+' in ts:
                ts = ts.split('+')[0]
            if '.' in ts:
                ts = ts.split('.')[0]
            result = ts.strip()
            # If it's just a date (YYYY-MM-DD), keep it as is
            # If it has time component 00:00:00, strip it for daily data matching
            if ' 00:00:00' in result:
                result = result.replace(' 00:00:00', '')
            return result
        elif isinstance(ts, (datetime, pd.Timestamp)):
            # For daily data, just use date portion
            date_str = ts.strftime('%Y-%m-%d')
            time_str = ts.strftime('%H:%M:%S')
            if time_str == '00:00:00':
                return date_str
            return f"{date_str} {time_str}"
        else:
            result = str(ts).replace('T', ' ').split('+')[0].split('.')[0].strip()
            if ' 00:00:00' in result:
                result = result.replace(' 00:00:00', '')
            return result

    def pair_fills_to_trades(self, fills: list) -> list:
        """
        Convert individual fills (BUY/SELL orders) into round-trip trades.
        
        Each trade has an entry (BUY) and exit (SELL) pair.
        Returns list of trades with entry_time, exit_time, prices, and PnL.
        """
        trades = []
        pending_entry = None
        
        # Debug: show first few fills to understand structure
        if fills:
            print(f"📊 pair_fills_to_trades: Processing {len(fills)} fills")
            if isinstance(fills[0], dict):
                print(f"   First fill keys: {list(fills[0].keys())}")
            first = fills[0] if isinstance(fills[0], dict) else {}
            print(f"   First fill: side='{first.get('side', 'N/A')}', price={first.get('price', 'N/A')}, timestamp='{first.get('timestamp', 'N/A')}', realized_pnl={first.get('realized_pnl', 'N/A')}")
        else:
            print("📊 pair_fills_to_trades: No fills to process")
            return []
        
        for fill in fills:
            # Handle different side field variations
            side = str(fill.get('side', '')).upper().strip()
            
            # Normalize timestamp using helper method
            fill_time = self.normalize_timestamp(fill.get('timestamp', ''))
            
            if side in ('BUY', 'LONG', 'B'):
                # This is an entry
                pending_entry = {
                    'timestamp': fill_time,
                    'price': float(fill.get('price', 0)),
                    'size': float(fill.get('size', 0)),
                }
            elif side in ('SELL', 'SHORT', 'S') and pending_entry is not None:
                # This is an exit, pair with pending entry
                entry_price = pending_entry['price']
                exit_price = float(fill.get('price', 0))
                size = pending_entry['size']
                
                # Calculate PnL (for long position: exit - entry)
                pnl = (exit_price - entry_price) * size
                # Use realized_pnl from fill if available (more accurate)
                if fill.get('realized_pnl') is not None and fill.get('realized_pnl') != 0:
                    pnl = float(fill.get('realized_pnl'))
                
                trades.append({
                    'entry_time': pending_entry['timestamp'],
                    'exit_time': fill_time,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'size': size,
                    'pnl': pnl,
                    'return_pct': ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                })
                pending_entry = None
        
        print(f"📊 Paired {len(fills)} fills into {len(trades)} round-trip trades")
        
        # If pairing didn't work well, fall back to using individual fills with realized_pnl
        if len(trades) == 0 and len(fills) > 0:
            print("⚠️  Pairing failed, using individual fills as trades")
            for fill in fills:
                pnl = float(fill.get('realized_pnl', 0))
                # Only include fills that have realized PnL (indicating closed positions)
                if pnl != 0:
                    fill_time = self.normalize_timestamp(fill.get('timestamp', ''))
                    trades.append({
                        'entry_time': fill_time,
                        'exit_time': fill_time,
                        'entry_price': float(fill.get('price', 0)),
                        'exit_price': float(fill.get('price', 0)),
                        'size': float(fill.get('size', 0)),
                        'pnl': pnl,
                        'return_pct': 0
                    })
            print(f"📊 Created {len(trades)} trades from fills with realized_pnl")
        
        return trades

    @database_sync_to_async
    def save_backtest_result_to_db(self, strategy_id: int, result_data: dict) -> bool:
        """
        Save backtest result to database.
        Replaces any existing result for the same strategy.
        
        Args:
            strategy_id: The ID of the strategy
            result_data: Dictionary containing backtest results
        
        Returns:
            True if saved successfully, False otherwise
        """
        if LatestBacktestResult is None:
            print("⚠️  LatestBacktestResult model not available, skipping DB save")
            return False
        
        try:
            # Verify strategy exists
            if Strategy is None:
                print("⚠️  Strategy model not available, skipping DB save")
                return False
            
            if not Strategy.objects.filter(id=strategy_id).exists():
                print(f"⚠️  Strategy {strategy_id} not found, skipping DB save")
                return False
            
            # Save/update the result
            LatestBacktestResult.save_result(
                strategy_id=strategy_id,
                result_data=result_data
            )
            
            print(f"💾 Saved backtest result to database for strategy {strategy_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving backtest result to DB: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def safe_send(self, data: dict) -> bool:
        """
        Safely send data, checking connection state first.
        Returns True if send was successful, False otherwise.
        """
        if not getattr(self, 'is_connected', False):
            return False
        try:
            await self.send(text_data=json.dumps(data))
            return True
        except Exception as e:
            # Connection was closed
            self.is_connected = False
            return False

    async def receive(self, text_data):
        """
        Receive backtest configuration and start streaming
        
        Expected message format:
        {
            "action": "start_backtest",
            "config": {
                "strategy_code": "...",
                "symbol": "AAPL",
                "start_date": "2024-01-01",
                "end_date": "2024-10-31",
                "timeframe": "1d",
                "initial_balance": 10000,
                "lot_size": 1.0,
                "commission": 0.001,
                "slippage": 0.0005,
                "indicators": {
                    "RSI": {"timeperiod": 14},
                    "SMA": {"timeperiod": 20}
                }
            }
        }
        """
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "start_backtest":
                config = data.get("config", {})
                await self.run_backtest_stream(config)
            else:
                await self.safe_send({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })

        except Exception as e:
            await self.safe_send({
                "type": "error",
                "message": str(e)
            })

    def normalize_period(self, period: str) -> str:
        """
        Normalize period format for yfinance
        Converts frontend formats like '1year', '3months' to yfinance format like '1y', '3mo'
        """
        period_map = {
            '1day': '1d',
            '5days': '5d',
            '1month': '1mo',
            '3months': '3mo',
            '6months': '6mo',
            '1year': '1y',
            '2years': '2y',
            '5years': '5y',
            '10years': '10y',
            'ytd': 'ytd',
            'max': 'max',
        }
        return period_map.get(period.lower(), period)

    async def run_backtest_stream(self, config: dict):
        """
        Run backtest with backtesting.py and stream visualization
        
        Strategy:
        1. Load all data first
        2. Run backtest with backtesting.py (fast, gets all trades)
        3. Stream the candles + trade signals for visualization
        4. Save results to database (if strategy_id provided)
        
        Args:
            config: Backtest configuration dictionary
        """
        try:
            # Extract configuration with type conversion
            symbol = config.get("symbol", "AAPL")
            indicators = config.get("indicators", {})
            period = self.normalize_period(config.get("period", "6mo"))
            interval = config.get("interval", "1d")
            strategy_code = config.get("strategy_code")  # Strategy code or canonical JSON
            strategy_id = config.get("strategy_id")  # Strategy ID for database storage
            
            # Add default indicators if none provided (most strategies need these)
            # Use uppercase names and correct format for multi-period indicators
            if not indicators:
                indicators = {
                    'RSI': {'timeperiod': 14},
                    'EMA': {'periods': [9, 21]},
                    'SMA': {'periods': [20, 50]},
                }
                print(f"📊 Using default indicators: RSI(14), EMA(9,21), SMA(20,50)")
            
            # Convert to proper types (frontend may send as strings)
            initial_balance = float(config.get("initial_balance", 10000))
            lot_size = float(config.get("lot_size", 1.0))
            commission = float(config.get("commission", 0.002))
            slippage = float(config.get("slippage", 0.0005))
            
            print(f"💰 Backtest Configuration:")
            print(f"   Initial Balance: ${initial_balance:,.2f}")
            print(f"   Lot Size: {lot_size}")
            print(f"   Commission: {commission}")
            print(f"   Slippage: {slippage}")
            
            # Send initial metadata
            if not await self.safe_send({
                "type": "metadata",
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "status": "loading_data"
            }):
                print("⚠️  Client disconnected before streaming started")
                return
            
            # STEP 1: Load all data (not streaming, need full dataset for backtesting.py)
            print(f"📥 Loading data for {symbol}...")
            result = load_market_data(
                ticker=symbol,
                indicators=indicators,
                period=period,
                interval=interval,
                stream=False  # Get full dataframe
            )
            
            # Unpack result - load_market_data returns (df, ticker) tuple
            if isinstance(result, tuple):
                data_df, _ = result
            else:
                data_df = result
            
            total_bars = len(data_df)
            print(f"✅ Loaded {total_bars} bars")
            print(f"📊 DataFrame columns: {list(data_df.columns)}")
            print(f"✅ Loaded {total_bars} bars")
            
            # STEP 2: Run backtest with strategy (if strategy provided)
            trades_list = []
            backtest_results = None
            
            if strategy_code:
                print(f"🚀 Running backtest with strategy...")
                await self.safe_send({
                    "type": "metadata",
                    "status": "running_backtest",
                    "total_bars": total_bars
                })
                
                # Try to execute strategy
                try:
                    # First, try to parse as canonical JSON
                    is_json = False
                    try:
                        canonical_json = json.loads(strategy_code) if isinstance(strategy_code, str) else strategy_code
                        is_json = True
                    except (json.JSONDecodeError, TypeError):
                        is_json = False
                    
                    if is_json:
                        # Create strategy class from canonical JSON
                        strategy_class = create_strategy_from_canonical(canonical_json)
                        
                        # Run backtest
                        adapter = BacktestingAdapter(
                            data=data_df,
                            strategy_class=strategy_class,
                            cash=initial_balance,
                            commission=commission,
                            trade_on_close=True
                        )
                        
                        backtest_results = adapter.run()
                        
                        # Extract trades
                        if hasattr(adapter.results, '_trades') and adapter.results._trades is not None:
                            trades_df = adapter.results._trades
                            print(f"📋 Extracting {len(trades_df)} trades from backtesting.py results")
                            for _, trade in trades_df.iterrows():
                                trade_pnl = float(trade.get('PnL', 0))
                                trades_list.append({
                                    'entry_time': str(trade.get('EntryTime', '')),
                                    'exit_time': str(trade.get('ExitTime', '')),
                                    'entry_price': float(trade.get('EntryPrice', 0)),
                                    'exit_price': float(trade.get('ExitPrice', 0)),
                                    'size': float(trade.get('Size', 0)),
                                    'pnl': trade_pnl,
                                    'return_pct': float(trade.get('ReturnPct', 0))
                                })
                            total_pnl_from_trades = sum(t['pnl'] for t in trades_list)
                            print(f"💰 Total PnL from trades: ${total_pnl_from_trades:.2f}")
                        
                        print(f"✅ Backtest complete (JSON strategy): {len(trades_list)} trades")
                    
                    else:
                        # Execute Python strategy code directly
                        print("🐍 Executing Python strategy code...")
                        trades_list, backtest_results = await self.execute_python_strategy(
                            strategy_code=strategy_code,
                            data_df=data_df,
                            symbol=symbol,
                            initial_balance=initial_balance,
                            lot_size=lot_size,
                            commission=commission
                        )
                        print(f"✅ Backtest complete (Python strategy): {len(trades_list)} trades")
                    
                except Exception as e:
                    print(f"⚠️  Error running backtest: {e}")
                    import traceback
                    traceback.print_exc()
            
            # STEP 3: Stream visualization with trade signals
            print(f"📺 Starting visualization stream...")
            print(f"📊 Total trades to stream: {len(trades_list)}")
            
            # Pre-compute actual stats from trades_list (not dependent on timestamp matching)
            actual_total_trades = len(trades_list)
            actual_winning = sum(1 for t in trades_list if t.get('pnl', 0) > 0)
            actual_losing = sum(1 for t in trades_list if t.get('pnl', 0) <= 0)
            actual_pnl = sum(t.get('pnl', 0) for t in trades_list)
            actual_win_rate = (actual_winning / actual_total_trades * 100) if actual_total_trades > 0 else 0
            
            print(f"📊 Actual stats: {actual_total_trades} trades, {actual_winning} wins, {actual_losing} losses, PnL=${actual_pnl:.2f}, WinRate={actual_win_rate:.1f}%")
            
            # Send actual stats immediately so frontend shows real data
            await self.safe_send({
                "type": "stats",
                "total_trades": actual_total_trades,
                "winning_trades": actual_winning,
                "losing_trades": actual_losing,
                "pnl": actual_pnl,
                "win_rate": actual_win_rate,
            })
            
            if not await self.safe_send({
                "type": "metadata",
                "status": "streaming_visualization",
                "total_bars": total_bars,
                "total_trades": actual_total_trades
            }):
                print("⚠️  Client disconnected before visualization started")
                return

            # Stream candles with trade signals
            bar_number = 0
            trades_sent = 0
            winning_trades = 0
            losing_trades = 0
            total_pnl = 0.0
            
            # Debug: print trade timestamps and first DataFrame timestamp for comparison
            if trades_list:
                print(f"📊 Sample trade timestamps (first 3):")
                for t in trades_list[:3]:
                    print(f"   Entry: '{t['entry_time']}', Exit: '{t['exit_time']}', PnL: ${t['pnl']:.2f}")
            
            # Get first DataFrame timestamp for format comparison
            first_df_ts = data_df.index[0] if len(data_df) > 0 else None
            if first_df_ts is not None:
                normalized_first = self.normalize_timestamp(first_df_ts)
                print(f"📊 First DataFrame timestamp: raw='{first_df_ts}', normalized='{normalized_first}'")
            
            for idx, (timestamp, row) in enumerate(data_df.iterrows()):
                bar_number += 1
                progress_pct = (bar_number / total_bars) * 100
                
                # Normalize the DataFrame timestamp for comparison
                normalized_ts = self.normalize_timestamp(timestamp)
                
                # Send candle data - exit loop if client disconnected
                if not await self.safe_send({
                    "type": "candle",
                    "bar_number": bar_number,
                    "progress": progress_pct,
                    "timestamp": str(timestamp),
                    "open": float(row.get("open", row.get("Open", 0))),
                    "high": float(row.get("high", row.get("High", 0))),
                    "low": float(row.get("low", row.get("Low", 0))),
                    "close": float(row.get("close", row.get("Close", 0))),
                    "volume": float(row.get("volume", row.get("Volume", 0))),
                }):
                    print(f"⚠️  Client disconnected at bar {bar_number}/{total_bars}")
                    return
                
                # Check for trades at this timestamp using normalized comparison
                for trade in trades_list:
                    # Send entry signal
                    if trade['entry_time'] == normalized_ts:
                        side = "BUY" if trade['size'] > 0 else "SELL"
                        print(f"[SIGNAL] Sending {side} ENTRY at {normalized_ts}: ${trade['entry_price']:.2f} x {abs(trade['size'])}")
                        await self.safe_send({
                            "type": "signal",
                            "timestamp": str(timestamp),
                            "action": "ENTRY",
                            "side": side,
                            "price": trade['entry_price'],
                            "size": abs(trade['size']),
                        })
                    
                    # Send exit signal (use normalized timestamp for comparison)
                    if trade['exit_time'] == normalized_ts:
                        trades_sent += 1
                        if trade['pnl'] > 0:
                            winning_trades += 1
                        else:
                            losing_trades += 1
                        total_pnl += trade['pnl']
                        
                        pnl_pct = (trade['pnl'] / trade['entry_price']) * 100 if trade['entry_price'] != 0 else 0
                        print(f"[SIGNAL] Sending EXIT at {normalized_ts}: ${trade['exit_price']:.2f} | PnL: ${trade['pnl']:.2f} ({pnl_pct:+.2f}%)")
                        await self.safe_send({
                            "type": "signal",
                            "timestamp": str(timestamp),
                            "action": "EXIT",
                            "side": "CLOSE",
                            "price": trade['exit_price'],
                            "size": abs(trade['size']),
                            "pnl": trade['pnl'],
                        })
                
                # Send updated statistics periodically (use actual stats, not visualization-matched)
                # Every 50 bars, resend the actual stats so frontend stays updated
                if bar_number % 50 == 0:
                    await self.safe_send({
                        "type": "stats",
                        "total_trades": actual_total_trades,
                        "winning_trades": actual_winning,
                        "losing_trades": actual_losing,
                        "pnl": actual_pnl,
                        "win_rate": actual_win_rate,
                    })
                
                # Delay for visualization (adjust speed here)
                await asyncio.sleep(0.02)  # 20ms = faster, 50ms = slower
            
            # Calculate final equity
            final_equity = initial_balance + actual_pnl
            total_return_pct = (actual_pnl / initial_balance) * 100 if initial_balance > 0 else 0
            
            print(f"📤 Sending complete message with {len(trades_list)} trades")
            print(f"💰 Final Results:")
            print(f"   Initial Balance: ${initial_balance:,.2f}")
            print(f"   Total PnL: ${actual_pnl:.2f}")
            print(f"   Final Equity: ${final_equity:.2f}")
            print(f"   Return: {total_return_pct:.2f}%")
            
            # Send final completion message with ACTUAL stats (not visualization-matched)
            await self.safe_send({
                "type": "complete",
                "total_bars": total_bars,
                "metrics": {
                    "total_trades": actual_total_trades,
                    "winning_trades": actual_winning,
                    "losing_trades": actual_losing,
                    "win_rate": actual_win_rate,
                    "net_profit": actual_pnl,
                    "total_return_pct": total_return_pct,
                    "final_equity": final_equity,
                    "max_drawdown": backtest_results.get("Max. Drawdown [%]", 0) if backtest_results is not None else 0,
                    "sharpe_ratio": backtest_results.get("Sharpe Ratio", 0) if backtest_results is not None else 0,
                },
                "trades": trades_list,  # Include trades for visualization
            })
            
            # Also send final stats message so frontend updates
            await self.safe_send({
                "type": "stats",
                "total_trades": actual_total_trades,
                "winning_trades": actual_winning,
                "losing_trades": actual_losing,
                "pnl": actual_pnl,
                "win_rate": actual_win_rate,
            })
            
            print(f"✅ Visualization streaming completed: {total_bars} bars, {actual_total_trades} trades (actual)")
            
            # Save results to database if strategy_id is provided
            if strategy_id:
                try:
                    strategy_id_int = int(strategy_id)
                    result_data = {
                        'symbol': symbol,
                        'timeframe': interval,
                        'period': period,
                        'initial_balance': initial_balance,
                        'lot_size': lot_size,
                        'commission': commission,
                        'total_trades': actual_total_trades,
                        'winning_trades': actual_winning,
                        'losing_trades': actual_losing,
                        'win_rate': actual_win_rate,
                        'net_profit': actual_pnl,
                        'total_return_pct': total_return_pct,
                        'final_equity': final_equity,
                        'max_drawdown': backtest_results.get("Max. Drawdown [%]", 0) if backtest_results else 0,
                        'sharpe_ratio': backtest_results.get("Sharpe Ratio", 0) if backtest_results else 0,
                        'trades': trades_list,
                        'equity_curve': [],  # Could add equity curve data here
                    }
                    
                    await self.save_backtest_result_to_db(strategy_id_int, result_data)
                    
                except (ValueError, TypeError) as e:
                    print(f"⚠️  Invalid strategy_id '{strategy_id}', skipping DB save: {e}")
            else:
                print("ℹ️  No strategy_id provided, skipping DB save")

        except Exception as e:
            print(f"❌ Backtest streaming error: {e}")
            import traceback
            traceback.print_exc()
            # Try to send error, but don't fail if client disconnected
            await self.safe_send({
                "type": "error",
                "message": str(e)
            })

    def get_recent_signals(self, broker: SimBroker) -> list:
        """
        Get recent signals from broker (signals that haven't been sent yet)
        
        This is a placeholder - you'll need to implement signal tracking
        in SimBroker or maintain a separate signal queue
        """
        # For now, return empty list
        # TODO: Implement signal tracking in SimBroker
        return []

    async def execute_python_strategy(
        self,
        strategy_code: str,
        data_df,
        symbol: str,
        initial_balance: float,
        lot_size: float,
        commission: float
    ) -> tuple:
        """
        Execute Python strategy code directly
        
        Args:
            strategy_code: Python strategy code string
            data_df: Market data DataFrame
            symbol: Trading symbol
            initial_balance: Starting cash
            lot_size: Position size for trades
            commission: Commission rate
            
        Returns:
            Tuple of (trades_list, backtest_results)
        """
        import tempfile
        import importlib.util
        import os
        import sys
        import inspect
        from datetime import datetime
        
        trades_list = []
        backtest_results = None
        
        # Create temporary file with Python code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(strategy_code)
            strategy_file = f.name
        
        try:
            # Load strategy module
            spec = importlib.util.spec_from_file_location("ws_strategy_module", strategy_file)
            if not spec or not spec.loader:
                raise ValueError("Failed to load strategy module")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules['ws_strategy_module'] = module
            spec.loader.exec_module(module)
            
            # Try to find Strategy class (for backtesting.py framework)
            strategy_class = None
            uses_backtesting_py = False
            
            try:
                from backtesting import Backtest, Strategy as BacktestStrategy
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BacktestStrategy) and 
                        attr is not BacktestStrategy):
                        strategy_class = attr
                        uses_backtesting_py = True
                        print(f"📊 Found backtesting.py strategy class: {attr_name}")
                        break
            except ImportError:
                print("ℹ️  backtesting.py not available, trying SimBroker")
            
            # If not backtesting.py, try SimBroker framework
            if not strategy_class:
                for attr_name in dir(module):
                    if attr_name.startswith('_'):
                        continue
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and hasattr(attr, '__init__'):
                        # Check if it looks like a strategy (has broker/symbol params)
                        sig = inspect.signature(attr.__init__)
                        params = list(sig.parameters.keys())
                        if 'broker' in params or 'symbol' in params:
                            strategy_class = attr
                            print(f"📊 Found SimBroker strategy class: {attr_name}")
                            break
            
            if not strategy_class:
                raise ValueError("No Strategy class found in code")
            
            # Execute based on framework
            if uses_backtesting_py:
                # Use backtesting.py framework
                from backtesting import Backtest
                
                bt = Backtest(
                    data_df,
                    strategy_class,
                    cash=initial_balance,
                    commission=commission,
                    exclusive_orders=True
                )
                
                stats = bt.run()
                
                # Store results
                backtest_results = {
                    'Return [%]': stats.get('Return [%]', 0),
                    'Max. Drawdown [%]': stats.get('Max. Drawdown [%]', 0),
                    'Sharpe Ratio': stats.get('Sharpe Ratio', 0),
                    '# Trades': stats.get('# Trades', 0),
                    'Win Rate [%]': stats.get('Win Rate [%]', 0),
                    'Equity Final [$]': stats.get('Equity Final [$]', initial_balance),
                }
                
                # Extract trades
                if hasattr(stats, '_trades') and stats._trades is not None and len(stats._trades) > 0:
                    trades_df = stats._trades
                    for _, trade in trades_df.iterrows():
                        trades_list.append({
                            'entry_time': str(trade.get('EntryTime', '')),
                            'exit_time': str(trade.get('ExitTime', '')),
                            'entry_price': float(trade.get('EntryPrice', 0)),
                            'exit_price': float(trade.get('ExitPrice', 0)),
                            'size': float(trade.get('Size', 0)),
                            'pnl': float(trade.get('PnL', 0)),
                            'return_pct': float(trade.get('ReturnPct', 0))
                        })
            else:
                # Use SimBroker framework
                from Backtest.sim_broker import SimBroker
                from Backtest.config import BacktestConfig
                
                config = BacktestConfig()
                config.start_cash = initial_balance
                config.fee_pct = commission
                
                broker = SimBroker(config)
                
                # Initialize strategy with lot_size if it accepts it
                strategy_sig = inspect.signature(strategy_class.__init__)
                strategy_params = list(strategy_sig.parameters.keys())
                
                if 'lot_size' in strategy_params:
                    strategy = strategy_class(broker=broker, symbol=symbol, lot_size=lot_size)
                else:
                    strategy = strategy_class(broker=broker, symbol=symbol)
                
                # Run backtest bar by bar
                for idx, row in data_df.iterrows():
                    # Build market data dict with OHLCV and indicators
                    symbol_data = {
                        'open': float(row.get('Open', row.get('open', 0))),
                        'high': float(row.get('High', row.get('high', 0))),
                        'low': float(row.get('Low', row.get('low', 0))),
                        'close': float(row.get('Close', row.get('close', 0))),
                        'volume': float(row.get('Volume', row.get('volume', 0)))
                    }
                    
                    # Add any indicator columns from the dataframe
                    for col in row.index:
                        col_lower = col.lower()
                        if any(ind in col_lower for ind in ['rsi', 'ema', 'sma', 'macd', 'bb', 'atr']):
                            try:
                                symbol_data[col_lower] = float(row[col]) if pd.notna(row[col]) else None
                            except (ValueError, TypeError):
                                pass
                    
                    market_data = {symbol: symbol_data}
                    
                    timestamp = idx if isinstance(idx, datetime) else datetime.fromisoformat(str(idx))
                    
                    # Call strategy's on_bar method (SimBroker strategies use on_bar)
                    if hasattr(strategy, 'on_bar'):
                        strategy.on_bar(timestamp, market_data)
                    elif hasattr(strategy, 'on_data'):
                        strategy.on_data(row, timestamp)
                    
                    # Then advance broker to process any signals
                    broker.step_to(timestamp, market_data)
                
                # Finalize strategy if it has a finalize method
                if hasattr(strategy, 'finalize'):
                    strategy.finalize()
                
                # Get results
                snapshot = broker.get_account_snapshot()
                final_equity = snapshot.get('equity', initial_balance)
                fills = broker.get_trade_log()
                
                print(f"📈 SimBroker results:")
                print(f"   Starting Balance: ${initial_balance:,.2f}")
                print(f"   Final Equity: ${final_equity:,.2f}")
                print(f"   Total Fills: {len(fills)}")
                print(f"   P&L: ${final_equity - initial_balance:,.2f}")
                
                total_return = ((final_equity - initial_balance) / initial_balance) * 100
                winning = [t for t in fills if t.get('pnl', t.get('realized_pnl', 0)) > 0]
                win_rate = (len(winning) / len(fills) * 100) if fills else 0
                
                backtest_results = {
                    'Return [%]': total_return,
                    'Max. Drawdown [%]': 0,
                    'Sharpe Ratio': 0,
                    '# Trades': len(fills),
                    'Win Rate [%]': win_rate,
                    'Equity Final [$]': final_equity,
                }
                
                # Convert fills to round-trip trades format
                # Pair BUY (entry) with SELL (exit) fills to create complete trades
                trades_list = self.pair_fills_to_trades(fills)
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(strategy_file)
                if 'ws_strategy_module' in sys.modules:
                    del sys.modules['ws_strategy_module']
            except Exception as cleanup_error:
                print(f"⚠️  Cleanup warning: {cleanup_error}")
        
        return trades_list, backtest_results
