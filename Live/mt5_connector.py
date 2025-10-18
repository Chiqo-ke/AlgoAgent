"""
MetaTrader5 Connection Manager
Handles MT5 initialization, login, reconnection, and graceful shutdown
"""
import MetaTrader5 as mt5
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import time
from pathlib import Path

from config import LiveConfig, MT5Constants

logger = logging.getLogger('LiveTrader.MT5Connector')


class MT5ConnectionError(Exception):
    """Raised when MT5 connection fails"""
    pass


class MT5Connector:
    """
    Manages MetaTrader5 connection lifecycle
    """
    
    def __init__(self, config: LiveConfig):
        """
        Initialize MT5 connector
        
        Args:
            config: Live trading configuration
        """
        self.config = config
        self.is_connected = False
        self.account_info = None
        self.terminal_info = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        logger.info("MT5Connector initialized")
    
    def initialize(self) -> bool:
        """
        Initialize MT5 connection
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Initializing MT5 connection...")
        
        try:
            # Initialize MT5 with optional terminal path
            if self.config.mt5_path:
                terminal_path = Path(self.config.mt5_path)
                if not terminal_path.exists():
                    logger.error(f"MT5 terminal not found at: {terminal_path}")
                    return False
                
                if not mt5.initialize(str(terminal_path), timeout=self.config.mt5_timeout):
                    logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                    return False
            else:
                # Auto-detect terminal
                if not mt5.initialize(timeout=self.config.mt5_timeout):
                    logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                    return False
            
            # Login to account
            if not self._login():
                mt5.shutdown()
                return False
            
            # Get terminal and account info
            self.terminal_info = mt5.terminal_info()
            self.account_info = mt5.account_info()
            
            if not self.terminal_info or not self.account_info:
                logger.error("Failed to retrieve terminal/account info")
                mt5.shutdown()
                return False
            
            self.is_connected = True
            self.reconnect_attempts = 0
            
            logger.info(f"✓ MT5 connected successfully")
            logger.info(f"  Terminal: {self.terminal_info.name} "
                       f"(Build {self.terminal_info.build})")
            logger.info(f"  Account: {self.account_info.login} - {self.account_info.server}")
            logger.info(f"  Balance: ${self.account_info.balance:.2f}")
            logger.info(f"  Equity: ${self.account_info.equity:.2f}")
            logger.info(f"  Margin Free: ${self.account_info.margin_free:.2f}")
            
            return True
        
        except Exception as e:
            logger.error(f"MT5 initialization exception: {e}", exc_info=True)
            return False
    
    def _login(self) -> bool:
        """
        Login to MT5 account
        
        Returns:
            True if successful
        """
        if self.config.dry_run:
            logger.info("DRY_RUN mode: Skipping MT5 login")
            return True
        
        if not self.config.mt5_login or not self.config.mt5_password:
            logger.error("MT5 credentials not configured")
            return False
        
        logger.info(f"Logging in to account {self.config.mt5_login}...")
        
        authorized = mt5.login(
            login=self.config.mt5_login,
            password=self.config.mt5_password,
            server=self.config.mt5_server
        )
        
        if not authorized:
            error = mt5.last_error()
            logger.error(f"MT5 login failed: {error}")
            return False
        
        logger.info("✓ MT5 login successful")
        return True
    
    def shutdown(self):
        """Gracefully shutdown MT5 connection"""
        if self.is_connected:
            logger.info("Shutting down MT5 connection...")
            mt5.shutdown()
            self.is_connected = False
            logger.info("✓ MT5 connection closed")
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to MT5
        
        Returns:
            True if reconnection successful
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            return False
        
        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 60)  # Exponential backoff, max 60s
        
        logger.warning(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} "
                      f"in {wait_time}s...")
        
        time.sleep(wait_time)
        
        # Shutdown existing connection
        try:
            mt5.shutdown()
        except:
            pass
        
        self.is_connected = False
        
        # Attempt re-initialization
        return self.initialize()
    
    def check_connection(self) -> bool:
        """
        Check if connection is still alive
        
        Returns:
            True if connected and responsive
        """
        if not self.is_connected:
            return False
        
        try:
            # Try to get account info as a health check
            account = mt5.account_info()
            if account is None:
                logger.warning("Connection check failed: account_info returned None")
                self.is_connected = False
                return False
            
            self.account_info = account
            return True
        
        except Exception as e:
            logger.error(f"Connection check exception: {e}")
            self.is_connected = False
            return False
    
    def ensure_connected(self) -> bool:
        """
        Ensure connection is active, reconnect if necessary
        
        Returns:
            True if connected (possibly after reconnect)
        """
        if self.check_connection():
            return True
        
        logger.warning("Connection lost, attempting to reconnect...")
        return self.reconnect()
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current account information
        
        Returns:
            Dict with account details or None if unavailable
        """
        if not self.ensure_connected():
            return None
        
        try:
            info = mt5.account_info()
            if info is None:
                return None
            
            return {
                'login': info.login,
                'trade_mode': info.trade_mode,
                'leverage': info.leverage,
                'balance': info.balance,
                'equity': info.equity,
                'profit': info.profit,
                'margin': info.margin,
                'margin_free': info.margin_free,
                'margin_level': info.margin_level,
                'currency': info.currency,
                'server': info.server,
                'company': info.company
            }
        
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Dict with symbol details or None
        """
        if not self.ensure_connected():
            return None
        
        try:
            # Ensure symbol is visible in MarketWatch
            if not mt5.symbol_select(symbol, True):
                logger.warning(f"Failed to select symbol: {symbol}")
                return None
            
            info = mt5.symbol_info(symbol)
            if info is None:
                logger.warning(f"Symbol info not available: {symbol}")
                return None
            
            return {
                'name': info.name,
                'bid': info.bid,
                'ask': info.ask,
                'last': info.last,
                'volume': info.volume_min,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
                'volume_step': info.volume_step,
                'trade_contract_size': info.trade_contract_size,
                'trade_tick_size': info.trade_tick_size,
                'trade_tick_value': info.trade_tick_value,
                'point': info.point,
                'digits': info.digits,
                'spread': info.spread,
                'trade_mode': info.trade_mode,
                'currency_base': info.currency_base,
                'currency_profit': info.currency_profit,
                'currency_margin': info.currency_margin
            }
        
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return None
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get open positions
        
        Args:
            symbol: Optional symbol filter
        
        Returns:
            List of position dicts
        """
        if not self.ensure_connected():
            return []
        
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            return [
                {
                    'ticket': pos.ticket,
                    'time': datetime.fromtimestamp(pos.time),
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == 0 else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'magic': pos.magic,
                    'comment': pos.comment
                }
                for pos in positions
            ]
        
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get pending orders
        
        Args:
            symbol: Optional symbol filter
        
        Returns:
            List of order dicts
        """
        if not self.ensure_connected():
            return []
        
        try:
            if symbol:
                orders = mt5.orders_get(symbol=symbol)
            else:
                orders = mt5.orders_get()
            
            if orders is None:
                return []
            
            return [
                {
                    'ticket': order.ticket,
                    'time_setup': datetime.fromtimestamp(order.time_setup),
                    'symbol': order.symbol,
                    'type': order.type,
                    'volume': order.volume_current,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'magic': order.magic,
                    'comment': order.comment
                }
                for order in orders
            ]
        
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []
    
    def check_order(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check order before sending (MT5's order_check)
        
        Args:
            request: Order request dict
        
        Returns:
            Check result dict or None if failed
        """
        if not self.ensure_connected():
            return None
        
        try:
            result = mt5.order_check(request)
            
            if result is None:
                error = mt5.last_error()
                logger.error(f"order_check failed: {error}")
                return None
            
            return {
                'retcode': result.retcode,
                'balance': result.balance,
                'equity': result.equity,
                'profit': result.profit,
                'margin': result.margin,
                'margin_free': result.margin_free,
                'margin_level': result.margin_level,
                'comment': result.comment,
                'request': result.request._asdict() if hasattr(result.request, '_asdict') else {}
            }
        
        except Exception as e:
            logger.error(f"order_check exception: {e}")
            return None
    
    def send_order(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send order to MT5
        
        Args:
            request: Order request dict
        
        Returns:
            Order result dict or None if failed
        """
        if not self.ensure_connected():
            logger.error("Cannot send order: not connected")
            return None
        
        if self.config.dry_run:
            logger.info(f"DRY_RUN: Would send order: {request}")
            return {
                'retcode': 10008,  # TRADE_RETCODE_DONE
                'deal': 999999,  # Fake deal ticket
                'order': 999999,  # Fake order ticket
                'volume': request.get('volume', 0),
                'price': request.get('price', 0),
                'comment': 'DRY_RUN',
                'request_id': 0
            }
        
        try:
            logger.info(f"Sending order: {request['action']} {request['volume']} "
                       f"{request['symbol']} @ {request.get('price', 'market')}")
            
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                logger.error(f"order_send failed: {error}")
                return None
            
            result_dict = {
                'retcode': result.retcode,
                'retcode_message': MT5Constants.get_retcode_message(result.retcode),
                'deal': result.deal,
                'order': result.order,
                'volume': result.volume,
                'price': result.price,
                'bid': result.bid,
                'ask': result.ask,
                'comment': result.comment,
                'request_id': result.request_id,
                'retcode_external': result.retcode_external
            }
            
            if MT5Constants.is_success(result.retcode):
                logger.info(f"✓ Order executed successfully: "
                          f"Deal #{result.deal}, Order #{result.order}")
            else:
                logger.error(f"✗ Order failed: {result_dict['retcode_message']} "
                           f"(code {result.retcode})")
            
            return result_dict
        
        except Exception as e:
            logger.error(f"order_send exception: {e}", exc_info=True)
            return None
    
    def get_last_error(self) -> tuple:
        """Get last MT5 error"""
        return mt5.last_error()
    
    def __enter__(self):
        """Context manager entry"""
        if not self.initialize():
            raise MT5ConnectionError("Failed to initialize MT5 connection")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()


# Example usage
if __name__ == "__main__":
    from config import LiveConfig, setup_logging
    
    config = LiveConfig()
    logger = setup_logging(config)
    
    # Test connection
    connector = MT5Connector(config)
    
    if connector.initialize():
        print("\n" + "="*50)
        print("MT5 CONNECTION TEST")
        print("="*50)
        
        # Get account info
        account = connector.get_account_info()
        if account:
            print(f"\nAccount: {account['login']}")
            print(f"Balance: ${account['balance']:.2f}")
            print(f"Equity: ${account['equity']:.2f}")
            print(f"Margin Free: ${account['margin_free']:.2f}")
        
        # Test symbol info
        test_symbol = config.symbols[0] if config.symbols else 'EURUSD'
        symbol_info = connector.get_symbol_info(test_symbol)
        if symbol_info:
            print(f"\nSymbol: {symbol_info['name']}")
            print(f"Bid: {symbol_info['bid']:.5f}")
            print(f"Ask: {symbol_info['ask']:.5f}")
            print(f"Spread: {symbol_info['spread']}")
        
        # Get positions
        positions = connector.get_positions()
        print(f"\nOpen Positions: {len(positions)}")
        for pos in positions[:5]:  # Show first 5
            print(f"  {pos['symbol']} {pos['type']} {pos['volume']} @ {pos['price_open']:.5f} "
                  f"(P/L: ${pos['profit']:.2f})")
        
        connector.shutdown()
        print("\n✓ Test completed")
    else:
        print("✗ Connection test failed")
