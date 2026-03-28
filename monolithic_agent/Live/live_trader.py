"""
Live Trader - Main trading loop and orchestration
"""
import math
import signal
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import logging

from config import LiveConfig, setup_logging, MT5Constants

# On Linux the native MetaTrader5 package is unavailable; use the HTTP bridge
# connector instead.  Set MT5_USE_BRIDGE=true in the environment to activate.
import os as _os
if _os.getenv('MT5_USE_BRIDGE', 'false').lower() == 'true':
    from mt5_bridge_connector import MT5BridgeConnector as MT5Connector, MT5ConnectionError
else:
    from mt5_connector import MT5Connector, MT5ConnectionError
from order_executor import OrderExecutor
from state_manager import StateManager
from audit_logger import AuditLogger
from backtesting_bridge import BacktestingBridge, get_strategy_from_file
from live_data_fetcher import LiveDataFetcher

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
        self.data_fetcher = LiveDataFetcher()
        
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
        
        # Resolve the correct tvDatafeed exchange for this symbol.
        # FX pairs use 'FX', gold uses 'OANDA', crypto uses 'COINBASE'.
        exchange = self._resolve_exchange(symbol)
        
        # Refresh warehouse data before generating signals
        fetch_result = self.data_fetcher.refresh(
            symbol=symbol,
            exchange=exchange,
            interval=self.config.timeframe,
            n_bars=self.config.data_bars,
        )
        if fetch_result['status'] not in ('ok',):
            logger.warning(
                f"Data refresh for {symbol} returned status={fetch_result['status']}: "
                f"{fetch_result['message']} — proceeding with existing warehouse data"
            )
        else:
            logger.info(
                f"Data refresh {symbol}: +{fetch_result['new_rows']} new bars, "
                f"latest={fetch_result['latest_bar']}"
            )
        
        # Get symbol info
        symbol_info = self.connector.get_symbol_info(symbol)
        if not symbol_info:
            logger.warning(f"Could not get symbol info for {symbol}")
            return

        # Skip when the market is closed (bid/ask == 0.0) to avoid stale-signal
        # retry storms and "Invalid price: 0.0" precheck failures.
        bid = symbol_info.get('bid', 0)
        ask = symbol_info.get('ask', 0)
        if bid == 0 and ask == 0:
            logger.info(f"{symbol} market appears closed (bid/ask = 0.0) — skipping iteration")
            return

        # Generate signals — use a 7-day lookback so the window always
        # contains recent bars regardless of weekends or data gaps.
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=7)
        
        try:
            signals = self.bridge.generate_signals(
                symbol=symbol,
                from_ts=start_time,
                to_ts=end_time,
                timeframe=self.config.timeframe,
                n_bars=self.config.data_bars,
            )
            
            if signals.empty:
                logger.info(f"No signals generated for {symbol}")
                return
            
            # Prefer the most recent actionable (BUY/SELL) signal in the window.
            # The bridge returns one row per bar; on most bars the signal is HOLD
            # because EMA crossovers (and similar events) are rare.  Blindly taking
            # iloc[-1] would always yield HOLD even when a crossover occurred earlier
            # in the same 7-day window.  We pick the latest non-HOLD signal so that
            # a real entry/exit is not missed, while still using the deduplication ID
            # to avoid re-executing the same signal on every subsequent iteration.
            actionable = signals[signals['signal'].isin(['BUY', 'SELL'])]
            if not actionable.empty:
                latest_signal = actionable.iloc[-1]
                logger.info(
                    f"Actionable signal found for {symbol}: "
                    f"{latest_signal['signal']} @ {latest_signal.name}"
                )
            else:
                latest_signal = signals.iloc[-1]
            signal_timestamp = latest_signal.name.strftime('%Y%m%d%H%M%S')
            signal_id = f"{self.config.strategy_id}_{symbol}_{signal_timestamp}"
            
            # Check if signal already processed.
            # For HOLD signals, in-memory dedup is sufficient (they never execute).
            # For BUY/SELL signals, bypass in-memory check and go straight to the DB
            # so that failed orders (e.g. bridge was down) can be retried.
            signal_type_value = latest_signal['signal']
            if signal_type_value not in ['BUY', 'SELL']:
                if self.state.is_signal_processed(signal_id):
                    logger.debug(f"Signal already processed: {signal_id}")
                    return
            
            # Log signal
            signal_logged = self.audit.log_signal(
                signal_id=signal_id,
                symbol=symbol,
                signal_type=latest_signal['signal'],
                confidence=latest_signal['confidence'],
                price=latest_signal['price'],
                strategy_id=latest_signal['strategy_id']
            )

            if not signal_logged:
                # Signal already in audit DB — only skip if a successful order exists.
                # If the previous order failed (e.g. bridge was down), allow retry.
                last_order = self.audit.get_last_order_for_signal(signal_id)
                if last_order is None or last_order.get('status') != 'FAILED':
                    self.state.mark_signal_processed(signal_id)
                    self.state.update_last_signal_time(symbol)
                    logger.info(f"Signal already persisted, skipping reprocessing: {signal_id}")
                    return
                else:
                    logger.info(f"Signal {signal_id} previously failed ({last_order.get('error_message')}), retrying")
            
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
    
    @staticmethod
    def _pip_size(symbol_info: dict) -> float:
        """
        Return the pip size for a symbol using MT5 tick_size data.

        Uses broker-supplied ``trade_tick_size`` (the minimum price movement
        for the instrument) rather than a ``digits``-based heuristic, which
        breaks for non-standard instruments.

        Mapping:
          - tick_size ≤ 0.001 (5-digit FX, 3-digit JPY):  pip = tick_size × 10
          - tick_size > 0.001 (metals, indices, crypto …): pip = tick_size

        Fallback: if tick_size is unavailable, falls back to the digits heuristic
        so existing behaviour is preserved for older broker data.

        Example outputs:
          EURUSD (tick_size=0.00001) → pip = 0.00010
          USDJPY (tick_size=0.001)   → pip = 0.010
          XAUUSD (tick_size=0.01)    → pip = 0.01
          US30   (tick_size=1.0)     → pip = 1.0
        """
        tick_size = symbol_info.get('trade_tick_size')
        if tick_size:
            return tick_size * 10 if tick_size <= 0.001 else tick_size

        # Fallback: digits heuristic (for brokers that omit tick_size)
        digits = symbol_info.get('digits', 5)
        point  = symbol_info.get('point', 0.00001)
        if digits in (5, 3):
            return point * 10
        elif digits == 2:
            return point * 100
        else:
            return point

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
        
        entry_price = symbol_info['ask'] if signal_type == 'BUY' else symbol_info['bid']

        # ── SL/TP resolution (priority order) ─────────────────────────────
        # 1. Strategy-computed value (from backtesting_bridge: self.stop_loss attr
        #    or stop_loss_pct × entry_price)
        # 2. Session-configured fixed pips (sl_pips / tp_pips set when the
        #    session was started — independent of any bot script)
        # 3. No SL/TP (trade runs until the strategy emits an exit signal)
        # The old 2% percentage fallback has been removed; it produced arbitrary
        # SL values that had nothing to do with the strategy's risk model.
        # ------------------------------------------------------------------
        signal_sl = signal.get('sl') if hasattr(signal, 'get') else None
        signal_tp = signal.get('tp') if hasattr(signal, 'get') else None

        # Priority 1: strategy-supplied SL/TP
        stop_loss_price: Optional[float] = None
        take_profit_price: Optional[float] = None

        if signal_sl is not None:
            _sl_val = float(signal_sl)
            if not math.isnan(_sl_val) and _sl_val > 0:
                stop_loss_price = _sl_val
                logger.info(f"Using strategy-defined SL for {symbol}: {stop_loss_price:.5f}")
            else:
                logger.debug(f"Strategy SL for {symbol} is {_sl_val!r} (invalid) — ignoring.")

        if signal_tp is not None:
            _tp_val = float(signal_tp)
            if not math.isnan(_tp_val) and _tp_val > 0:
                take_profit_price = _tp_val
                logger.info(f"Using strategy-defined TP for {symbol}: {take_profit_price:.5f}")
            else:
                logger.debug(f"Strategy TP for {symbol} is {_tp_val!r} (invalid) — ignoring.")

        # Priority 2: session pip-based fallback (fixed_pips mode only)
        if self.config.exit_mode == 'fixed_pips' and (stop_loss_price is None or take_profit_price is None):
            pip_size = self._pip_size(symbol_info)

            if stop_loss_price is None and self.config.sl_pips is not None:
                dist = self.config.sl_pips * pip_size
                stop_loss_price = (
                    entry_price - dist if signal_type == 'BUY' else entry_price + dist
                )
                logger.info(
                    f"Using session SL pips for {symbol}: "
                    f"{self.config.sl_pips} pips → {stop_loss_price:.5f}"
                )

            if take_profit_price is None and self.config.tp_pips is not None:
                dist = self.config.tp_pips * pip_size
                take_profit_price = (
                    entry_price + dist if signal_type == 'BUY' else entry_price - dist
                )
                logger.info(
                    f"Using session TP pips for {symbol}: "
                    f"{self.config.tp_pips} pips → {take_profit_price:.5f}"
                )

        # Priority 3: no SL/TP
        if stop_loss_price is None:
            logger.warning(
                f"No SL configured for {symbol} (strategy provided none, no sl_pips set). "
                f"Trade will run without a stop-loss."
            )
        if take_profit_price is None:
            logger.debug(
                f"No TP configured for {symbol}; trade will run until exit signal."
            )

        # Enforce broker minimum stop distance (trade_stops_level × point).
        # Some brokers (e.g. Exness on metals) require SL/TP to be at least
        # N points away from the current price, otherwise the order is rejected.
        stops_level = symbol_info.get('trade_stops_level', 0) or 0
        point = symbol_info.get('point', 0.00001)
        if stops_level > 0 and stop_loss_price is not None:
            min_stop_dist = stops_level * point * 1.2   # 20 % buffer above the hard minimum
            actual_dist = abs(entry_price - stop_loss_price)
            if actual_dist < min_stop_dist:
                logger.warning(
                    f"{symbol} SL distance {actual_dist:.5f} < broker minimum {min_stop_dist:.5f} "
                    f"(stops_level={stops_level}). Widening SL to broker minimum."
                )
                stop_loss_price = (
                    entry_price - min_stop_dist if signal_type == 'BUY'
                    else entry_price + min_stop_dist
                )


        # Pass entry_price as a sentinel stop_loss_price so the risk calc uses
        # the configured DEFAULT_RISK_PCT with a 1% distance assumption.
        effective_sl_for_sizing = stop_loss_price if stop_loss_price is not None else (
            entry_price * 0.99 if signal_type == 'BUY' else entry_price * 1.01
        )
        # Compute the correct price-per-point for position sizing.
        # Prefer broker-side order_calc_profit (Phase 2); fall back to
        # tick_value / tick_size ratio when the endpoint is unavailable.
        pip_size_for_sizing = self._pip_size(symbol_info)
        action_code = 0 if signal_type == 'BUY' else 1
        broker_pip_value = self.connector.get_pip_value(
            symbol, pip_size_for_sizing, entry_price, action=action_code
        )
        if broker_pip_value is not None and pip_size_for_sizing:
            # broker_pip_value = monetary value of 1 pip on 1 lot
            # price_per_point  = pip_value / pip_size  (value per 1 price unit)
            price_per_point = broker_pip_value / pip_size_for_sizing
        else:
            tick_value = symbol_info.get('trade_tick_value', 1.0)
            tick_size  = symbol_info.get('trade_tick_size', 1.0)
            price_per_point = (tick_value / tick_size) if tick_size else 1.0

        volume = self.bridge.position_size(
            account_balance=account['balance'],
            risk_pct=self.config.default_risk_pct,
            stop_loss_price=effective_sl_for_sizing,
            entry_price=entry_price,
            symbol=symbol,
            price_per_point=price_per_point
        )

        # Limit position size: global config cap, then broker's volume_max for this symbol
        volume = min(volume, self.config.max_position_size)
        volume = min(volume, symbol_info.get('volume_max', volume))
        
        # Build order request
        order_meta = {
            'symbol': symbol,
            'magic': self.config.magic_number,
            'deviation': 20,
            'comment': signal_id[-29:],
            'exit_mode': self.config.exit_mode,
        }
        if stop_loss_price is not None:
            order_meta['sl'] = stop_loss_price
        if take_profit_price is not None:
            order_meta['tp'] = take_profit_price

        order_request = self.bridge.build_order_request(
            signal_row=signal,
            volume=volume,
            meta=order_meta,
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
            sl=stop_loss_price,
            tp=take_profit_price,
            metadata={
                'exit_mode': self.config.exit_mode,
            }
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
                'tp': take_profit_price,
                'open_time': datetime.now()
            })
            logger.info(
                f"✓ Position opened: {symbol} {signal_type} {volume} @ {entry_price:.5f} "
                f"SL={stop_loss_price:.5f} "
                f"TP={f'{take_profit_price:.5f}' if take_profit_price is not None else 'none'}"
            )
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
            open_time = position['open_time']
            if isinstance(open_time, (int, float)):
                open_time = datetime.fromtimestamp(open_time)
            duration = (datetime.now() - open_time).seconds
            
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
                strategy_id=self.config.strategy_id,
                metadata={
                    'exit_mode': self.config.exit_mode,
                    'exit_reason': 'strategy_signal',
                }
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
    
    def _resolve_exchange(self, symbol: str) -> str:
        """
        Return the correct tvDatafeed exchange string for a given symbol.
        Falls back to self.config.exchange (default 'FX') if not recognised.
        """
        symbol_upper = symbol.upper()
        # Explicit overrides for non-FX symbols
        EXCHANGE_MAP = {
            'XAUUSD': 'OANDA',
            'XAGUSD': 'OANDA',
            'BTCUSD': 'COINBASE',
            'ETHUSD': 'COINBASE',
            'BTCUSDT': 'BINANCE',
            'ETHUSDT': 'BINANCE',
        }
        return EXCHANGE_MAP.get(symbol_upper, self.config.exchange)

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
        load_dotenv(args.config, override=True)
    
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
