"""
Live Trader - Main trading loop and orchestration
"""
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import logging

from config import LiveConfig, setup_logging, MT5Constants
from mt5_connector import MT5Connector, MT5ConnectionError
from order_executor import OrderExecutor
from state_manager import StateManager
from audit_logger import AuditLogger
from backtesting_bridge import BacktestingBridge, get_strategy_from_file

logger = logging.getLogger('LiveTrader')


class LiveTrader:
    """
    Main live trading orchestrator
    """
    
    def __init__(self, config: LiveConfig, strategy_path: str):
        """
        Initialize live trader
        
        Args:
            config: Live trading configuration
            strategy_path: Path to strategy file
        """
        self.config = config
        self.strategy_path = strategy_path
        self.running = False
        self.shutdown_requested = False
        
        # Initialize components
        logger.info("Initializing Live Trader...")
        
        self.connector = MT5Connector(config)
        self.executor = OrderExecutor(config, self.connector)
        self.state = StateManager(config)
        self.audit = AuditLogger(config.audit_db_path)
        
        # Load strategy
        logger.info(f"Loading strategy from: {strategy_path}")
        strategy_class = get_strategy_from_file(strategy_path)
        self.bridge = BacktestingBridge(strategy_class)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("✓ Live Trader initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    def start(self):
        """Start the live trading loop"""
        try:
            # Initialize MT5 connection
            if not self.connector.initialize():
                logger.error("Failed to initialize MT5 connection")
                return False
            
            # Sync state with MT5
            self._sync_state()
            
            # Log startup event
            self.audit.log_event(
                event_type='STARTUP',
                severity='INFO',
                message='Live trader started',
                details=self.config.to_dict()
            )
            
            self.running = True
            logger.info("🚀 Live Trader started")
            logger.info(f"   Mode: {'DRY RUN' if self.config.dry_run else 'LIVE'}")
            logger.info(f"   Symbols: {', '.join(self.config.symbols)}")
            logger.info(f"   Interval: {self.config.interval_seconds}s")
            logger.info(f"   Strategy: {self.bridge.strategy_class.__name__}")
            
            # Main trading loop
            self._run_loop()
            
            return True
        
        except Exception as e:
            logger.error(f"Startup failed: {e}", exc_info=True)
            self.audit.log_event(
                event_type='STARTUP_ERROR',
                severity='CRITICAL',
                message=str(e)
            )
            return False
        
        finally:
            self._shutdown()
    
    def _run_loop(self):
        """Main trading loop"""
        iteration = 0
        last_snapshot_time = datetime.now()
        
        while self.running and not self.shutdown_requested:
            iteration += 1
            loop_start = datetime.now()
            
            try:
                logger.info(f"--- Iteration {iteration} ({loop_start.strftime('%Y-%m-%d %H:%M:%S')}) ---")
                
                # Check kill switch
                if self._check_kill_switch():
                    logger.critical("🚨 Kill switch activated - stopping trading")
                    break
                
                # Check if trading is allowed
                can_trade, reason = self.state.can_trade()
                if not can_trade:
                    logger.warning(f"Trading not allowed: {reason}")
                    time.sleep(self.config.interval_seconds)
                    continue
                
                # Check connection health
                if not self.connector.ensure_connected():
                    logger.error("Connection lost and reconnection failed")
                    self.audit.log_event(
                        event_type='CONNECTION_LOST',
                        severity='ERROR',
                        message='Failed to maintain MT5 connection'
                    )
                    time.sleep(self.config.interval_seconds)
                    continue
                
                # Sync state periodically
                self._sync_state()
                
                # Process each symbol
                for symbol in self.config.symbols:
                    try:
                        self._process_symbol(symbol)
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}", exc_info=True)
                        self.audit.log_event(
                            event_type='PROCESSING_ERROR',
                            severity='ERROR',
                            message=f"Error processing {symbol}: {str(e)}"
                        )
                
                # Take account snapshot periodically (every 5 minutes)
                if (datetime.now() - last_snapshot_time).seconds >= 300:
                    self._take_account_snapshot()
                    last_snapshot_time = datetime.now()
                
                # Calculate sleep time
                loop_duration = (datetime.now() - loop_start).total_seconds()
                sleep_time = max(0, self.config.interval_seconds - loop_duration)
                
                logger.info(f"Loop completed in {loop_duration:.2f}s, sleeping {sleep_time:.2f}s")
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            except Exception as e:
                logger.error(f"Loop iteration error: {e}", exc_info=True)
                self.audit.log_event(
                    event_type='LOOP_ERROR',
                    severity='ERROR',
                    message=str(e)
                )
                time.sleep(self.config.interval_seconds)
    
    def _process_symbol(self, symbol: str):
        """
        Process trading signals for a symbol
        
        Args:
            symbol: Trading symbol
        """
        logger.info(f"Processing {symbol}...")
        
        # Get symbol info
        symbol_info = self.connector.get_symbol_info(symbol)
        if not symbol_info:
            logger.warning(f"Could not get symbol info for {symbol}")
            return
        
        # Generate signals
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)  # Look at last day of data
        
        try:
            signals = self.bridge.generate_signals(
                symbol=symbol,
                from_ts=start_time,
                to_ts=end_time,
                timeframe=self.config.timeframe
            )
            
            if signals.empty:
                logger.info(f"No signals generated for {symbol}")
                return
            
            # Get the latest signal
            latest_signal = signals.iloc[-1]
            signal_id = f"{symbol}_{latest_signal.name.strftime('%Y%m%d%H%M%S')}"
            
            # Check if signal already processed
            if self.state.is_signal_processed(signal_id):
                logger.debug(f"Signal already processed: {signal_id}")
                return
            
            # Log signal
            self.audit.log_signal(
                signal_id=signal_id,
                symbol=symbol,
                signal_type=latest_signal['signal'],
                confidence=latest_signal['confidence'],
                price=latest_signal['price'],
                strategy_id=latest_signal['strategy_id']
            )
            
            # Mark as processed
            self.state.mark_signal_processed(signal_id)
            self.state.update_last_signal_time(symbol)
            
            # Process signal
            if latest_signal['signal'] in ['BUY', 'SELL']:
                self._execute_signal(signal_id, symbol, latest_signal, symbol_info)
            else:
                logger.info(f"HOLD signal for {symbol}")
        
        except Exception as e:
            logger.error(f"Signal generation failed for {symbol}: {e}", exc_info=True)
    
    def _execute_signal(self, signal_id: str, symbol: str, signal, symbol_info: dict):
        """
        Execute a trading signal
        
        Args:
            signal_id: Signal identifier
            symbol: Trading symbol
            signal: Signal data (pandas Series)
            symbol_info: MT5 symbol information
        """
        signal_type = signal['signal']
        logger.info(f"Executing {signal_type} signal for {symbol}")
        
        # Check if we already have a position
        has_position = self.state.has_position(symbol)
        
        if signal_type == 'BUY' and has_position:
            logger.info(f"Already have position in {symbol}, skipping BUY signal")
            return
        
        if signal_type == 'SELL' and has_position:
            # This is an exit signal - close position
            self._close_position(symbol, signal, symbol_info)
            return
        
        # Calculate position size
        account = self.connector.get_account_info()
        if not account:
            logger.error("Could not get account info")
            return
        
        # Simple stop loss calculation (could be enhanced)
        entry_price = symbol_info['ask'] if signal_type == 'BUY' else symbol_info['bid']
        stop_loss_price = entry_price * 0.98 if signal_type == 'BUY' else entry_price * 1.02
        
        volume = self.bridge.position_size(
            account_balance=account['balance'],
            risk_pct=self.config.default_risk_pct,
            stop_loss_price=stop_loss_price,
            entry_price=entry_price,
            symbol=symbol
        )
        
        # Limit position size
        volume = min(volume, self.config.max_position_size)
        
        # Build order request
        order_request = self.bridge.build_order_request(
            signal_row=signal,
            volume=volume,
            meta={
                'symbol': symbol,
                'magic': self.config.magic_number,
                'deviation': 20,
                'sl': stop_loss_price,
                'comment': f"{self.config.strategy_id}_{signal_id}"
            },
            symbol_info=symbol_info
        )
        
        # Pre-check with backtesting bridge
        precheck = self.bridge.simulate_precheck(order_request, account)
        if not precheck['pass']:
            logger.error(f"Precheck failed: {precheck['reason']}")
            self.audit.log_event(
                event_type='PRECHECK_FAILED',
                severity='WARNING',
                message=precheck['reason'],
                details={'order_request': order_request}
            )
            return
        
        if precheck['warnings']:
            for warning in precheck['warnings']:
                logger.warning(f"Precheck warning: {warning}")
        
        # Log order
        client_order_id = self.executor.generate_client_order_id(symbol, signal_id)
        self.audit.log_order(
            client_order_id=client_order_id,
            signal_id=signal_id,
            symbol=symbol,
            order_type='MARKET',
            side=signal_type,
            volume=volume,
            price=entry_price,
            sl=stop_loss_price
        )
        
        # Execute order
        result = self.executor.execute_order(order_request, client_order_id)
        
        # Update audit log
        self.audit.update_order(
            client_order_id=client_order_id,
            status='EXECUTED' if result['success'] else 'FAILED',
            mt5_order_id=result.get('mt5_order_id'),
            mt5_deal_id=result.get('mt5_deal_id'),
            executed_price=result.get('executed_price'),
            executed_volume=result.get('executed_volume'),
            retcode=result.get('retcode'),
            retcode_message=result.get('retcode_message'),
            attempts=result.get('attempts'),
            error_message=result.get('message') if not result['success'] else None
        )
        
        # Update state
        if result['success']:
            self.state.update_position(symbol, {
                'ticket': result.get('mt5_order_id'),
                'symbol': symbol,
                'type': signal_type,
                'volume': volume,
                'price_open': result.get('executed_price', entry_price),
                'sl': stop_loss_price,
                'open_time': datetime.now()
            })
            logger.info(f"✓ Position opened: {symbol} {signal_type} {volume} @ {entry_price:.5f}")
        else:
            logger.error(f"✗ Order execution failed: {result.get('message')}")
    
    def _close_position(self, symbol: str, signal, symbol_info: dict):
        """Close an existing position"""
        position = self.state.get_position(symbol)
        if not position:
            logger.warning(f"No position found for {symbol}")
            return
        
        logger.info(f"Closing position: {symbol}")
        
        # Build close order (opposite direction)
        close_type = 'SELL' if position['type'] == 'BUY' else 'BUY'
        close_price = symbol_info['bid'] if close_type == 'SELL' else symbol_info['ask']
        
        order_request = {
            'action': MT5Constants.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': position['volume'],
            'type': MT5Constants.ORDER_TYPE_SELL if close_type == 'SELL' else MT5Constants.ORDER_TYPE_BUY,
            'price': close_price,
            'deviation': 20,
            'magic': self.config.magic_number,
            'comment': f"Close_{position.get('ticket', 'unknown')}",
            'type_time': MT5Constants.ORDER_TIME_GTC,
            'type_filling': MT5Constants.ORDER_FILLING_IOC,
        }
        
        # Execute close
        result = self.executor.execute_order(order_request)
        
        if result['success']:
            # Calculate profit
            if position['type'] == 'BUY':
                profit = (close_price - position['price_open']) * position['volume'] * symbol_info['trade_contract_size']
            else:
                profit = (position['price_open'] - close_price) * position['volume'] * symbol_info['trade_contract_size']
            
            # Record trade
            duration = (datetime.now() - position['open_time']).seconds
            
            self.audit.log_trade(
                symbol=symbol,
                side=position['type'],
                entry_price=position['price_open'],
                exit_price=close_price,
                volume=position['volume'],
                profit=profit,
                duration_seconds=duration,
                entry_order_id=str(position.get('ticket', '')),
                exit_order_id=str(result.get('mt5_order_id', '')),
                strategy_id=self.config.strategy_id
            )
            
            # Update state
            self.state.close_position(symbol, {'price': close_price, 'profit': profit})
            self.state.record_trade(symbol, profit)
            
            logger.info(f"✓ Position closed: {symbol}, P/L: ${profit:.2f}")
        else:
            logger.error(f"✗ Failed to close position: {result.get('message')}")
    
    def _sync_state(self):
        """Synchronize internal state with MT5"""
        positions = self.connector.get_positions()
        self.state.sync_with_mt5(positions)
        logger.debug(f"State synced: {len(positions)} positions")
    
    def _take_account_snapshot(self):
        """Take and log account snapshot"""
        account = self.connector.get_account_info()
        if account:
            self.audit.log_account_snapshot(
                balance=account['balance'],
                equity=account['equity'],
                profit=account['profit'],
                margin=account['margin'],
                margin_free=account['margin_free'],
                margin_level=account.get('margin_level'),
                open_positions=len(self.state.positions)
            )
            
            logger.info(f"Account: Balance=${account['balance']:.2f}, "
                       f"Equity=${account['equity']:.2f}, "
                       f"P/L=${account['profit']:.2f}")
    
    def _check_kill_switch(self) -> bool:
        """Check if kill switch file exists"""
        if not self.config.enable_kill_switch:
            return False
        
        kill_switch_path = Path(self.config.kill_switch_file)
        if kill_switch_path.exists():
            self.state.activate_kill_switch("Kill switch file detected")
            self.audit.log_event(
                event_type='KILL_SWITCH',
                severity='CRITICAL',
                message='Kill switch activated via file'
            )
            return True
        
        return False
    
    def _shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Live Trader...")
        
        self.running = False
        
        # Log shutdown
        self.audit.log_event(
            event_type='SHUTDOWN',
            severity='INFO',
            message='Live trader shutting down'
        )
        
        # Print summary
        summary = self.executor.get_execution_summary()
        state_summary = self.state.get_state_summary()
        
        logger.info("="*50)
        logger.info("SESSION SUMMARY")
        logger.info("="*50)
        logger.info(f"Orders: {summary['total_orders']} "
                   f"(Executed: {summary['executed']}, Failed: {summary['failed']})")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"Open Positions: {state_summary['open_positions']}")
        logger.info(f"Daily Trades: {state_summary['daily_trades']}")
        logger.info(f"Daily P/L: ${state_summary['daily_pnl']:.2f}")
        logger.info("="*50)
        
        # Close MT5 connection
        self.connector.shutdown()
        
        logger.info("✓ Shutdown complete")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AlgoAgent Live Trader')
    parser.add_argument('--strategy', '-s', required=True, 
                       help='Path to strategy file')
    parser.add_argument('--config', '-c', 
                       help='Path to .env configuration file')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (override config)')
    
    args = parser.parse_args()
    
    # Load config
    if args.config:
        from dotenv import load_dotenv
        load_dotenv(args.config)
    
    config = LiveConfig()
    
    # Override dry-run if specified
    if args.dry_run:
        config.dry_run = True
    
    # Setup logging
    logger = setup_logging(config)
    
    logger.info("="*50)
    logger.info("ALGOAGENT LIVE TRADER")
    logger.info("="*50)
    logger.info(f"Version: 1.0.0")
    logger.info(f"Mode: {'DRY RUN' if config.dry_run else 'LIVE'}")
    logger.info(f"Strategy: {args.strategy}")
    logger.info("="*50)
    
    # Create and start trader
    trader = LiveTrader(config, args.strategy)
    
    try:
        trader.start()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
