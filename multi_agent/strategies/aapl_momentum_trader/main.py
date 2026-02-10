import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading
import signal
import sys

from config import *
from data_manager import DataManager
from indicators import SignalGenerator
from risk_management import RiskManager, PositionManager
from mt5_trader import MT5Trader
from backtester import Backtester

class AAPLMomentumStrategy:
    """AAPL Momentum Trading Strategy - Main Strategy Class"""
    
    def __init__(self, mode: str = 'backtest', config: dict = None):
        """
        Initialize the strategy
        
        Args:
            mode: 'backtest', 'live', or 'demo'
            config: Configuration dictionary
        """
        self.mode = mode
        self.config = config or {}
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.data_manager = None
        self.signal_generator = None
        self.risk_manager = None
        self.position_manager = None
        self.trader = None
        self.backtester = None
        
        self._initialize_components()
        
        # Signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, LOGGING_CONFIG['level']),
            format=LOGGING_CONFIG['format'],
            handlers=[
                logging.FileHandler(LOGGING_CONFIG['file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _initialize_components(self):
        """Initialize all strategy components"""
        try:
            # Data Manager
            if self.mode == 'live' or self.mode == 'demo':
                self.data_manager = DataManager(
                    provider_type="mt5",
                    **MT5_CONFIG
                )
            else:  # backtest
                self.data_manager = DataManager(provider_type="yfinance")
            
            # Signal Generator
            self.signal_generator = SignalGenerator(
                rsi_period=STRATEGY_CONFIG['rsi_period'],
                sma_period=STRATEGY_CONFIG['sma_period'],
                rsi_long_threshold=STRATEGY_CONFIG['rsi_long_threshold'],
                rsi_short_threshold=STRATEGY_CONFIG['rsi_short_threshold']
            )
            
            # Risk Manager
            self.risk_manager = RiskManager(
                risk_per_trade=RISK_CONFIG['risk_per_trade'],
                max_positions=RISK_CONFIG['max_positions'],
                stop_loss_pips=RISK_CONFIG['stop_loss_pips'],
                take_profit_ratio=RISK_CONFIG['take_profit_ratio'],
                max_spread=RISK_CONFIG['max_spread']
            )
            
            # Position Manager
            self.position_manager = PositionManager()
            
            # Live Trader (only for live/demo mode)
            if self.mode == 'live' or self.mode == 'demo':
                self.trader = MT5Trader(**MT5_CONFIG)
            
            # Backtester (only for backtest mode)
            if self.mode == 'backtest':
                self.backtester = Backtester(
                    initial_balance=BACKTEST_CONFIG['initial_balance'],
                    commission=BACKTEST_CONFIG['commission'],
                    slippage=BACKTEST_CONFIG['slippage']
                )
            
            self.logger.info(f"Strategy initialized in {self.mode} mode")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize strategy: {e}")
            raise
    
    def run_backtest(self) -> Dict:
        """Run backtest on historical data"""
        if self.mode != 'backtest':
            raise ValueError("Backtest mode required for backtesting")
        
        self.logger.info("Starting backtest...")
        
        try:
            # Get historical data
            data = self.data_manager.get_data(
                symbol=STRATEGY_CONFIG['symbol'],
                timeframe=STRATEGY_CONFIG['timeframe'],
                start_date=BACKTEST_CONFIG['start_date'],
                end_date=BACKTEST_CONFIG['end_date']
            )
            
            if data.empty:
                raise ValueError("No historical data available")
            
            # Validate and clean data
            if not self.data_manager.validate_data(data):
                self.logger.warning("Data validation failed, attempting to clean...")
                data = self.data_manager.cleanup_data(data)
            
            self.logger.info(f"Loaded {len(data)} bars of historical data")
            
            # Generate signals
            signals_df = self.signal_generator.generate_signals(data)
            
            # Run backtest
            results = self.backtester.run_backtest(
                data, signals_df, self.risk_manager, self.position_manager
            )
            
            # Generate report
            report = self.backtester.generate_report(results)
            print(report)
            
            # Plot results
            try:
                self.backtester.plot_results(results, 'backtest_results.png')
            except Exception as e:
                self.logger.warning(f"Failed to generate plots: {e}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {e}")
            raise
    
    def run_live(self):
        """Run live trading"""
        if self.mode not in ['live', 'demo']:
            raise ValueError("Live or demo mode required for live trading")
        
        self.logger.info("Starting live trading...")
        
        try:
            # Connect to MT5
            if not self.trader.connect():
                raise ConnectionError("Failed to connect to MT5")
            
            # Get account info
            account_info = self.trader.get_account_info()
            self.logger.info(f"Account Balance: ${account_info.get('balance', 0):.2f}")
            
            self.running = True
            
            # Main trading loop
            while self.running:
                try:
                    self._trading_cycle()
                    time.sleep(60)  # Wait 1 minute between cycles
                    
                except KeyboardInterrupt:
                    self.logger.info("Received interrupt signal")
                    break
                except Exception as e:
                    self.logger.error(f"Error in trading cycle: {e}")
                    time.sleep(60)
            
        except Exception as e:
            self.logger.error(f"Live trading failed: {e}")
            raise
        finally:
            if self.trader:
                self.trader.disconnect()
            self.logger.info("Live trading stopped")
    
    def _trading_cycle(self):
        """Single trading cycle"""
        try:
            # Get current market data
            data = self.data_manager.get_data(
                symbol=STRATEGY_CONFIG['symbol'],
                timeframe=STRATEGY_CONFIG['timeframe'],
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                live=True,
                bars=100
            )
            
            if data.empty:
                self.logger.warning("No market data available")
                return
            
            # Generate signals on latest data
            signals_df = self.signal_generator.generate_signals(data)
            latest_signal = signals_df['signal'].iloc[-1]
            
            if latest_signal == 0:
                self.logger.debug("No trading signal")
                return
            
            # Get current price and market info
            current_price = data['close'].iloc[-1]
            symbol_info = self.trader.get_symbol_info(STRATEGY_CONFIG['symbol'])
            market_price = self.trader.get_market_price(STRATEGY_CONFIG['symbol'])
            
            if not symbol_info or not market_price:
                self.logger.warning("Failed to get market information")
                return
            
            # Check current positions
            current_positions = self.trader.get_positions(STRATEGY_CONFIG['symbol'])
            
            # Update position manager with live positions
            self._sync_positions(current_positions)
            
            # Check for position exits
            self._check_position_exits(current_positions, current_price)
            
            # Check for new entries
            if len(current_positions) < self.risk_manager.max_positions:
                self._check_new_entry(signals_df, symbol_info, market_price)
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")
    
    def _sync_positions(self, mt5_positions: list):
        """Sync position manager with MT5 positions"""
        # Clear position manager and rebuild from MT5
        self.position_manager.positions.clear()
        
        for pos in mt5_positions:
            position_id = f"MT5_{pos['ticket']}"
            self.position_manager.positions[position_id] = {
                'id': position_id,
                'symbol': pos['symbol'],
                'direction': pos['type'],
                'entry_price': pos['price_open'],
                'volume': pos['volume'],
                'stop_loss': pos.get('sl', 0),
                'take_profit': pos.get('tp', 0),
                'entry_time': pos['time'],
                'status': 'open',
                'unrealized_pnl': pos.get('profit', 0),
                'mt5_ticket': pos['ticket']
            }
    
    def _check_position_exits(self, positions: list, current_price: float):
        """Check if any positions should be closed"""
        for pos in positions:
            # Check stop loss and take profit (handled by MT5)
            # Additional exit logic can be added here
            
            # Example: Time-based exit after 24 hours
            entry_time = pos['time']
            if (datetime.now() - entry_time).total_seconds() > 86400:  # 24 hours
                self.logger.info(f"Closing position {pos['ticket']} - Time exit")
                result = self.trader.close_position(pos['ticket'])
                if result['success']:
                    self.logger.info(f"Position {pos['ticket']} closed successfully")
                else:
                    self.logger.error(f"Failed to close position: {result['error']}")
    
    def _check_new_entry(self, signals_df: pd.DataFrame, symbol_info: dict, market_price: dict):
        """Check for new entry opportunities"""
        latest_signal = signals_df['signal'].iloc[-1]
        
        if latest_signal == 0:
            return
        
        # Calculate signal strength
        rsi = signals_df['rsi'].iloc[-1]
        current_price = signals_df['close'].iloc[-1]
        sma = signals_df['sma20'].iloc[-1]
        atr = signals_df['atr'].iloc[-1]
        
        signal_strength = self.signal_generator.get_signal_strength(rsi, current_price, sma)
        spread = market_price['spread']
        
        # Validate trade
        is_valid, reason = self.risk_manager.validate_trade(
            signal_strength, spread, len(self.position_manager.positions)
        )
        
        if not is_valid:
            self.logger.info(f"Trade not valid: {reason}")
            return
        
        # Determine direction and prices
        direction = 'long' if latest_signal > 0 else 'short'
        order_type = 'buy' if direction == 'long' else 'sell'
        entry_price = market_price['ask'] if direction == 'long' else market_price['bid']
        
        # Calculate position parameters
        stop_loss = self.risk_manager.calculate_stop_loss(entry_price, direction, atr)
        take_profit = self.risk_manager.calculate_take_profit(entry_price, stop_loss, direction)
        
        # Get account balance
        account_info = self.trader.get_account_info()
        balance = account_info.get('balance', 0)
        
        # Calculate position size
        volume = self.risk_manager.calculate_position_size(
            balance, entry_price, stop_loss, symbol_info
        )
        
        # Place order
        self.logger.info(f"Placing {direction} order: {volume} lots @ {entry_price:.5f}")
        
        result = self.trader.place_order(
            symbol=STRATEGY_CONFIG['symbol'],
            order_type=order_type,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
            comment=f"AAPL Momentum {direction.upper()}"
        )
        
        if result['success']:
            self.logger.info(f"Order placed successfully: {result}")
        else:
            self.logger.error(f"Failed to place order: {result['error']}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def get_status(self) -> Dict:
        """Get current strategy status"""
        status = {
            'mode': self.mode,
            'running': self.running,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.trader and self.trader.connected:
            account_info = self.trader.get_account_info()
            positions = self.trader.get_positions()
            
            status.update({
                'account_balance': account_info.get('balance', 0),
                'account_equity': account_info.get('equity', 0),
                'open_positions': len(positions),
                'positions': positions
            })
        
        if self.position_manager:
            stats = self.position_manager.get_statistics()
            status.update({
                'trade_statistics': stats
            })
        
        return status
    
    def stop(self):
        """Stop the strategy"""
        self.running = False
        if self.trader:
            self.trader.disconnect()

def main():
    """Main function to run the strategy"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AAPL Momentum Trading Strategy')
    parser.add_argument('--mode', choices=['backtest', 'demo', 'live'], 
                       default='backtest', help='Trading mode')
    parser.add_argument('--config', type=str, help='Path to config file')
    
    args = parser.parse_args()
    
    try:
        # Initialize strategy
        strategy = AAPLMomentumStrategy(mode=args.mode)
        
        if args.mode == 'backtest':
            # Run backtest
            results = strategy.run_backtest()
            print(f"Backtest completed. Total return: {results.get('total_return_pct', 0):.2f}%")
        
        else:
            # Run live trading
            print(f"Starting {args.mode} trading...")
            strategy.run_live()
    
    except KeyboardInterrupt:
        print("\nStrategy stopped by user")
    except Exception as e:
        print(f"Strategy failed: {e}")

if __name__ == "__main__":
    main()