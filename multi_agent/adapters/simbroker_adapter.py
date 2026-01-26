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
            # SimBroker expects a dictionary in MT5 format
            # Pass the order_request directly to SimBroker
            result = self.broker.place_order(order_request)
            
            # Log event
            self._event_log.append({
                'event': 'order_placed',
                'timestamp': self.broker.current_time if hasattr(self.broker, 'current_time') else None,
                'order_request': order_request,
                'result': result
            })
            
            # Convert OrderResponse to dict
            # Success if order was accepted, filled, or partially filled (not rejected)
            status_value = result.status.value if hasattr(result.status, 'value') else str(result.status)
            return {
                'success': status_value.lower() not in ['rejected', 'cancelled', 'failed'],
                'order_id': result.order_id,
                'status': status_value,
                'message': result.message
            }
            
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
            # Call SimBroker's step_bar method
            events = self.broker.step_bar(bar)
            
            # Convert Event objects to dicts
            event_dicts = []
            for event in events:
                if hasattr(event, '__dict__'):
                    event_dict = {k: v for k, v in event.__dict__.items()}
                else:
                    event_dict = dict(event) if isinstance(event, dict) else {'event': str(event)}
                
                event_dict['timestamp'] = bar.name if hasattr(bar, 'name') else None
                self._event_log.append(event_dict)
                event_dicts.append(event_dict)
            
            return event_dicts
            
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
        positions = self.broker.get_positions()
        # Convert Position objects to dicts
        position_dicts = []
        for pos in positions:
            if hasattr(pos, '__dict__'):
                pos_dict = {k: v for k, v in pos.__dict__.items()}
            else:
                pos_dict = dict(pos) if isinstance(pos, dict) else {'position': str(pos)}
            position_dicts.append(pos_dict)
        return position_dicts
    
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
                # Convert any non-serializable objects to strings
                serializable_event = {}
                for key, value in event.items():
                    if hasattr(value, '__dict__'):
                        # Convert objects to dict representation
                        serializable_event[key] = str(value)
                    else:
                        serializable_event[key] = value
                f.write(json.dumps(serializable_event, default=str) + '\n')
        saved_files['events'] = str(events_path)
        
        return saved_files
