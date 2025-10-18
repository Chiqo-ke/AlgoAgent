"""
Order Execution Engine
Handles order submission with retry logic, idempotency, and result tracking
"""
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from config import LiveConfig, MT5Constants
from mt5_connector import MT5Connector

logger = logging.getLogger('LiveTrader.OrderExecutor')


class OrderExecutor:
    """
    Manages order execution with retries and idempotency
    """
    
    def __init__(self, config: LiveConfig, connector: MT5Connector):
        """
        Initialize order executor
        
        Args:
            config: Live trading configuration
            connector: MT5 connector instance
        """
        self.config = config
        self.connector = connector
        self.pending_orders = {}  # client_order_id -> order_request
        self.executed_orders = {}  # client_order_id -> execution_result
        self.failed_orders = {}  # client_order_id -> failure_reason
        
        logger.info("OrderExecutor initialized")
    
    def generate_client_order_id(self, symbol: str, signal_id: str) -> str:
        """
        Generate unique client order ID for idempotency
        
        Args:
            symbol: Trading symbol
            signal_id: Signal identifier
        
        Returns:
            Unique client order ID
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"{symbol}_{signal_id}_{timestamp}_{unique_id}"
    
    def is_duplicate_order(self, client_order_id: str) -> bool:
        """
        Check if order has already been processed
        
        Args:
            client_order_id: Client order identifier
        
        Returns:
            True if order already exists
        """
        return (client_order_id in self.executed_orders or 
                client_order_id in self.pending_orders)
    
    def execute_order(
        self, 
        order_request: Dict[str, Any],
        client_order_id: Optional[str] = None,
        allow_retry: bool = True
    ) -> Dict[str, Any]:
        """
        Execute order with retry logic
        
        Args:
            order_request: MT5 order request dictionary
            client_order_id: Optional unique identifier for idempotency
            allow_retry: Whether to retry on failure
        
        Returns:
            Execution result dictionary with status and details
        """
        # Generate client order ID if not provided
        if not client_order_id:
            client_order_id = self.generate_client_order_id(
                order_request['symbol'],
                str(uuid.uuid4())[:8]
            )
        
        # Check for duplicate
        if self.is_duplicate_order(client_order_id):
            logger.warning(f"Duplicate order detected: {client_order_id}")
            return {
                'success': False,
                'client_order_id': client_order_id,
                'error': 'DUPLICATE_ORDER',
                'message': 'Order already processed'
            }
        
        # Add to pending orders
        self.pending_orders[client_order_id] = {
            'request': order_request,
            'timestamp': datetime.now(),
            'attempts': 0
        }
        
        # Attempt execution with retries
        result = self._execute_with_retry(
            client_order_id, 
            order_request,
            allow_retry
        )
        
        # Move from pending to executed or failed
        if client_order_id in self.pending_orders:
            del self.pending_orders[client_order_id]
        
        if result['success']:
            self.executed_orders[client_order_id] = result
            logger.info(f"✓ Order executed: {client_order_id}")
        else:
            self.failed_orders[client_order_id] = result
            logger.error(f"✗ Order failed: {client_order_id} - {result.get('message')}")
        
        return result
    
    def _execute_with_retry(
        self, 
        client_order_id: str,
        order_request: Dict[str, Any],
        allow_retry: bool
    ) -> Dict[str, Any]:
        """
        Execute order with exponential backoff retry
        
        Args:
            client_order_id: Client order identifier
            order_request: Order request dictionary
            allow_retry: Whether to retry on failure
        
        Returns:
            Execution result
        """
        max_attempts = self.config.max_retry_attempts if allow_retry else 1
        attempt = 0
        last_error = None
        
        while attempt < max_attempts:
            attempt += 1
            self.pending_orders[client_order_id]['attempts'] = attempt
            
            logger.info(f"Order execution attempt {attempt}/{max_attempts}: {client_order_id}")
            
            # Pre-execution check
            precheck = self._precheck_order(order_request)
            if not precheck['valid']:
                return {
                    'success': False,
                    'client_order_id': client_order_id,
                    'error': 'PRECHECK_FAILED',
                    'message': precheck['reason'],
                    'attempts': attempt
                }
            
            # Execute order
            try:
                result = self.connector.send_order(order_request)
                
                if result is None:
                    last_error = "MT5 send_order returned None"
                    logger.error(f"Attempt {attempt} failed: {last_error}")
                else:
                    retcode = result['retcode']
                    
                    if MT5Constants.is_success(retcode):
                        # Success!
                        return {
                            'success': True,
                            'client_order_id': client_order_id,
                            'mt5_order_id': result.get('order'),
                            'mt5_deal_id': result.get('deal'),
                            'executed_price': result.get('price'),
                            'executed_volume': result.get('volume'),
                            'retcode': retcode,
                            'retcode_message': result.get('retcode_message'),
                            'attempts': attempt,
                            'timestamp': datetime.now()
                        }
                    else:
                        # Check if error is retryable
                        if self._is_retryable_error(retcode):
                            last_error = f"Retryable error: {result.get('retcode_message')} (code {retcode})"
                            logger.warning(f"Attempt {attempt} failed with retryable error: {last_error}")
                        else:
                            # Non-retryable error - fail immediately
                            return {
                                'success': False,
                                'client_order_id': client_order_id,
                                'error': 'NON_RETRYABLE_ERROR',
                                'message': result.get('retcode_message'),
                                'retcode': retcode,
                                'attempts': attempt
                            }
            
            except Exception as e:
                last_error = f"Exception during execution: {str(e)}"
                logger.error(f"Attempt {attempt} exception: {e}", exc_info=True)
            
            # If we should retry, wait before next attempt
            if attempt < max_attempts:
                wait_time = self.config.retry_backoff_base ** attempt
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
        
        # All attempts exhausted
        return {
            'success': False,
            'client_order_id': client_order_id,
            'error': 'MAX_RETRIES_EXCEEDED',
            'message': last_error or 'All retry attempts failed',
            'attempts': max_attempts
        }
    
    def _precheck_order(self, order_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-flight checks before sending order
        
        Args:
            order_request: Order request dictionary
        
        Returns:
            Dict with 'valid' (bool) and 'reason' (str)
        """
        # Check required fields
        required_fields = ['action', 'symbol', 'volume', 'type', 'price']
        for field in required_fields:
            if field not in order_request:
                return {
                    'valid': False,
                    'reason': f"Missing required field: {field}"
                }
        
        # Check volume
        volume = order_request['volume']
        if volume <= 0:
            return {
                'valid': False,
                'reason': f"Invalid volume: {volume}"
            }
        
        # Check price
        price = order_request.get('price', 0)
        if price <= 0:
            return {
                'valid': False,
                'reason': f"Invalid price: {price}"
            }
        
        # Use MT5's order_check for detailed validation
        check_result = self.connector.check_order(order_request)
        
        if check_result is None:
            return {
                'valid': False,
                'reason': "MT5 order_check failed"
            }
        
        if not MT5Constants.is_success(check_result['retcode']):
            return {
                'valid': False,
                'reason': f"MT5 check failed: {check_result.get('comment', 'Unknown error')}"
            }
        
        # Check margin requirements
        account = self.connector.get_account_info()
        if account:
            required_margin = check_result.get('margin', 0)
            free_margin = account['margin_free']
            
            if required_margin > free_margin:
                return {
                    'valid': False,
                    'reason': f"Insufficient margin: need ${required_margin:.2f}, have ${free_margin:.2f}"
                }
        
        return {'valid': True, 'reason': ''}
    
    def _is_retryable_error(self, retcode: int) -> bool:
        """
        Determine if error code is retryable
        
        Args:
            retcode: MT5 return code
        
        Returns:
            True if error is temporary and retryable
        """
        retryable_codes = {
            10004,  # TRADE_RETCODE_REQUOTE
            10011,  # TRADE_RETCODE_TIMEOUT
            10020,  # TRADE_RETCODE_PRICE_CHANGED
            10021,  # TRADE_RETCODE_PRICE_OFF
            10024,  # TRADE_RETCODE_TOO_MANY_REQUESTS
            10031,  # TRADE_RETCODE_CONNECTION
        }
        
        return retcode in retryable_codes
    
    def cancel_pending_order(self, client_order_id: str) -> bool:
        """
        Cancel a pending order
        
        Args:
            client_order_id: Client order identifier
        
        Returns:
            True if cancelled successfully
        """
        if client_order_id not in self.pending_orders:
            logger.warning(f"Cannot cancel: order not found: {client_order_id}")
            return False
        
        # Remove from pending
        del self.pending_orders[client_order_id]
        
        # Add to failed with cancellation reason
        self.failed_orders[client_order_id] = {
            'success': False,
            'client_order_id': client_order_id,
            'error': 'CANCELLED',
            'message': 'Order cancelled by user',
            'timestamp': datetime.now()
        }
        
        logger.info(f"Order cancelled: {client_order_id}")
        return True
    
    def get_order_status(self, client_order_id: str) -> Dict[str, Any]:
        """
        Get status of an order
        
        Args:
            client_order_id: Client order identifier
        
        Returns:
            Status dictionary
        """
        if client_order_id in self.executed_orders:
            return {
                'status': 'EXECUTED',
                'details': self.executed_orders[client_order_id]
            }
        elif client_order_id in self.pending_orders:
            return {
                'status': 'PENDING',
                'details': self.pending_orders[client_order_id]
            }
        elif client_order_id in self.failed_orders:
            return {
                'status': 'FAILED',
                'details': self.failed_orders[client_order_id]
            }
        else:
            return {
                'status': 'UNKNOWN',
                'details': None
            }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of execution statistics
        
        Returns:
            Summary dictionary
        """
        total_orders = (len(self.executed_orders) + 
                       len(self.failed_orders) + 
                       len(self.pending_orders))
        
        return {
            'total_orders': total_orders,
            'executed': len(self.executed_orders),
            'failed': len(self.failed_orders),
            'pending': len(self.pending_orders),
            'success_rate': (len(self.executed_orders) / total_orders * 100 
                           if total_orders > 0 else 0)
        }


# Example usage
if __name__ == "__main__":
    from config import LiveConfig, setup_logging
    from mt5_connector import MT5Connector
    
    config = LiveConfig()
    logger = setup_logging(config)
    
    # Initialize connector
    connector = MT5Connector(config)
    
    if connector.initialize():
        executor = OrderExecutor(config, connector)
        
        # Example order request (dry run)
        test_symbol = config.symbols[0] if config.symbols else 'EURUSD'
        symbol_info = connector.get_symbol_info(test_symbol)
        
        if symbol_info:
            order_request = {
                'action': MT5Constants.TRADE_ACTION_DEAL,
                'symbol': test_symbol,
                'volume': 0.01,  # Minimum lot
                'type': MT5Constants.ORDER_TYPE_BUY,
                'price': symbol_info['ask'],
                'deviation': 20,
                'magic': config.magic_number,
                'comment': 'Test order',
                'type_time': MT5Constants.ORDER_TIME_GTC,
                'type_filling': MT5Constants.ORDER_FILLING_IOC,
            }
            
            print("\n" + "="*50)
            print("ORDER EXECUTOR TEST")
            print("="*50)
            print(f"\nTest order: BUY 0.01 {test_symbol} @ {symbol_info['ask']:.5f}")
            
            # Execute order
            result = executor.execute_order(order_request)
            
            print(f"\nResult: {'✓ SUCCESS' if result['success'] else '✗ FAILED'}")
            print(f"Message: {result.get('message', 'N/A')}")
            
            if result['success']:
                print(f"Order ID: {result.get('mt5_order_id')}")
                print(f"Deal ID: {result.get('mt5_deal_id')}")
                print(f"Executed Price: {result.get('executed_price'):.5f}")
            
            # Get summary
            summary = executor.get_execution_summary()
            print(f"\nExecution Summary:")
            print(f"  Total Orders: {summary['total_orders']}")
            print(f"  Executed: {summary['executed']}")
            print(f"  Failed: {summary['failed']}")
            print(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        connector.shutdown()
        print("\n✓ Test completed")
    else:
        print("✗ Connection test failed")
