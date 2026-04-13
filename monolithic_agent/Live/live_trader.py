"""
Live Trader - Main trading loop and orchestration
"""
import hashlib
import math
import re
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
    
    def _build_order_comment(self, signal_id: str) -> str:
        """
        Build a unique, human-readable MT5 order comment (max 31 chars).
        Format: <StratSlug>_s<SessionNum>_<Hash5>
        e.g. TrendFol_s44_a3f2b
        """
        # Slug: first 8 alphanumeric chars of strategy name
        raw_name = getattr(self.config, 'strategy_name', '') or self.config.strategy_id
        slug = re.sub(r'[^A-Za-z0-9]', '', raw_name)[:8] or 'Bot'
        # Session number: extract digits from strategy_id (e.g. "session_44" → "44")
        session_digits = re.sub(r'[^0-9]', '', self.config.strategy_id)[-4:] or '0'
        # Short hash of signal_id for uniqueness
        sig_hash = hashlib.md5(signal_id.encode()).hexdigest()[:5]
        comment = f"{slug}_s{session_digits}_{sig_hash}"
        return comment[:31]  # MT5 hard limit

    @staticmethod
    def _pip_size(symbol: str, symbol_info: dict) -> float:
        """
        Return the pip size for a symbol using MT5 symbol_info data.

        Rules (MT5 convention):
          5-digit FX (EURUSD, GBPUSD):   digits=5, point=0.00001 → pip = 0.00010
          3-digit JPY pairs (USDJPY):     digits=3, point=0.001   → pip = 0.01000
          Silver (XAGUSD):                digits=3, point=0.001   → pip = 0.01000
          Gold / metals (XAUUSD, XPT…):  digits=2, point=0.01    → pip = 1.0
          Bitcoin (BTCUSD):               digits=2, point=0.01    → pip = 10.0
          Ethereum / other crypto:        digits=2, point=0.01    → pip = 1.0
          Indices (US30, NAS100, US500):  digits=2, point=0.01    → pip = 1.0

        Pip sizes are chosen so that sl_pips × pip_size always exceeds the
        broker's minimum stop distance (max of stops_level and spread).
        BTCUSD has a wide spread (~$25) so pip = $10 ensures a 15-pip SL
        lands at $150, safely above that spread.  XAGUSD raw point (0.001)
        gives $0.015 per pip which is below its ~$0.047 spread, so we use
        0.01 instead.

        Falls back to symbol-name inference when symbol_info lacks digits/point.
        """
        digits = symbol_info.get('digits')
        point  = symbol_info.get('point')
        sym = symbol.upper().replace(' ', '')

        if digits is not None and point is not None:
            # 5-digit standard FX: always ×10 (e.g. EURUSD 0.00001 → 0.0001)
            if digits == 5:
                return point * 10
            # 3-digit JPY pairs only: ×10 (e.g. USDJPY 0.001 → 0.01)
            if digits == 3 and sym.endswith('JPY'):
                return point * 10
            # Precious metals (XAU, XPT, XPD) with digits=2 → pip = $1 (100 pts)
            if digits == 2 and sym[:3] in ('XAU', 'XPT', 'XPD'):
                return 1.0
            # Silver (XAGUSD): digits=3, point=0.001 → pip = $0.01 (10 points)
            # Raw point (0.001) gives $0.015 for a 15-pip SL which is below typical spread.
            if sym[:3] == 'XAG':
                return 0.01
            # Bitcoin: BTC spread on FBS is ~$25; point=0.01, so pip = $10 (1000 points)
            # keeps a 15-pip SL at $150, safely above the broker spread.
            if sym[:3] == 'BTC':
                return 10.0
            # Ethereum and other major crypto: pip = $1 (100 points)
            if sym[:3] in ('ETH', 'LTC', 'XRP'):
                return 1.0
            # Major indices (US30, US500, NAS100, SPX, DAX, etc.)
            # digits=2, point=0.01 → pip = 1.0 (1 full price unit per pip)
            _idx_prefixes = ('US30', 'US50', 'US500', 'NAS', 'SPX', 'DAX',
                             'UK100', 'JP225', 'AUS200', 'HK50')
            if any(sym.startswith(t) for t in _idx_prefixes):
                return 1.0
            # Everything else (remaining FX variants, stocks): 1 pip = 1 point
            return point

        # Fallback: infer from symbol name when symbol_info is unavailable
        return LiveTrader._infer_pip_size_from_name(sym)

    @staticmethod
    def _infer_pip_size_from_name(sym: str) -> float:
        """
        Fallback pip size inferred from the symbol name alone.
        Used when MT5 symbol_info is unavailable (dry-run without MT5 connection).
        """
        if sym.endswith('JPY'):
            return 0.01                          # 3-digit JPY pairs
        if sym.startswith('XAU'):
            return 1.0                           # Gold — 1 pip = $1
        if sym.startswith('XAG'):
            return 0.01                          # Silver — 1 pip = $0.01
        if sym.startswith(('XPT', 'XPD')):
            return 0.01                          # Platinum / Palladium
        if sym.startswith('BTC'):
            return 10.0                          # Bitcoin — 1 pip = $10
        if sym.startswith(('ETH', 'LTC', 'XRP')):
            return 1.0                           # Other major crypto — 1 pip = $1
        # Major indices (large nominal prices)
        _indices = ('US30', 'US50', 'US500', 'NAS', 'SPX', 'DAX',
                    'UK100', 'JP225', 'AUS200', 'HK50')
        if any(sym.startswith(t) for t in _indices):
            return 1.0
        # US-listed stocks and ETFs (2-decimal prices)
        _stocks = ('AAPL', 'TSLA', 'AMZN', 'GOOGL', 'MSFT', 'NVDA', 'META',
                   'SPY', 'QQQ', 'NVDA')
        if sym in _stocks:
            return 0.01
        # Default: standard 5-digit FX pair
        return 0.0001

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
        
        # Check if we've already reached the max allowed positions for this symbol
        pos_count = self.state.position_count(symbol)
        max_pos = self.config.max_positions_per_symbol

        if signal_type == 'BUY' and pos_count >= max_pos:
            logger.info(
                f"Max positions ({max_pos}) reached for {symbol}, skipping BUY signal"
            )
            return
        
        if signal_type == 'SELL' and pos_count > 0:
            # This is an exit signal - close position
            self._close_position(symbol, signal, symbol_info)
            return
        
        # Calculate position size
        account = self.connector.get_account_info()
        if not account:
            logger.error("Could not get account info")
            return
        
        entry_price = symbol_info['ask'] if signal_type == 'BUY' else symbol_info['bid']

        # ── SL/TP resolution — driven by session exit_mode ─────────────────
        # fixed_pips : session sl_pips / tp_pips are authoritative; any
        #              strategy-supplied values are ignored.
        # bot        : strategy provides all SL/TP; session pips are ignored.
        # percentage : same as bot — strategy or no SL/TP; session pips ignored.
        # --------------------------------------------------------------------
        signal_sl = signal.get('sl') if hasattr(signal, 'get') else None
        signal_tp = signal.get('tp') if hasattr(signal, 'get') else None

        stop_loss_price: Optional[float] = None
        take_profit_price: Optional[float] = None

        exit_mode = getattr(self.config, 'exit_mode', 'bot')

        if exit_mode == 'fixed_pips':
            # Session pips are the authoritative source — calculate directly.
            pip_size = self._pip_size(symbol, symbol_info)
            if self.config.sl_pips is not None:
                dist = self.config.sl_pips * pip_size
                stop_loss_price = (
                    entry_price - dist if signal_type == 'BUY' else entry_price + dist
                )
                logger.info(
                    f"[fixed_pips] SL for {symbol}: "
                    f"{self.config.sl_pips} pips × {pip_size} = {dist:.5f} "
                    f"→ {stop_loss_price:.5f}"
                )
            else:
                logger.warning(
                    f"[fixed_pips] No sl_pips configured for {symbol}; "
                    f"trade will run without a stop-loss."
                )

            if self.config.tp_pips is not None:
                dist = self.config.tp_pips * pip_size
                take_profit_price = (
                    entry_price + dist if signal_type == 'BUY' else entry_price - dist
                )
                logger.info(
                    f"[fixed_pips] TP for {symbol}: "
                    f"{self.config.tp_pips} pips × {pip_size} = {dist:.5f} "
                    f"→ {take_profit_price:.5f}"
                )

        else:
            # bot / percentage — use strategy-provided SL/TP only.
            if signal_sl is not None:
                _sl_val = float(signal_sl)
                if not math.isnan(_sl_val) and _sl_val > 0:
                    stop_loss_price = _sl_val
                    logger.info(
                        f"[{exit_mode}] Using strategy-defined SL for {symbol}: "
                        f"{stop_loss_price:.5f}"
                    )
                else:
                    logger.debug(
                        f"Strategy SL for {symbol} is {_sl_val!r} (invalid) — ignoring."
                    )

            if signal_tp is not None:
                _tp_val = float(signal_tp)
                if not math.isnan(_tp_val) and _tp_val > 0:
                    take_profit_price = _tp_val
                    logger.info(
                        f"[{exit_mode}] Using strategy-defined TP for {symbol}: "
                        f"{take_profit_price:.5f}"
                    )
                else:
                    logger.debug(
                        f"Strategy TP for {symbol} is {_tp_val!r} (invalid) — ignoring."
                    )

            if stop_loss_price is None:
                logger.warning(
                    f"[{exit_mode}] No SL for {symbol} (strategy provided none). "
                    f"Trade will run without a stop-loss."
                )
            if take_profit_price is None:
                logger.debug(
                    f"[{exit_mode}] No TP for {symbol}; trade runs until exit signal."
                )

        # ── Enforce broker minimum stop distance ─────────────────────────────
        # MT5 rejects orders where the SL/TP is closer to entry than
        # max(stops_level × point, spread × point).  The spread component is
        # critical for instruments with wide spreads (e.g. BTCUSD spread ~$25):
        # a stop inside the spread is always rejected regardless of stops_level.
        stops_level = symbol_info.get('trade_stops_level') or 0
        point       = symbol_info.get('point') or 0
        spread_pts  = symbol_info.get('spread') or 0
        if point:
            min_dist = max(stops_level * point, spread_pts * point)
        else:
            min_dist = 0
        if min_dist:
            if stop_loss_price is not None:
                sl_dist = abs(entry_price - stop_loss_price)
                if sl_dist < min_dist:
                    logger.warning(
                        f"[{symbol}] SL distance {sl_dist:.5f} < broker minimum "
                        f"{min_dist:.5f} ({stops_level} pts × {point}) — expanding SL."
                    )
                    stop_loss_price = (
                        entry_price - min_dist if signal_type == 'BUY'
                        else entry_price + min_dist
                    )
            if take_profit_price is not None:
                tp_dist = abs(take_profit_price - entry_price)
                if tp_dist < min_dist:
                    logger.warning(
                        f"[{symbol}] TP distance {tp_dist:.5f} < broker minimum "
                        f"{min_dist:.5f} ({stops_level} pts × {point}) — expanding TP."
                    )
                    take_profit_price = (
                        entry_price + min_dist if signal_type == 'BUY'
                        else entry_price - min_dist
                    )

        # ── Position sizing ───────────────────────────────────────────────────
        # price_per_point = dollar value per lot per 1.0 price-unit move.
        # For a USD-quote instrument: price_per_point = trade_contract_size.
        #   EURUSD (contract=100,000): 1.0 price move × 100,000 = $100,000/lot
        #   XAUUSD (contract=100 oz):  1.0 price move × 100 oz   = $100/lot
        # This corrects the formula from the broken default (1.0) which produced
        # astronomically large lot counts that were only saved by the max_lots cap.
        # When no SL is set, position_size falls back to default risk calculation.
        # Pass entry_price as a sentinel stop_loss_price so the risk calc uses
        # the configured DEFAULT_RISK_PCT with a 1% distance assumption.
        pip_size_for_sizing = self._pip_size(symbol, symbol_info)
        contract_size = symbol_info.get('trade_contract_size') or 100_000.0
        # For pairs where profit is in a non-USD currency we'd need a conversion;
        # for all USD-quote instruments (the common case) contract_size is exact.
        price_per_point = contract_size

        effective_sl_for_sizing = stop_loss_price if stop_loss_price is not None else (
            entry_price * 0.99 if signal_type == 'BUY' else entry_price * 1.01
        )
        volume = self.bridge.position_size(
            account_balance=account['balance'],
            risk_pct=self.config.default_risk_pct,
            stop_loss_price=effective_sl_for_sizing,
            entry_price=entry_price,
            symbol=symbol,
            price_per_point=price_per_point,
        )
        
        # Limit position size
        volume = min(volume, self.config.max_position_size)
        
        # Build order request
        order_meta = {
            'symbol': symbol,
            'magic': self.config.magic_number,
            'deviation': 20,
            'comment': self._build_order_comment(signal_id),
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
            tp=take_profit_price
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
