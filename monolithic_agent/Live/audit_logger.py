"""
Audit Logger - Structured logging and persistent audit trail
"""
import sqlite3
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger('LiveTrader.AuditLogger')


class AuditLogger:
    """
    Persistent audit logging for all trading activities
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize audit logger
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"AuditLogger initialized: {db_path}")
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Signals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    signal_id TEXT UNIQUE,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    confidence REAL,
                    price REAL,
                    strategy_id TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    client_order_id TEXT UNIQUE NOT NULL,
                    signal_id TEXT,
                    symbol TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    side TEXT NOT NULL,
                    volume REAL NOT NULL,
                    price REAL,
                    sl REAL,
                    tp REAL,
                    status TEXT NOT NULL,
                    mt5_order_id INTEGER,
                    mt5_deal_id INTEGER,
                    executed_price REAL,
                    executed_volume REAL,
                    retcode INTEGER,
                    retcode_message TEXT,
                    attempts INTEGER DEFAULT 1,
                    error_message TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Trades table (completed trades)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    volume REAL NOT NULL,
                    profit REAL NOT NULL,
                    commission REAL DEFAULT 0,
                    swap REAL DEFAULT 0,
                    duration_seconds INTEGER,
                    entry_order_id TEXT,
                    exit_order_id TEXT,
                    strategy_id TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Events table (system events, errors, etc.)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Account snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    balance REAL NOT NULL,
                    equity REAL NOT NULL,
                    profit REAL NOT NULL,
                    margin REAL NOT NULL,
                    margin_free REAL NOT NULL,
                    margin_level REAL,
                    open_positions INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
            
            conn.commit()
            logger.info("✓ Audit database initialized")
    
    def log_signal(
        self, 
        signal_id: str,
        symbol: str,
        signal_type: str,
        confidence: float,
        price: float,
        strategy_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a trading signal"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO signals 
                (timestamp, signal_id, symbol, signal_type, confidence, price, strategy_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                signal_id,
                symbol,
                signal_type,
                confidence,
                price,
                strategy_id,
                json.dumps(metadata) if metadata else None
            ))
            
            conn.commit()
    
    def log_order(
        self,
        client_order_id: str,
        signal_id: Optional[str],
        symbol: str,
        order_type: str,
        side: str,
        volume: float,
        price: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an order submission"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO orders 
                (timestamp, client_order_id, signal_id, symbol, order_type, side, 
                 volume, price, sl, tp, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                client_order_id,
                signal_id,
                symbol,
                order_type,
                side,
                volume,
                price,
                sl,
                tp,
                'PENDING',
                json.dumps(metadata) if metadata else None
            ))
            
            conn.commit()
    
    def update_order(
        self,
        client_order_id: str,
        status: str,
        mt5_order_id: Optional[int] = None,
        mt5_deal_id: Optional[int] = None,
        executed_price: Optional[float] = None,
        executed_volume: Optional[float] = None,
        retcode: Optional[int] = None,
        retcode_message: Optional[str] = None,
        attempts: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Update order with execution results"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            update_fields = ['status = ?', 'updated_at = ?']
            values = [status, datetime.now().isoformat()]
            
            if mt5_order_id is not None:
                update_fields.append('mt5_order_id = ?')
                values.append(mt5_order_id)
            
            if mt5_deal_id is not None:
                update_fields.append('mt5_deal_id = ?')
                values.append(mt5_deal_id)
            
            if executed_price is not None:
                update_fields.append('executed_price = ?')
                values.append(executed_price)
            
            if executed_volume is not None:
                update_fields.append('executed_volume = ?')
                values.append(executed_volume)
            
            if retcode is not None:
                update_fields.append('retcode = ?')
                values.append(retcode)
            
            if retcode_message is not None:
                update_fields.append('retcode_message = ?')
                values.append(retcode_message)
            
            if attempts is not None:
                update_fields.append('attempts = ?')
                values.append(attempts)
            
            if error_message is not None:
                update_fields.append('error_message = ?')
                values.append(error_message)
            
            values.append(client_order_id)
            
            cursor.execute(f"""
                UPDATE orders 
                SET {', '.join(update_fields)}
                WHERE client_order_id = ?
            """, values)
            
            conn.commit()
    
    def log_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
        volume: float,
        profit: float,
        duration_seconds: int,
        entry_order_id: str,
        exit_order_id: str,
        strategy_id: str,
        commission: float = 0,
        swap: float = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a completed trade"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO trades 
                (timestamp, symbol, side, entry_price, exit_price, volume, profit,
                 commission, swap, duration_seconds, entry_order_id, exit_order_id,
                 strategy_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                symbol,
                side,
                entry_price,
                exit_price,
                volume,
                profit,
                commission,
                swap,
                duration_seconds,
                entry_order_id,
                exit_order_id,
                strategy_id,
                json.dumps(metadata) if metadata else None
            ))
            
            conn.commit()
    
    def log_event(
        self,
        event_type: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a system event"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO events 
                (timestamp, event_type, severity, message, details)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                event_type,
                severity,
                message,
                json.dumps(details) if details else None
            ))
            
            conn.commit()
    
    def log_account_snapshot(
        self,
        balance: float,
        equity: float,
        profit: float,
        margin: float,
        margin_free: float,
        margin_level: Optional[float],
        open_positions: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log account state snapshot"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO account_snapshots 
                (timestamp, balance, equity, profit, margin, margin_free, 
                 margin_level, open_positions, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                balance,
                equity,
                profit,
                margin,
                margin_free,
                margin_level,
                open_positions,
                json.dumps(metadata) if metadata else None
            ))
            
            conn.commit()
    
    def get_recent_signals(self, limit: int = 100) -> list:
        """Get recent signals"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM signals 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_orders(self, limit: int = 100) -> list:
        """Get recent orders"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM orders 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trades_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get trading summary for last N days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff = cutoff.replace(day=cutoff.day - days)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(profit) as total_profit,
                    AVG(profit) as avg_profit,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as winning_trades,
                    MAX(profit) as max_profit,
                    MIN(profit) as max_loss
                FROM trades
                WHERE timestamp >= ?
            """, (cutoff.isoformat(),))
            
            row = cursor.fetchone()
            
            if row and row[0] > 0:
                return {
                    'total_trades': row[0],
                    'total_profit': row[1] or 0,
                    'avg_profit': row[2] or 0,
                    'winning_trades': row[3] or 0,
                    'win_rate': (row[3] / row[0] * 100) if row[0] > 0 else 0,
                    'max_profit': row[4] or 0,
                    'max_loss': row[5] or 0
                }
            
            return {
                'total_trades': 0,
                'total_profit': 0,
                'avg_profit': 0,
                'winning_trades': 0,
                'win_rate': 0,
                'max_profit': 0,
                'max_loss': 0
            }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test audit logger
    db_path = Path('./data/test_audit.db')
    audit = AuditLogger(db_path)
    
    # Log test data
    audit.log_signal(
        signal_id='test_001',
        symbol='EURUSD',
        signal_type='BUY',
        confidence=0.8,
        price=1.0950,
        strategy_id='RSI_Strategy'
    )
    
    audit.log_order(
        client_order_id='order_001',
        signal_id='test_001',
        symbol='EURUSD',
        order_type='MARKET',
        side='BUY',
        volume=0.01,
        price=1.0950
    )
    
    audit.update_order(
        client_order_id='order_001',
        status='EXECUTED',
        mt5_order_id=123456,
        mt5_deal_id=789012,
        executed_price=1.0951,
        executed_volume=0.01,
        retcode=10008
    )
    
    # Get summary
    summary = audit.get_trades_summary(30)
    print("\nTrades Summary (Last 30 days):")
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Total Profit: ${summary['total_profit']:.2f}")
    print(f"Win Rate: {summary['win_rate']:.1f}%")
    
    print("\n✓ Audit logger test completed")
