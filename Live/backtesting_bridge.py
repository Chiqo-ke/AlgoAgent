"""
Backtesting Bridge - Stable API for Live Trading
Reuses Backtesting module's functions for signal generation, sizing, and order building
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
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
        
        # Load market data with indicators
        try:
            df, metadata = load_market_data(
                ticker=symbol,
                indicators=indicators,
                period='1mo',  # Load enough history
                interval=timeframe
            )
        except Exception as e:
            logger.error(f"Failed to load market data: {e}")
            return pd.DataFrame()
        
        # Filter to requested time range
        df = df[(df.index >= from_ts) & (df.index <= to_ts)]
        
        if df.empty:
            logger.warning(f"No data available for {symbol} in range {from_ts} to {to_ts}")
            return pd.DataFrame()
        
        # Initialize mock broker for signal generation
        config = BacktestConfig(start_cash=100000)
        self.mock_broker = SimBroker(config)
        
        # Initialize strategy
        self.strategy_instance = self.strategy_class(self.mock_broker, **self.strategy_params)
        
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
            old_signal_count = len(self.mock_broker.orders)
            
            self.strategy_instance.on_bar(timestamp, market_data)
            self.mock_broker.step_to(timestamp, market_data)
            
            # Check if new signal was generated
            new_signal_count = len(self.mock_broker.orders)
            
            if new_signal_count > old_signal_count:
                # New signal was generated
                latest_order = list(self.mock_broker.orders.values())[-1]
                
                signal_type = 'BUY' if latest_order['side'] == 'BUY' else 'SELL'
                
                signals_list.append({
                    'timestamp': timestamp,
                    'signal': signal_type,
                    'confidence': 1.0,  # Could be enhanced with strategy confidence
                    'price': latest_order.get('price', row['Close']),
                    'strategy_id': self.strategy_class.__name__,
                    'action': latest_order['action'],
                    'size': latest_order['size']
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
                    'size': 0
                })
        
        signals_df = pd.DataFrame(signals_list)
        signals_df.set_index('timestamp', inplace=True)
        
        logger.info(f"Generated {len(signals_df)} signals, "
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
        if account_info:
            balance = account_info.get('balance', 0)
            margin = account_info.get('margin', 0)
            free_margin = account_info.get('margin_free', balance)
            
            # Estimate required margin (simplified - actual calc is symbol-specific)
            # This is a rough estimate; MT5's order_check provides accurate value
            estimated_margin = volume * 1000 * price * 0.01  # Assume 1% margin
            
            if estimated_margin > free_margin:
                result['pass'] = False
                result['reason'] = (f"Insufficient margin. Required: ~${estimated_margin:.2f}, "
                                  f"Available: ${free_margin:.2f}")
                return result
            
            if estimated_margin > free_margin * 0.5:
                result['warnings'].append(
                    f"High margin usage: {(estimated_margin/free_margin)*100:.1f}% of free margin"
                )
        
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
