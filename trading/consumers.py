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
        Run backtest and stream data sequentially
        
        Args:
            config: Backtest configuration dictionary
        """
        try:
            # Extract configuration with type conversion
            symbol = config.get("symbol", "AAPL")
            indicators = config.get("indicators", {})
            period = self.normalize_period(config.get("period", "6mo"))
            interval = config.get("interval", "1d")
            
            # Convert to proper types (frontend may send as strings)
            initial_balance = float(config.get("initial_balance", 10000))
            commission = float(config.get("commission", 0.002))
            slippage = float(config.get("slippage", 0.0005))

            # Initialize broker
            backtest_config = BacktestConfig(
                start_cash=initial_balance,
                fee_flat=1.0,
                fee_pct=commission,
                slippage_pct=slippage
            )
            broker = SimBroker(backtest_config)

            # Load data in streaming mode
            # Note: load_market_data returns a generator, not blocking
            data_stream = load_market_data(
                ticker=symbol,
                indicators=indicators,
                period=period,
                interval=interval,
                stream=True  # Enable streaming mode
            )

            # Get total bar count (we need to consume the generator to get this)
            # For now, we'll estimate or count in real-time
            total_bars_sent = 0

            # Send metadata
            await self.send(text_data=json.dumps({
                "type": "metadata",
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "total_bars": "streaming"  # Unknown until complete
            }))

            # Process each bar sequentially
            bar_number = 0
            for timestamp, market_data, progress_pct in data_stream:
                bar_number += 1

                # Extract candle data
                symbol_data = market_data.get(symbol, {})
                
                # Send candle data
                await self.send(text_data=json.dumps({
                    "type": "candle",
                    "bar_number": bar_number,
                    "progress": progress_pct,
                    "timestamp": str(timestamp),
                    "open": symbol_data.get("open"),
                    "high": symbol_data.get("high"),
                    "low": symbol_data.get("low"),
                    "close": symbol_data.get("close"),
                    "volume": symbol_data.get("volume"),
                }))

                # Execute strategy (if provided) and capture signals
                # Note: This would require strategy execution integration
                # For now, we'll simulate the broker stepping through
                broker.step_to(timestamp, market_data)

                # Check for new signals/trades
                recent_signals = self.get_recent_signals(broker)
                for signal in recent_signals:
                    await self.send(text_data=json.dumps({
                        "type": "signal",
                        "timestamp": str(timestamp),
                        "action": signal.get("action"),
                        "side": signal.get("side"),
                        "price": signal.get("price"),
                        "size": signal.get("size"),
                    }))

                # Send updated statistics
                metrics = broker.compute_metrics()
                await self.send(text_data=json.dumps({
                    "type": "stats",
                    "total_trades": metrics.get("total_trades", 0),
                    "winning_trades": metrics.get("winning_trades", 0),
                    "losing_trades": metrics.get("losing_trades", 0),
                    "pnl": metrics.get("net_profit", 0),
                }))

                # Small delay to simulate real-time streaming (adjust as needed)
                await asyncio.sleep(0.05)  # 50ms between candles

                total_bars_sent += 1

            # Send completion message
            final_metrics = broker.compute_metrics()
            await self.send(text_data=json.dumps({
                "type": "complete",
                "total_bars": total_bars_sent,
                "metrics": {
                    "total_trades": final_metrics.get("total_trades", 0),
                    "win_rate": final_metrics.get("win_rate", 0),
                    "net_profit": final_metrics.get("net_profit", 0),
                    "max_drawdown": final_metrics.get("max_drawdown_pct", 0),
                    "sharpe_ratio": final_metrics.get("sharpe_ratio", 0),
                }
            }))

            print(f"✅ Backtest streaming completed: {total_bars_sent} bars")

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
