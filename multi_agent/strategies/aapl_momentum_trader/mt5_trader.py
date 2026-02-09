import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging
from datetime import datetime
import time

class MT5Trader:
    """Live trading interface for MetaTrader 5"""
    
    def __init__(self, server: str, login: int, password: str):
        self.server = server
        self.login = login
        self.password = password
        self.connected = False
        self.logger = logging.getLogger(__name__)
        
        # Trading state
        self.positions = {}
        self.orders = {}
        
    def connect(self) -> bool:
        """Connect to MT5 terminal"""
        if not mt5.initialize():
            self.logger.error(f"MT5 initialization failed: {mt5.last_error()}")
            return False
        
        if not mt5.login(self.login, password=self.password, server=self.server):
            self.logger.error(f"MT5 login failed: {mt5.last_error()}")
            mt5.shutdown()
            return False
        
        self.connected = True
        account_info = mt5.account_info()
        if account_info:
            self.logger.info(f"Connected to MT5 - Account: {account_info.login}, "
                           f"Balance: ${account_info.balance:.2f}, "
                           f"Equity: ${account_info.equity:.2f}")
        
        return True
    
    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            self.logger.info("Disconnected from MT5")
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        if not self.connected:
            return {}
        
        account_info = mt5.account_info()
        if account_info is None:
            return {}
        
        return {
            'login': account_info.login,
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'margin_free': account_info.margin_free,
            'margin_level': account_info.margin_level,
            'currency': account_info.currency,
            'server': account_info.server,
            'leverage': account_info.leverage
        }
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """Get symbol information"""
        if not self.connected:
            return {}
        
        info = mt5.symbol_info(symbol)
        if info is None:
            self.logger.error(f"Failed to get symbol info for {symbol}")
            return {}
        
        return {
            'symbol': info.name,
            'point': info.point,
            'digits': info.digits,
            'spread': info.spread,
            'trade_tick_value': info.trade_tick_value,
            'trade_tick_size': info.trade_tick_size,
            'minimum_volume': info.volume_min,
            'maximum_volume': info.volume_max,
            'volume_step': info.volume_step,
            'bid': info.bid,
            'ask': info.ask
        }
    
    def place_order(self, symbol: str, order_type: str, volume: float,
                   price: float = None, stop_loss: float = None,
                   take_profit: float = None, comment: str = "") -> Dict:
        """
        Place a trading order
        
        Args:
            symbol: Trading symbol
            order_type: 'buy' or 'sell'
            volume: Order volume
            price: Order price (None for market orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
            comment: Order comment
            
        Returns:
            Order result dictionary
        """
        if not self.connected:
            return {'success': False, 'error': 'Not connected to MT5'}
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {'success': False, 'error': f'Symbol {symbol} not found'}
        
        # Determine order type
        if order_type.lower() == 'buy':
            if price is None:
                action = mt5.ORDER_TYPE_BUY
                price = symbol_info.ask
            else:
                action = mt5.ORDER_TYPE_BUY_LIMIT if price < symbol_info.ask else mt5.ORDER_TYPE_BUY_STOP
        else:  # sell
            if price is None:
                action = mt5.ORDER_TYPE_SELL
                price = symbol_info.bid
            else:
                action = mt5.ORDER_TYPE_SELL_LIMIT if price > symbol_info.bid else mt5.ORDER_TYPE_SELL_STOP
        
        # Create order request
        request = {
            'action': mt5.TRADE_ACTION_DEAL if price is None else mt5.TRADE_ACTION_PENDING,
            'symbol': symbol,
            'volume': volume,
            'type': action,
            'price': price,
            'deviation': 20,  # Price deviation
            'magic': 234000,  # Magic number
            'comment': comment,
            'type_time': mt5.ORDER_TIME_GTC,  # Good till cancelled
            'type_filling': mt5.ORDER_FILLING_IOC  # Immediate or cancel
        }
        
        # Add stop loss and take profit if provided
        if stop_loss is not None:
            request['sl'] = stop_loss
        
        if take_profit is not None:
            request['tp'] = take_profit
        
        # Send order
        result = mt5.order_send(request)
        
        if result is None:
            return {'success': False, 'error': 'Order send failed'}
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = f"Order failed: {result.retcode} - {result.comment}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        self.logger.info(f"Order placed successfully: {order_type} {volume} {symbol} "
                        f"@ {price:.5f}, Order: {result.order}")
        
        return {
            'success': True,
            'order_id': result.order,
            'ticket': result.deal,
            'volume': result.volume,
            'price': result.price,
            'comment': result.comment
        }
    
    def close_position(self, ticket: int) -> Dict:
        """Close a position by ticket"""
        if not self.connected:
            return {'success': False, 'error': 'Not connected to MT5'}
        
        # Get position info
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return {'success': False, 'error': f'Position {ticket} not found'}
        
        position = position[0]
        symbol = position.symbol
        volume = position.volume
        position_type = position.type
        
        # Determine close order type
        if position_type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        
        # Create close request
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': volume,
            'type': order_type,
            'position': ticket,
            'price': price,
            'deviation': 20,
            'magic': 234000,
            'comment': "Close position",
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC
        }
        
        # Send close order
        result = mt5.order_send(request)
        
        if result is None:
            return {'success': False, 'error': 'Close order send failed'}
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = f"Close failed: {result.retcode} - {result.comment}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        self.logger.info(f"Position {ticket} closed successfully @ {result.price:.5f}")
        
        return {
            'success': True,
            'ticket': ticket,
            'close_price': result.price,
            'volume': result.volume
        }
    
    def get_positions(self, symbol: str = None) -> List[Dict]:
        """Get open positions"""
        if not self.connected:
            return []
        
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
        
        if positions is None:
            return []
        
        position_list = []
        for pos in positions:
            position_info = {
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'long' if pos.type == mt5.POSITION_TYPE_BUY else 'short',
                'volume': pos.volume,
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'profit': pos.profit,
                'swap': pos.swap,
                'comment': pos.comment,
                'time': datetime.fromtimestamp(pos.time),
                'sl': pos.sl,
                'tp': pos.tp
            }
            position_list.append(position_info)
        
        return position_list
    
    def get_orders(self, symbol: str = None) -> List[Dict]:
        """Get pending orders"""
        if not self.connected:
            return []
        
        if symbol:
            orders = mt5.orders_get(symbol=symbol)
        else:
            orders = mt5.orders_get()
        
        if orders is None:
            return []
        
        order_list = []
        for order in orders:
            order_info = {
                'ticket': order.ticket,
                'symbol': order.symbol,
                'type': order.type,
                'volume': order.volume,
                'price_open': order.price_open,
                'sl': order.sl,
                'tp': order.tp,
                'comment': order.comment,
                'time_setup': datetime.fromtimestamp(order.time_setup),
                'magic': order.magic
            }
            order_list.append(order_info)
        
        return order_list
    
    def cancel_order(self, ticket: int) -> Dict:
        """Cancel a pending order"""
        if not self.connected:
            return {'success': False, 'error': 'Not connected to MT5'}
        
        request = {
            'action': mt5.TRADE_ACTION_REMOVE,
            'order': ticket
        }
        
        result = mt5.order_send(request)
        
        if result is None:
            return {'success': False, 'error': 'Cancel order send failed'}
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = f"Cancel failed: {result.retcode} - {result.comment}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        self.logger.info(f"Order {ticket} cancelled successfully")
        
        return {'success': True, 'ticket': ticket}
    
    def modify_position(self, ticket: int, stop_loss: float = None, 
                       take_profit: float = None) -> Dict:
        """Modify position stop loss and take profit"""
        if not self.connected:
            return {'success': False, 'error': 'Not connected to MT5'}
        
        # Get current position
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return {'success': False, 'error': f'Position {ticket} not found'}
        
        position = position[0]
        
        request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'symbol': position.symbol,
            'position': ticket,
            'sl': stop_loss if stop_loss is not None else position.sl,
            'tp': take_profit if take_profit is not None else position.tp
        }
        
        result = mt5.order_send(request)
        
        if result is None:
            return {'success': False, 'error': 'Modify position send failed'}
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = f"Modify failed: {result.retcode} - {result.comment}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        self.logger.info(f"Position {ticket} modified successfully")
        
        return {'success': True, 'ticket': ticket}
    
    def get_market_price(self, symbol: str) -> Dict:
        """Get current market price"""
        if not self.connected:
            return {}
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {}
        
        return {
            'symbol': symbol,
            'bid': tick.bid,
            'ask': tick.ask,
            'spread': (tick.ask - tick.bid) / mt5.symbol_info(symbol).point,
            'time': datetime.fromtimestamp(tick.time)
        }