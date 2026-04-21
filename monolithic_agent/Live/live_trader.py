"""
Live Trader - Main trading loop and orchestration
"""
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

# ---------------------------------------------------------------------------
# Timeframe helpers
# ---------------------------------------------------------------------------

# Canonical mapping from normalised interval string to minutes.
# Keep in sync with live_data_fetcher._interval_to_tvdatafeed.
_TIMEFRAME_MINUTES: dict[str, int] = {
    '1m':  1,   '3m':  3,   '5m':  5,   '15m': 15,  '30m': 30,
    '45m': 45,  '1h':  60,  '2h':  120, '3h':  180, '4h':  240,
    '1d':  1440, '1w': 10080,
    # Use 31-day upper bound for monthly so we never falsely discard a signal
    # in shorter months (28/29 days).
    '1mo': 44640,
}

_TIMEFRAME_ALIASES: dict[str, str] = {
    '60m': '1h', '1hr': '1h', '1hour': '1h',
    '120m': '2h', '2hr': '2h', '2hour': '2h',
    '240m': '4h', '4hr': '4h', '4hour': '4h',
    '1wk': '1w', '1week': '1w',
    'd': '1d', 'daily': '1d',
}


def _timeframe_to_timedelta(timeframe: str) -> timedelta:
    """Convert a timeframe string (e.g. '1h', '4h', '1d') to a timedelta."""
    norm = timeframe.strip().lower()
    norm = _TIMEFRAME_ALIASES.get(norm, norm)
    minutes = _TIMEFRAME_MINUTES.get(norm)
    if minutes is None:
        raise ValueError(
            f"Unknown timeframe '{timeframe}'. "
            f"Supported: {sorted(_TIMEFRAME_MINUTES)} (plus aliases)"
        )
    return timedelta(minutes=minutes)


def _staleness_grace(tf_td: timedelta) -> timedelta:
    """
    Return the grace period *after bar close* during which a signal is still
    considered fresh.  Longer-timeframe bars have wider windows because uptime
    exactly at bar close is harder to guarantee.

    Intraday  (≤ 1 h) : 30 min
    Short HTF (≤ 4 h) : 60 min
    Daily              : 4 h
    Weekly / Monthly   : 12 h
    """
    minutes = tf_td.total_seconds() / 60
    if minutes <= 60:
        return timedelta(minutes=30)
    elif minutes <= 240:
        return timedelta(minutes=60)
    elif minutes <= 1440:
        return timedelta(hours=4)
    else:
        return timedelta(hours=12)


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

        # Cache: configured symbol → broker symbol name (e.g. AAPL → APPLE).
        # Populated lazily in _process_symbol and used in _sync_state to remap
        # MT5 position symbols back to configured names so that has_position()
        # works correctly even after broker-name normalisation.
        self._broker_symbol_map: dict = {}  # config_name → broker_name
        
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

            # Pre-populate broker symbol map so the startup _sync_state call below
            # can correctly remap MT5 broker names (e.g. APPLE) to configured names
            # (e.g. AAPL).  Without this, has_position() would always return False
            # after a restart, causing duplicate entries and accidental short sells.
            for sym in self.config.symbols:
                try:
                    info = self.connector.get_symbol_info(sym)
                    if info:
                        broker_name = info.get('name') or sym
                        if broker_name != sym:
                            self._broker_symbol_map[sym] = broker_name
                            logger.info(f"Startup symbol map: {sym} → {broker_name}")
                except Exception as e:
                    logger.warning(f"Could not resolve broker name for {sym} at startup: {e}")

            # Sync state with MT5 (uses _broker_symbol_map populated above)
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

        # Update broker-symbol map so _sync_state can remap positions correctly.
        broker_name = symbol_info.get('name') or symbol
        if broker_name != symbol:
            self._broker_symbol_map[symbol] = broker_name
        
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

            # Discard BUY/SELL signals that are too old relative to the bar
            # close time.  Signal timestamps are bar OPEN times; the bar only
            # becomes tradeable once it closes (open + timeframe duration).
            # We therefore measure staleness from bar close, not bar open, so
            # that signals on any timeframe (1m … 1mo) are handled correctly.
            if latest_signal['signal'] in ['BUY', 'SELL']:
                now = datetime.now(timezone.utc)
                bar_open_ts = latest_signal.name.to_pydatetime().replace(tzinfo=timezone.utc)
                tf_td = _timeframe_to_timedelta(self.config.timeframe)
                bar_close_ts = bar_open_ts + tf_td

                # Guard: bar hasn't closed yet (clock skew or incomplete bar).
                if bar_close_ts > now:
                    logger.debug(
                        f"Signal @ {latest_signal.name} for {symbol}: "
                        f"bar not yet closed (closes {bar_close_ts}), skipping"
                    )
                    return

                bar_close_age = now - bar_close_ts
                grace = _staleness_grace(tf_td)
                if bar_close_age > grace:
                    logger.warning(
                        f"Discarding stale {latest_signal['signal']} signal for {symbol}: "
                        f"bar closed {bar_close_age} ago (grace: {grace}) "
                        f"— bar open @ {latest_signal.name}, bar close @ {bar_close_ts}"
                    )
                    return

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
                # If no order was placed yet, or the previous order failed, allow retry.
                last_order = self.audit.get_last_order_for_signal(signal_id)
                if last_order is not None and last_order.get('status') not in ('FAILED', None):
                    self.state.mark_signal_processed(signal_id)
                    self.state.update_last_signal_time(symbol)
                    logger.info(f"Signal already persisted and executed, skipping reprocessing: {signal_id}")
                    return
                elif last_order is None:
                    logger.info(f"Signal {signal_id} was logged but no order was placed — retrying")
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
        Return the pip size for a symbol using MT5 symbol_info data.

        Instrument conventions:
          - FX 5-digit (EURUSD, digits=5, point=0.00001) → pip = 0.00010
          - FX 3-digit JPY pairs (USDJPY, digits=3, point=0.001) → pip = 0.010
          - Stocks / equities (e.g. AAPL, digits=2, tick_size=0.01) → pip = tick_size
          - Metals / indices / crypto (e.g. XAUUSD, BTCUSD) → pip = point

        For non-FX instruments, ``trade_tick_size`` from the broker is the
        most accurate minimum price increment to use as a "pip equivalent",
        falling back to ``point`` when tick size is unavailable.
        """
        digits    = symbol_info.get('digits', 5)
        point     = symbol_info.get('point', 0.00001)
        tick_size = symbol_info.get('trade_tick_size')

        # FX majors/crosses: 5-digit pairs (EURUSD) and 3-digit JPY pairs
        if digits in (5, 3):
            return point * 10

        # Stocks, indices, metals, crypto: use broker tick_size as pip equivalent
        if tick_size and tick_size > 0:
            return float(tick_size)

        # Last resort fallback
        return point

    @staticmethod
    def _order_filling_mode(symbol_info: dict) -> int:
        """
        Return the correct ORDER_FILLING_* constant for this symbol.

        MT5 symbol_info.filling_mode is a bitmask of SUPPORTED modes:
          bit 0 (value 1) → FOK  (Fill or Kill)        → ORDER_FILLING_FOK = 0
          bit 1 (value 2) → IOC  (Immediate or Cancel) → ORDER_FILLING_IOC = 1
          bit 2 (value 4) → Return (partial fill)       → ORDER_FILLING_RETURN = 2

        Priority: Return > IOC > FOK (most permissive first).
        Fallback: FOK (hardcoded, works for most instant-execution brokers).
        """
        filling_mask = symbol_info.get('filling_mode', 0) if symbol_info else 0
        if filling_mask & 4:   # Return supported
            return MT5Constants.ORDER_FILLING_RETURN
        if filling_mask & 2:   # IOC supported
            return MT5Constants.ORDER_FILLING_IOC
        if filling_mask & 1:   # FOK supported
            return MT5Constants.ORDER_FILLING_FOK
        return MT5Constants.ORDER_FILLING_FOK  # safe fallback

    def _build_order_comment(self) -> str:
        """
        Build a concise MT5 order comment that identifies the bot by name and
        session ID so trades can be traced back to the correct bot in the
        broker's terminal.  MT5 truncates comments at 31 characters; we stay
        within that limit.

        Format: ``<SanitisedBotName>-s<SessionPK>``
        Example: ``MyEURUSD_Strategy-s42``
        """
        # Derive a clean name: use BOT_NAME when available, fall back to STRATEGY_ID.
        raw_name = self.config.bot_name or self.config.strategy_id
        # Keep only alphanumeric chars and underscores; replace spaces with _
        clean_name = re.sub(r'[^A-Za-z0-9_]', '', raw_name.replace(' ', '_'))

        # Extract the numeric session PK from STRATEGY_ID ("session_42" → "42").
        strategy_id = self.config.strategy_id
        session_num = strategy_id.split('_')[-1] if '_' in strategy_id else strategy_id
        suffix = f"-s{session_num}"  # e.g. "-s42"

        max_name_len = 31 - len(suffix)
        return f"{clean_name[:max_name_len]}{suffix}"

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

        # Use the broker's resolved symbol name for all MT5 order submissions.
        # symbol_info['name'] is already populated with the canonical broker name
        # (e.g. TSLA → TESLA, AAPL → APPLE) by get_symbol_info().
        broker_symbol = symbol_info.get('name') or symbol
        if broker_symbol != symbol:
            logger.info(f"Using broker symbol name '{broker_symbol}' for MT5 order (configured as '{symbol}')")
        
        # Check if we already have a position
        has_position = self.state.has_position(symbol)
        
        if signal_type == 'BUY' and has_position:
            logger.info(f"Already have position in {symbol}, skipping BUY signal")
            return

        if signal_type == 'SELL' and has_position:
            # This is an exit signal - close position
            self._close_position(symbol, signal, symbol_info)
            return

        # Guard: no open position and we received a SELL signal.
        # This means either:
        #   a) strategy emitted an EXIT close signal but there's nothing to close, OR
        #   b) state was lost on a process restart and there IS a position in MT5 that
        #      we don't know about — in both cases we must NOT open a new short.
        #
        # Short selling is only allowed if the session config explicitly enables it.
        # The check below intentionally ignores action='EXIT' vs None — a SELL with
        # no tracked position must never place a new market short in a long-only setup.
        if signal_type == 'SELL':
            signal_action = signal.get('action') if hasattr(signal, 'get') else None
            if not getattr(self.config, 'allow_short_selling', False):
                logger.info(
                    f"SELL signal for {symbol} with no open position skipped "
                    f"(action={signal_action!r}, allow_short_selling=False). "
                    f"Enable short selling in session config to allow short entries."
                )
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

        # Priority 2: session pip-based fallback
        if stop_loss_price is None or take_profit_price is None:
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

        # When no SL is set, position_size falls back to default risk calculation.
        # Pass entry_price as a sentinel stop_loss_price so the risk calc uses
        # the configured DEFAULT_RISK_PCT with a 1% distance assumption.
        effective_sl_for_sizing = stop_loss_price if stop_loss_price is not None else (
            entry_price * 0.99 if signal_type == 'BUY' else entry_price * 1.01
        )
        # Use fixed lot_size if configured, otherwise calculate from risk
        if self.config.lot_size > 0:
            volume = self.config.lot_size
            logger.info(f"Using fixed lot size: {volume} lots")
        else:
            volume = self.bridge.position_size(
                account_balance=account['balance'],
                risk_pct=self.config.default_risk_pct,
                stop_loss_price=effective_sl_for_sizing,
                entry_price=entry_price,
                symbol=symbol
            )
            # Limit position size
            volume = min(volume, self.config.max_position_size)
        
        # Build order request
        filling_mode = self._order_filling_mode(symbol_info)
        order_meta = {
            'symbol': broker_symbol,  # use broker's resolved name (e.g. TESLA not TSLA)
            'magic': self.config.magic_number,
            'deviation': 20,
            'comment': self._build_order_comment(),
            'type_filling': filling_mode,
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
        
        # Execute order — pass broker credentials for per-trade login
        # so that multiple sessions with different broker accounts can share
        # the same MT5 terminal (the bridge serialises via _trade_lock).
        broker_credentials = {
            'login':    self.config.mt5_login,
            'password': self.config.mt5_password,
            'server':   self.config.mt5_server,
        } if (self.config.mt5_login and self.config.mt5_password) else None

        result = self.executor.execute_order(
            order_request, client_order_id, credentials=broker_credentials
        )
        
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

        broker_symbol = symbol_info.get('name') or symbol
        logger.info(f"Closing position: {symbol}" + (f" (broker: {broker_symbol})" if broker_symbol != symbol else ""))

        # Build close order (opposite direction)
        close_type = 'SELL' if position['type'] == 'BUY' else 'BUY'
        close_price = symbol_info['bid'] if close_type == 'SELL' else symbol_info['ask']

        order_request = {
            'action': MT5Constants.TRADE_ACTION_DEAL,
            'symbol': broker_symbol,  # use broker's resolved name (e.g. TESLA not TSLA)
            'volume': position['volume'],
            'type': MT5Constants.ORDER_TYPE_SELL if close_type == 'SELL' else MT5Constants.ORDER_TYPE_BUY,
            'price': close_price,
            'deviation': 20,
            'magic': self.config.magic_number,
            'comment': f"Close_{position.get('ticket', 'unknown')}",
            'type_time': MT5Constants.ORDER_TIME_GTC,
            'type_filling': self._order_filling_mode(symbol_info),
        }

        # Specify the exact ticket so MT5 closes the right position when multiple
        # positions on the same symbol exist (e.g. from different sessions).
        if position.get('ticket'):
            order_request['position'] = position['ticket']
        
        # Execute close — use per-trade login for multi-broker support
        close_creds = {
            'login':    self.config.mt5_login,
            'password': self.config.mt5_password,
            'server':   self.config.mt5_server,
        } if (self.config.mt5_login and self.config.mt5_password) else None

        result = self.executor.execute_order(order_request, credentials=close_creds)
        
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

        # Remap broker symbol names → configured symbol names so that
        # has_position('AAPL') correctly finds a position opened as 'APPLE'.
        # The reverse map is built from _broker_symbol_map which is populated
        # lazily each time get_symbol_info() resolves a symbol in _process_symbol.
        if positions and self._broker_symbol_map:
            broker_to_config = {v: k for k, v in self._broker_symbol_map.items()}
            for pos in positions:
                broker_sym = pos.get('symbol', '')
                if broker_sym in broker_to_config:
                    pos['symbol'] = broker_to_config[broker_sym]

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
