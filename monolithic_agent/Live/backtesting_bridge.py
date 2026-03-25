"""
Backtesting Bridge - Stable API for Live Trading
Reuses Backtesting module's functions for signal generation, sizing, and order building
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import pandas as pd
import logging

# Add parent directory to path to access Backtest module
PARENT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_PATH))

try:
    from Backtest.data_loader import load_market_data, get_available_indicators
    from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
    from Backtest.config import BacktestConfig
    from Backtest.sim_broker import SimBroker
except ImportError as e:
    raise ImportError(
        f"Failed to import Backtesting modules. Ensure Backtest module is at {PARENT_PATH / 'Backtest'}. "
        f"Error: {e}"
    )

logger = logging.getLogger('LiveTrader.BacktestBridge')


class BacktestingBridge:
    """
    Bridge to Backtesting module - provides stable APIs for Live trading
    """
    
    def __init__(self, strategy_class, strategy_params: Optional[Dict[str, Any]] = None):
        """
        Initialize bridge with a strategy class from Backtesting
        
        Args:
            strategy_class: Strategy class (e.g., from my_strategy.py)
            strategy_params: Optional parameters for strategy initialization
        """
        self.strategy_class = strategy_class
        self.strategy_params = strategy_params or {}
        self.strategy_instance = None
        self.mock_broker = None
        
        logger.info(f"Initialized BacktestingBridge with strategy: {strategy_class.__name__}")
    
    def generate_signals(
        self, 
        symbol: str, 
        from_ts: datetime, 
        to_ts: datetime, 
        timeframe: str = '1d',
        indicators: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Generate trading signals using the backtesting strategy
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD', 'AAPL')
            from_ts: Start timestamp
            to_ts: End timestamp
            timeframe: Timeframe/interval (e.g., '1d', '1h', '5m')
            indicators: Optional dict of indicators to load
        
        Returns:
            DataFrame with columns: timestamp, signal, confidence, price, strategy_id
            where signal is 'BUY', 'SELL', or 'HOLD'
        """
        logger.info(f"Generating signals for {symbol} from {from_ts} to {to_ts} ({timeframe})")
        
        # Resolve indicators to pass to load_market_data.
        # Priority:
        #   1. Explicitly passed `indicators` arg (caller knows best)
        #   2. INDICATORS class attribute on the strategy (strategy declares its needs)
        #   3. Auto-derive EMA columns by instantiating the strategy briefly and
        #      reading fast_period/slow_period instance attributes.
        if indicators is None:
            indicators = getattr(self.strategy_class, 'INDICATORS', None)
        if indicators is None:
            try:
                config_probe = BacktestConfig(start_cash=100000)
                broker_probe = SimBroker(config_probe)
                probe = self.strategy_class(broker_probe, symbol=symbol, **self.strategy_params)
                indicators = {}
                # EMA: detect fast_period / slow_period
                fp = getattr(probe, 'fast_period', None)
                sp = getattr(probe, 'slow_period', None)
                if fp is not None and sp is not None:
                    indicators['EMA'] = {'periods': [fp, sp]}
                    logger.info(f"Auto-detected EMA indicators from strategy: periods={[fp, sp]}")
                # ATR: detect atr_period or fallback to 14 when atr_multiplier present
                atr_p = getattr(probe, 'atr_period', None)
                if atr_p is None and getattr(probe, 'atr_multiplier', None) is not None:
                    atr_p = 14  # standard default
                if atr_p is not None:
                    indicators['ATR'] = {'periods': [atr_p]}
                    logger.info(f"Auto-detected ATR indicator from strategy: period={atr_p}")
                # RSI: detect rsi_period
                rsi_p = getattr(probe, 'rsi_period', None)
                if rsi_p is not None:
                    indicators['RSI'] = {'periods': [rsi_p]}
                    logger.info(f"Auto-detected RSI indicator from strategy: period={rsi_p}")
                if not indicators:
                    indicators = None  # nothing detected, pass None to avoid empty-dict issues
            except Exception as probe_exc:
                logger.debug(f"Strategy probe for indicators failed (non-fatal): {probe_exc}")

        # Load market data with indicators — use 'max' period so strategy indicators
        # (SMA, EMA, RSI, etc.) have enough historical bars to warm up properly.
        try:
            df, metadata = load_market_data(
                ticker=symbol,
                indicators=indicators,
                period='max',
                interval=timeframe
            )
        except Exception as e:
            logger.error(f"Failed to load market data: {e}")
            return pd.DataFrame()
        
        if df.empty:
            logger.warning(f"No warehouse data found for {symbol} ({timeframe})")
            return pd.DataFrame()
        
        # Normalise timezone: ensure from_ts / to_ts are UTC-aware when the
        # DataFrame index is tz-aware (it always is after _load_warehouse_csv).
        if df.index.tz is not None:
            if from_ts.tzinfo is None:
                from_ts = from_ts.replace(tzinfo=timezone.utc)
            if to_ts.tzinfo is None:
                to_ts = to_ts.replace(tzinfo=timezone.utc)
        
        # Run the strategy over ALL loaded bars so indicators warm up correctly,
        # then filter the returned *signals* to those on or after from_ts.
        # We keep a hard cap of 500 bars to avoid unbounded memory use.
        df = df.tail(500)
        logger.info(f"Running strategy over {len(df)} bars for {symbol} "
                    f"(signals window: {from_ts} → {to_ts})")
        
        # Initialize mock broker for signal generation
        config = BacktestConfig(start_cash=100000)
        self.mock_broker = SimBroker(config)
        
        # Initialize strategy — pass symbol so on_bar looks up the right key in market_data
        self.strategy_instance = self.strategy_class(self.mock_broker, symbol=symbol, **self.strategy_params)
        
        # Collect signals
        signals_list = []
        
        for timestamp, row in df.iterrows():
            # Prepare market data dict
            market_data = {
                symbol: {
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row.get('Volume', 0)
                }
            }
            
            # Add indicator values to market data
            for col in df.columns:
                if col not in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    market_data[symbol][col.lower()] = row[col]
            
            # Call strategy's on_bar method
            # (Strategy will call broker.submit_signal internally)
            old_order_count = self.mock_broker.order_manager.orders_created
            
            self.strategy_instance.on_bar(timestamp, market_data)
            self.mock_broker.step_to(timestamp, market_data)
            
            # Check if new order was created this bar
            new_order_count = self.mock_broker.order_manager.orders_created
            
            if new_order_count > old_order_count:
                # New order was placed — find the most recent one
                all_orders = list(self.mock_broker.order_manager.orders.values())
                latest_order = all_orders[-1]  # Order dataclass instance
                
                # side is "BUY" or "SELL" string (OrderSide constant)
                signal_type = 'BUY' if latest_order.side == 'BUY' else 'SELL'

                # ── Extract SL/TP from the strategy instance ──────────────────
                # Bot scripts compute SL/TP as instance attributes INSIDE on_bar()
                # but do NOT pass them to create_signal().  We read them directly
                # from the strategy object right after on_bar() has run.
                #
                # Convention 1 — absolute price already computed by strategy:
                #   self.stop_loss   (e.g. ATR/breakout strategies)
                #   self.take_profit (rarely set, same pattern)
                #
                # Convention 2 — percentage stored as parameter:
                #   self.stop_loss_pct  (e.g. 0.02 = 2%)
                #   self.take_profit_pct (e.g. 0.05 = 5%)
                #   combined with self.entry_price set just after the signal
                #
                # In all cases we prefer a value the strategy computed over the
                # fallback in live_trader._execute_signal().
                # -----------------------------------------------------------------
                strategy_sl: Optional[float] = None
                strategy_tp: Optional[float] = None

                # Convention 1: absolute price attribute
                raw_sl = getattr(self.strategy_instance, 'stop_loss', None)
                if raw_sl is not None and isinstance(raw_sl, (int, float)) and raw_sl > 0:
                    strategy_sl = float(raw_sl)

                raw_tp = getattr(self.strategy_instance, 'take_profit', None)
                if raw_tp is not None and isinstance(raw_tp, (int, float)) and raw_tp > 0:
                    strategy_tp = float(raw_tp)

                # Convention 2: percentage-based (only applies to ENTRY signals)
                if latest_order.meta.get('action') != 'EXIT':
                    entry_px = getattr(self.strategy_instance, 'entry_price', None)
                    sl_pct = getattr(self.strategy_instance, 'stop_loss_pct', None)
                    tp_pct = getattr(self.strategy_instance, 'take_profit_pct', None)

                    if sl_pct is not None and entry_px is not None and strategy_sl is None:
                        sl_pct = float(sl_pct)
                        entry_px_f = float(entry_px)
                        strategy_sl = (
                            entry_px_f * (1.0 - sl_pct)
                            if signal_type == 'BUY'
                            else entry_px_f * (1.0 + sl_pct)
                        )

                    if tp_pct is not None and entry_px is not None and strategy_tp is None:
                        tp_pct = float(tp_pct)
                        entry_px_f = float(entry_px)
                        strategy_tp = (
                            entry_px_f * (1.0 + tp_pct)
                            if signal_type == 'BUY'
                            else entry_px_f * (1.0 - tp_pct)
                        )

                # Merge: strategy-extracted values take priority over anything in
                # the order meta (order meta is typically empty for current bots).
                final_sl = strategy_sl or latest_order.meta.get('sl')
                final_tp = strategy_tp or latest_order.meta.get('tp')

                if final_sl:
                    logger.debug(
                        f"Signal SL extracted for {latest_order.symbol}: {final_sl:.5f} "
                        f"(source: {'strategy attr' if strategy_sl else 'order meta'})"
                    )
                if final_tp:
                    logger.debug(
                        f"Signal TP extracted for {latest_order.symbol}: {final_tp:.5f} "
                        f"(source: {'strategy attr' if strategy_tp else 'order meta'})"
                    )

                signals_list.append({
                    'timestamp': timestamp,
                    'signal': signal_type,
                    'confidence': 1.0,
                    'price': latest_order.price or row['Close'],
                    'strategy_id': self.strategy_class.__name__,
                    'action': latest_order.meta.get('action'),
                    'size': latest_order.size_requested,
                    'sl': final_sl,
                    'tp': final_tp,
                })
            else:
                # No signal - HOLD
                signals_list.append({
                    'timestamp': timestamp,
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'price': row['Close'],
                    'strategy_id': self.strategy_class.__name__,
                    'action': None,
                    'size': 0,
                    'sl': None,
                    'tp': None,
                })
        
        signals_df = pd.DataFrame(signals_list)
        signals_df.set_index('timestamp', inplace=True)
        
        # Filter to the caller's requested window so only recent signals are returned.
        signals_df = signals_df[
            (signals_df.index >= from_ts) & (signals_df.index <= to_ts)
        ]
        
        if signals_df.empty:
            logger.warning(
                f"No signals in requested window [{from_ts} → {to_ts}] for {symbol}. "
                f"Latest warehouse bar may be older than from_ts."
            )
            # Fall back: return the single most-recent signal regardless of window
            # so the live trader always gets something to act on.
            full_df = pd.DataFrame(signals_list)
            full_df.set_index('timestamp', inplace=True)
            if not full_df.empty:
                signals_df = full_df.iloc[[-1]]
                logger.info(
                    f"Falling back to latest bar signal: "
                    f"{signals_df.index[-1]} → {signals_df.iloc[-1]['signal']}"
                )
        
        logger.info(f"Returning {len(signals_df)} signals, "
                   f"{len(signals_df[signals_df['signal'] != 'HOLD'])} actionable")
        
        return signals_df
    
    def position_size(
        self, 
        account_balance: float, 
        risk_pct: float, 
        stop_loss_price: float, 
        entry_price: float,
        symbol: str,
        price_per_point: float = 1.0
    ) -> float:
        """
        Calculate position size based on risk management rules
        
        Args:
            account_balance: Current account balance
            risk_pct: Risk percentage (e.g., 1.0 for 1%)
            stop_loss_price: Stop loss price level
            entry_price: Entry price level
            symbol: Trading symbol
            price_per_point: Contract/pip value (e.g., 10 for mini lots)
        
        Returns:
            Position size in lots/volume
        """
        if stop_loss_price == entry_price:
            logger.warning("Stop loss equals entry price, using minimum position size")
            return 0.01  # Minimum lot size
        
        # Calculate risk amount in account currency
        risk_amount = account_balance * (risk_pct / 100.0)
        
        # Calculate distance to stop loss (in price points)
        stop_distance = abs(entry_price - stop_loss_price)
        
        # Calculate position size
        # risk_amount = position_size * stop_distance * price_per_point
        position_size = risk_amount / (stop_distance * price_per_point)
        
        # Round to 2 decimal places (standard lot size precision)
        position_size = round(position_size, 2)
        
        # Ensure minimum lot size
        position_size = max(position_size, 0.01)
        
        logger.info(f"Calculated position size: {position_size} lots "
                   f"(Risk: ${risk_amount:.2f}, Stop distance: {stop_distance:.5f})")
        
        return position_size
    
    def build_order_request(
        self, 
        signal_row: pd.Series, 
        volume: float, 
        meta: Dict[str, Any],
        symbol_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build MT5 order request structure from signal
        
        Args:
            signal_row: Row from signals DataFrame
            volume: Position size (lots)
            meta: Additional metadata (magic, deviation, sl, tp, etc.)
            symbol_info: Optional symbol information from MT5
        
        Returns:
            Dictionary ready for mt5.order_send()
        """
        from config import MT5Constants
        
        signal_type = signal_row['signal']
        price = signal_row['price']
        
        # Determine order type and action
        if signal_type == 'BUY':
            order_type = MT5Constants.ORDER_TYPE_BUY
            trade_action = MT5Constants.TRADE_ACTION_DEAL
            # For market orders, use ask price if available
            if symbol_info and 'ask' in symbol_info:
                price = symbol_info['ask']
        elif signal_type == 'SELL':
            order_type = MT5Constants.ORDER_TYPE_SELL
            trade_action = MT5Constants.TRADE_ACTION_DEAL
            # For market orders, use bid price if available
            if symbol_info and 'bid' in symbol_info:
                price = symbol_info['bid']
        else:
            raise ValueError(f"Invalid signal type: {signal_type}")
        
        # Build request structure
        request = {
            'action': trade_action,
            'symbol': meta.get('symbol', 'UNKNOWN'),
            'volume': volume,
            'type': order_type,
            'price': price,
            'deviation': meta.get('deviation', 20),  # Max price deviation in points
            'magic': meta.get('magic', 0),
            'comment': meta.get('comment', f"LiveTrader_{signal_row.get('strategy_id', 'unknown')}"),
            'type_time': MT5Constants.ORDER_TIME_GTC,
            'type_filling': meta.get('type_filling', MT5Constants.ORDER_FILLING_IOC),
        }
        
        # Add stop loss and take profit if provided
        if 'sl' in meta and meta['sl'] is not None:
            request['sl'] = meta['sl']
        
        if 'tp' in meta and meta['tp'] is not None:
            request['tp'] = meta['tp']
        
        logger.info(f"Built order request: {signal_type} {volume} lots of {request['symbol']} "
                   f"@ {price:.5f}")
        
        return request
    
    def simulate_precheck(
        self, 
        order_request: Dict[str, Any],
        account_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run pre-trade checks similar to backtesting validation
        
        Args:
            order_request: Order request dictionary
            account_info: Optional account information from MT5
        
        Returns:
            Dict with 'pass' (bool), 'reason' (str), and 'warnings' (list)
        """
        result = {
            'pass': True,
            'reason': '',
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['action', 'symbol', 'volume', 'type', 'price']
        for field in required_fields:
            if field not in order_request:
                result['pass'] = False
                result['reason'] = f"Missing required field: {field}"
                return result
        
        # Check volume
        volume = order_request['volume']
        if volume <= 0:
            result['pass'] = False
            result['reason'] = f"Invalid volume: {volume}"
            return result
        
        if volume < 0.01:
            result['warnings'].append(f"Volume {volume} is below minimum (0.01)")
        
        # Check price
        price = order_request['price']
        if price <= 0:
            result['pass'] = False
            result['reason'] = f"Invalid price: {price}"
            return result
        
        # Check margin requirement (if account info available)
        # NOTE: We skip the margin estimate here because our simplified formula
        # (volume * 1000 * price * 0.01) assumes forex lot sizing which is incorrect
        # for crypto and other instruments. MT5's order_check (called in execute_order)
        # performs the authoritative margin check with the correct contract size.
        if account_info:
            balance = account_info.get('balance', 0)
            free_margin = account_info.get('margin_free', balance)

            # Only hard-block if free margin is essentially zero (avoid div-by-zero)
            if free_margin <= 0:
                result['pass'] = False
                result['reason'] = f"No free margin available: ${free_margin:.2f}"
                return result
        
        # Check stop loss and take profit validity
        if 'sl' in order_request and order_request['sl'] > 0:
            sl = order_request['sl']
            price = order_request['price']
            order_type = order_request['type']
            
            from config import MT5Constants
            
            if order_type == MT5Constants.ORDER_TYPE_BUY and sl >= price:
                result['pass'] = False
                result['reason'] = f"Invalid SL for BUY order: SL {sl} >= Price {price}"
                return result
            
            if order_type == MT5Constants.ORDER_TYPE_SELL and sl <= price:
                result['pass'] = False
                result['reason'] = f"Invalid SL for SELL order: SL {sl} <= Price {price}"
                return result
        
        logger.info(f"Precheck passed with {len(result['warnings'])} warnings")
        
        return result


def get_strategy_from_file(strategy_file_path: str):
    """
    Dynamically load a strategy class from a Python file
    
    Args:
        strategy_file_path: Path to strategy .py file
    
    Returns:
        Strategy class
    """
    import importlib.util
    
    spec = importlib.util.spec_from_file_location("dynamic_strategy", strategy_file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find strategy class (assumes class name ends with 'Strategy' or is only class)
    strategy_classes = [
        obj for name, obj in module.__dict__.items()
        if isinstance(obj, type) and 'Strategy' in name
    ]
    
    if not strategy_classes:
        raise ValueError(f"No strategy class found in {strategy_file_path}")
    
    if len(strategy_classes) > 1:
        logger.warning(f"Multiple strategy classes found, using first: {strategy_classes[0].__name__}")
    
    return strategy_classes[0]


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example: Load a strategy and generate signals
    try:
        # Load example strategy from Backtesting module
        backtest_path = PARENT_PATH / 'Backtest'
        strategy_path = backtest_path / 'rsi_strategy.py'
        
        if strategy_path.exists():
            StrategyClass = get_strategy_from_file(str(strategy_path))
            
            bridge = BacktestingBridge(StrategyClass)
            
            # Generate signals for recent data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)
            
            signals = bridge.generate_signals(
                symbol='AAPL',
                from_ts=start_time,
                to_ts=end_time,
                timeframe='1d',
                indicators={'RSI': {'timeperiod': 14}}
            )
            
            print(f"\nGenerated {len(signals)} signals")
            print(signals.head(10))
            
            # Test position sizing
            position_size = bridge.position_size(
                account_balance=10000,
                risk_pct=1.0,
                stop_loss_price=148.0,
                entry_price=150.0,
                symbol='AAPL'
            )
            print(f"\nCalculated position size: {position_size} lots")
            
        else:
            print(f"Strategy file not found: {strategy_path}")
    
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
