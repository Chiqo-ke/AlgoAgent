"""
SimBrokerAdapter - Wraps SimBroker to implement BaseAdapter protocol.

This adapter allows strategies to use SimBroker for backtesting through
the universal BaseAdapter interface.
"""

from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path
import json

from adapters.base_adapter import BaseAdapter


class SimBrokerAdapter:
    """
    Adapter that wraps SimBroker and implements BaseAdapter protocol.
    
    Usage:
        from simulator.simbroker import SimBroker
        broker = SimBroker(initial_balance=10000, fee=0.001)
        adapter = SimBrokerAdapter(broker)
        
        # Now use adapter with universal interface
        adapter.place_order({'action': 'BUY', 'symbol': 'AAPL', 'volume': 1.0, ...})
    """
    
    def __init__(self, simbroker):
        """
        Initialize adapter with SimBroker instance.
        
        Args:
            simbroker: SimBroker instance to wrap
        """
        self.broker = simbroker
        self._event_log: List[Dict] = []
    
    def place_order(self, order_request: Dict) -> Dict:
        """Place order via SimBroker."""
        try:
            # Extract order parameters
            action = order_request['action']
            symbol = order_request['symbol']
            volume = order_request['volume']
            order_type = order_request.get('type', 'MARKET')
            price = order_request.get('price')
            sl = order_request.get('sl')
            tp = order_request.get('tp')
            comment = order_request.get('comment', '')
            
            # Call SimBroker (assumes it has place_order method)
            result = self.broker.place_order(
                action=action,
                symbol=symbol,
                volume=volume,
                order_type=order_type,
                price=price,
                sl=sl,
                tp=tp,
                comment=comment
            )
            
            # Log event
            self._event_log.append({
                'event': 'order_placed',
                'timestamp': self.broker.current_time if hasattr(self.broker, 'current_time') else None,
                'order_request': order_request,
                'result': result
            })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order."""
        try:
            return self.broker.cancel_order(order_id)
        except Exception as e:
            self._event_log.append({
                'event': 'cancel_failed',
                'order_id': order_id,
                'error': str(e)
            })
            return False
    
    def close_position(self, pos_id: str, price: float = None) -> Dict:
        """Close position."""
        try:
            result = self.broker.close_position(pos_id, price=price)
            
            self._event_log.append({
                'event': 'position_closed_requested',
                'position_id': pos_id,
                'price': price,
                'result': result
            })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def step_bar(self, bar: pd.Series) -> List[Dict]:
        """
        Process one bar via SimBroker.
        
        Returns list of events that occurred (position opens, closes, SL/TP hits).
        """
        try:
            # Call SimBroker's step method
            events = self.broker.step(bar)
            
            # Log all events
            for event in events:
                self._event_log.append({
                    **event,
                    'timestamp': bar.name if hasattr(bar, 'name') else None
                })
            
            return events
            
        except Exception as e:
            error_event = {
                'event': 'step_error',
                'error': str(e),
                'bar': bar.to_dict() if hasattr(bar, 'to_dict') else str(bar)
            }
            self._event_log.append(error_event)
            return [error_event]
    
    def get_positions(self) -> List[Dict]:
        """Get all open positions."""
        return self.broker.get_positions()
    
    def get_account(self) -> Dict:
        """Get account state."""
        return self.broker.get_account()
    
    def generate_report(self) -> Dict:
        """Generate performance report."""
        return self.broker.generate_report()
    
    def save_report(self, out_dir: str) -> Dict[str, str]:
        """
        Save report artifacts.
        
        Creates:
            - trades.csv
            - equity_curve.csv
            - summary.json
            - events.log
        """
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_report()
        saved_files = {}
        
        # Save trades
        if 'trades' in report and report['trades']:
            trades_df = pd.DataFrame(report['trades'])
            trades_path = out_path / 'trades.csv'
            trades_df.to_csv(trades_path, index=False)
            saved_files['trades'] = str(trades_path)
        
        # Save equity curve
        if 'equity_curve' in report and report['equity_curve']:
            equity_df = pd.DataFrame(report['equity_curve'])
            equity_path = out_path / 'equity_curve.csv'
            equity_df.to_csv(equity_path, index=False)
            saved_files['equity_curve'] = str(equity_path)
        
        # Save summary
        summary = {k: v for k, v in report.items() if k not in ['trades', 'equity_curve']}
        summary_path = out_path / 'summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        saved_files['summary'] = str(summary_path)
        
        # Save event log
        events_path = out_path / 'events.log'
        with open(events_path, 'w') as f:
            for event in self._event_log:
                f.write(json.dumps(event) + '\n')
        saved_files['events'] = str(events_path)
        
        return saved_files
