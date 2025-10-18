"""
Simple Web Dashboard - Monitor live trading status
"""
from flask import Flask, render_template_string, jsonify
from datetime import datetime
import threading
import logging

logger = logging.getLogger('LiveTrader.Dashboard')


class Dashboard:
    """
    Simple web dashboard for monitoring
    """
    
    def __init__(self, state_manager, executor, audit_logger, config, port=5000):
        """
        Initialize dashboard
        
        Args:
            state_manager: StateManager instance
            executor: OrderExecutor instance
            audit_logger: AuditLogger instance
            config: LiveConfig instance
            port: Web server port
        """
        self.state = state_manager
        self.executor = executor
        self.audit = audit_logger
        self.config = config
        self.port = port
        
        self.app = Flask(__name__)
        self.app.logger.setLevel(logging.WARNING)
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"Dashboard initialized on port {port}")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return render_template_string(DASHBOARD_HTML)
        
        @self.app.route('/api/status')
        def status():
            """Get current status"""
            state_summary = self.state.get_state_summary()
            exec_summary = self.executor.get_execution_summary()
            
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'mode': 'DRY RUN' if self.config.dry_run else 'LIVE',
                'trading_enabled': state_summary['trading_enabled'],
                'kill_switch_active': state_summary['kill_switch_active'],
                'positions': {
                    'open': state_summary['open_positions'],
                    'symbols': state_summary['positions']
                },
                'daily': {
                    'trades': state_summary['daily_trades'],
                    'pnl': state_summary['daily_pnl']
                },
                'orders': {
                    'total': exec_summary['total_orders'],
                    'executed': exec_summary['executed'],
                    'failed': exec_summary['failed'],
                    'pending': exec_summary['pending'],
                    'success_rate': exec_summary['success_rate']
                }
            })
        
        @self.app.route('/api/positions')
        def positions():
            """Get open positions"""
            return jsonify(list(self.state.positions.values()))
        
        @self.app.route('/api/recent_orders')
        def recent_orders():
            """Get recent orders"""
            orders = self.audit.get_recent_orders(limit=20)
            return jsonify(orders)
        
        @self.app.route('/api/recent_signals')
        def recent_signals():
            """Get recent signals"""
            signals = self.audit.get_recent_signals(limit=20)
            return jsonify(signals)
        
        @self.app.route('/api/summary')
        def summary():
            """Get trading summary"""
            summary = self.audit.get_trades_summary(days=30)
            return jsonify(summary)
    
    def start(self):
        """Start dashboard in background thread"""
        def run_app():
            self.app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)
        
        thread = threading.Thread(target=run_app, daemon=True)
        thread.start()
        
        logger.info(f"✓ Dashboard running at http://127.0.0.1:{self.port}")


# HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AlgoAgent Live Trader Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 32px; margin-bottom: 10px; }
        .header .status { font-size: 14px; opacity: 0.9; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card h3 {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .card .value {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }
        .card .subvalue {
            font-size: 14px;
            color: #999;
            margin-top: 5px;
        }
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        .table-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f9fafb;
            font-weight: 600;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-success { background: #d1fae5; color: #065f46; }
        .badge-error { background: #fee2e2; color: #991b1b; }
        .badge-warning { background: #fef3c7; color: #92400e; }
        .badge-info { background: #dbeafe; color: #1e40af; }
        .timestamp { color: #999; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AlgoAgent Live Trader</h1>
            <div class="status">
                <span id="mode">Loading...</span> • 
                <span id="timestamp">-</span> • 
                Status: <span id="trading-status">-</span>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Open Positions</h3>
                <div class="value" id="open-positions">-</div>
                <div class="subvalue" id="position-symbols">-</div>
            </div>
            <div class="card">
                <h3>Daily Trades</h3>
                <div class="value" id="daily-trades">-</div>
                <div class="subvalue">Orders executed today</div>
            </div>
            <div class="card">
                <h3>Daily P/L</h3>
                <div class="value" id="daily-pnl">-</div>
                <div class="subvalue">Profit & Loss</div>
            </div>
            <div class="card">
                <h3>Success Rate</h3>
                <div class="value" id="success-rate">-</div>
                <div class="subvalue" id="order-stats">-</div>
            </div>
        </div>

        <div class="table-container">
            <h3 style="margin-bottom: 15px;">Recent Signals</h3>
            <table id="signals-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Symbol</th>
                        <th>Signal</th>
                        <th>Price</th>
                        <th>Strategy</th>
                    </tr>
                </thead>
                <tbody id="signals-body">
                    <tr><td colspan="5">Loading...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="table-container">
            <h3 style="margin-bottom: 15px;">Recent Orders</h3>
            <table id="orders-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Volume</th>
                        <th>Price</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="orders-body">
                    <tr><td colspan="6">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function updateDashboard() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('mode').textContent = data.mode;
                    document.getElementById('timestamp').textContent = new Date(data.timestamp).toLocaleTimeString();
                    document.getElementById('trading-status').textContent = 
                        data.trading_enabled ? '✓ Enabled' : '✗ Disabled';
                    
                    document.getElementById('open-positions').textContent = data.positions.open;
                    document.getElementById('position-symbols').textContent = 
                        data.positions.symbols.join(', ') || 'No positions';
                    
                    document.getElementById('daily-trades').textContent = data.daily.trades;
                    
                    const pnl = data.daily.pnl;
                    const pnlEl = document.getElementById('daily-pnl');
                    pnlEl.textContent = '$' + pnl.toFixed(2);
                    pnlEl.className = 'value ' + (pnl >= 0 ? 'positive' : 'negative');
                    
                    document.getElementById('success-rate').textContent = data.orders.success_rate.toFixed(1) + '%';
                    document.getElementById('order-stats').textContent = 
                        `${data.orders.executed}/${data.orders.total} executed`;
                });
            
            fetch('/api/recent_signals')
                .then(r => r.json())
                .then(signals => {
                    const tbody = document.getElementById('signals-body');
                    if (signals.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="5">No signals yet</td></tr>';
                        return;
                    }
                    tbody.innerHTML = signals.slice(0, 10).map(s => `
                        <tr>
                            <td class="timestamp">${new Date(s.timestamp).toLocaleTimeString()}</td>
                            <td><strong>${s.symbol}</strong></td>
                            <td><span class="badge badge-${s.signal_type === 'BUY' ? 'success' : s.signal_type === 'SELL' ? 'error' : 'info'}">${s.signal_type}</span></td>
                            <td>${parseFloat(s.price).toFixed(5)}</td>
                            <td>${s.strategy_id}</td>
                        </tr>
                    `).join('');
                });
            
            fetch('/api/recent_orders')
                .then(r => r.json())
                .then(orders => {
                    const tbody = document.getElementById('orders-body');
                    if (orders.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="6">No orders yet</td></tr>';
                        return;
                    }
                    tbody.innerHTML = orders.slice(0, 10).map(o => `
                        <tr>
                            <td class="timestamp">${new Date(o.timestamp).toLocaleTimeString()}</td>
                            <td><strong>${o.symbol}</strong></td>
                            <td>${o.side}</td>
                            <td>${o.volume}</td>
                            <td>${o.executed_price ? parseFloat(o.executed_price).toFixed(5) : '-'}</td>
                            <td><span class="badge badge-${o.status === 'EXECUTED' ? 'success' : o.status === 'FAILED' ? 'error' : 'warning'}">${o.status}</span></td>
                        </tr>
                    `).join('');
                });
        }
        
        // Update every 2 seconds
        updateDashboard();
        setInterval(updateDashboard, 2000);
    </script>
</body>
</html>
"""


# Example usage
if __name__ == "__main__":
    from config import LiveConfig
    from state_manager import StateManager
    from order_executor import OrderExecutor
    from audit_logger import AuditLogger
    from mt5_connector import MT5Connector
    
    config = LiveConfig()
    state = StateManager(config)
    connector = MT5Connector(config)
    executor = OrderExecutor(config, connector)
    audit = AuditLogger(config.audit_db_path)
    
    dashboard = Dashboard(state, executor, audit, config)
    dashboard.start()
    
    print("Dashboard running at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped")
