"""
WebSocket Consumer for Real-time Backtest Streaming
Sends candle data and trade signals sequentially as the backtest runs
"""

import json
import asyncio
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


class BacktestStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that streams backtest progress in real-time
    """

    async def connect(self):
        """Accept WebSocket connection"""
        await self.accept()
        print("📡 WebSocket connected for backtest streaming")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        print(f"📡 WebSocket disconnected: {close_code}")

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
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(e)
            }))

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
            
            # Convert to proper types (frontend may send as strings)
            initial_balance = float(config.get("initial_balance", 10000))
            commission = float(config.get("commission", 0.002))
            slippage = float(config.get("slippage", 0.0005))
            
            # Send initial metadata
            await self.send(text_data=json.dumps({
                "type": "metadata",
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "status": "loading_data"
            }))
            
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
            
            # STEP 2: Run backtest with backtesting.py (if strategy provided)
            trades_list = []
            backtest_results = None
            
            if strategy_code:
                print(f"🚀 Running backtest with strategy...")
                await self.send(text_data=json.dumps({
                    "type": "metadata",
                    "status": "running_backtest",
                    "total_bars": total_bars
                }))
                
                # Parse and run strategy
                try:
                    # Try to parse as canonical JSON
                    canonical_json = json.loads(strategy_code) if isinstance(strategy_code, str) else strategy_code
                    
                    # Create strategy class from canonical
                    strategy_class = create_strategy_from_canonical(canonical_json)
                    
                    # Run backtest
                    adapter = BacktestingAdapter(
                        data=data_df,
                        strategy_class=strategy_class,
                        cash=initial_balance,
                        commission=commission
                    )
                    
                    backtest_results = adapter.run()
                    
                    # Extract trades
                    if hasattr(adapter.results, '_trades') and adapter.results._trades is not None:
                        trades_df = adapter.results._trades
                        # Convert trades to list of dicts with timestamps
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
                    
                    print(f"✅ Backtest complete: {len(trades_list)} trades")
                    
                except json.JSONDecodeError:
                    print("⚠️  Strategy code is not JSON, skipping backtest execution")
                except Exception as e:
                    print(f"⚠️  Error running backtest: {e}")
                    import traceback
                    traceback.print_exc()
            
            # STEP 3: Stream visualization with trade signals
            print(f"📺 Starting visualization stream...")
            await self.send(text_data=json.dumps({
                "type": "metadata",
                "status": "streaming_visualization",
                "total_bars": total_bars,
                "total_trades": len(trades_list)
            }))

            # Stream candles with trade signals
            bar_number = 0
            trades_sent = 0
            winning_trades = 0
            losing_trades = 0
            total_pnl = 0.0
            
            for idx, (timestamp, row) in enumerate(data_df.iterrows()):
                bar_number += 1
                progress_pct = (bar_number / total_bars) * 100
                
                # Send candle data
                await self.send(text_data=json.dumps({
                    "type": "candle",
                    "bar_number": bar_number,
                    "progress": progress_pct,
                    "timestamp": str(timestamp),
                    "open": float(row.get("open", row.get("Open", 0))),
                    "high": float(row.get("high", row.get("High", 0))),
                    "low": float(row.get("low", row.get("Low", 0))),
                    "close": float(row.get("close", row.get("Close", 0))),
                    "volume": float(row.get("volume", row.get("Volume", 0))),
                }))
                
                # Check for trades at this timestamp
                timestamp_str = str(timestamp)
                for trade in trades_list:
                    # Send entry signal
                    if trade['entry_time'] == timestamp_str:
                        side = "BUY" if trade['size'] > 0 else "SELL"
                        print(f"[SIGNAL] Sending {side} signal at {timestamp_str}: ${trade['entry_price']:.2f} x {abs(trade['size'])}")
                        await self.send(text_data=json.dumps({
                            "type": "signal",
                            "timestamp": timestamp_str,
                            "action": "ENTRY",
                            "side": side,
                            "price": trade['entry_price'],
                            "size": abs(trade['size']),
                        }))
                    
                    # Send exit signal
                    if trade['exit_time'] == timestamp_str:
                        trades_sent += 1
                        if trade['pnl'] > 0:
                            winning_trades += 1
                        else:
                            losing_trades += 1
                        total_pnl += trade['pnl']
                        
                        pnl_pct = (trade['pnl'] / trade['entry_price']) * 100 if trade['entry_price'] != 0 else 0
                        print(f"[SIGNAL] Sending EXIT signal at {timestamp_str}: ${trade['exit_price']:.2f} | PnL: ${trade['pnl']:.2f} ({pnl_pct:+.2f}%)")
                        await self.send(text_data=json.dumps({
                            "type": "signal",
                            "timestamp": timestamp_str,
                            "action": "EXIT",
                            "side": "CLOSE",
                            "price": trade['exit_price'],
                            "size": abs(trade['size']),
                        }))
                
                # Send updated statistics (every 10 bars or at trade)
                if bar_number % 10 == 0 or any(t['entry_time'] == timestamp_str or t['exit_time'] == timestamp_str for t in trades_list):
                    win_rate = (winning_trades / trades_sent * 100) if trades_sent > 0 else 0
                    await self.send(text_data=json.dumps({
                        "type": "stats",
                        "total_trades": trades_sent,
                        "winning_trades": winning_trades,
                        "losing_trades": losing_trades,
                        "pnl": total_pnl,
                        "win_rate": win_rate,
                    }))
                
                # Delay for visualization (adjust speed here)
                await asyncio.sleep(0.02)  # 20ms = faster, 50ms = slower
            
            # Send final completion message
            final_win_rate = (winning_trades / trades_sent * 100) if trades_sent > 0 else 0
            
            await self.send(text_data=json.dumps({
                "type": "complete",
                "total_bars": total_bars,
                "metrics": {
                    "total_trades": trades_sent,
                    "winning_trades": winning_trades,
                    "losing_trades": losing_trades,
                    "win_rate": final_win_rate,
                    "net_profit": total_pnl,
                    "max_drawdown": backtest_results.get("Max. Drawdown [%]", 0) if backtest_results is not None else 0,
                    "sharpe_ratio": backtest_results.get("Sharpe Ratio", 0) if backtest_results is not None else 0,
                }
            }))
            
            print(f"✅ Visualization streaming completed: {total_bars} bars, {trades_sent} trades")

        except Exception as e:
            print(f"❌ Backtest streaming error: {e}")
            import traceback
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(e)
            }))

    def get_recent_signals(self, broker: SimBroker) -> list:
        """
        Get recent signals from broker (signals that haven't been sent yet)
        
        This is a placeholder - you'll need to implement signal tracking
        in SimBroker or maintain a separate signal queue
        """
        # For now, return empty list
        # TODO: Implement signal tracking in SimBroker
        return []
