"""
Live Trading Configuration
Manages settings, environment variables, and trading parameters
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()


@dataclass
class LiveConfig:
    """Configuration for live trading operations"""
    
    # MT5 Connection
    mt5_login: int = int(os.getenv('MT5_LOGIN', '0'))
    mt5_password: str = os.getenv('MT5_PASSWORD', '')
    mt5_server: str = os.getenv('MT5_SERVER', '')
    mt5_path: Optional[str] = os.getenv('MT5_PATH', None)  # Path to terminal64.exe
    mt5_timeout: int = int(os.getenv('MT5_TIMEOUT', '60000'))  # milliseconds
    
    # Trading Parameters
    dry_run: bool = os.getenv('DRY_RUN', 'true').lower() == 'true'
    interval_seconds: int = int(os.getenv('INTERVAL_SECONDS', '60'))
    max_retry_attempts: int = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    retry_backoff_base: float = float(os.getenv('RETRY_BACKOFF_BASE', '2.0'))
    
    # Risk Management
    default_risk_pct: float = float(os.getenv('DEFAULT_RISK_PCT', '1.0'))
    max_position_size: float = float(os.getenv('MAX_POSITION_SIZE', '10.0'))  # lots
    max_daily_trades: int = int(os.getenv('MAX_DAILY_TRADES', '10'))
    max_daily_loss_pct: float = float(os.getenv('MAX_DAILY_LOSS_PCT', '5.0'))
    
    # Strategy Parameters
    symbols: list = field(default_factory=lambda: os.getenv('SYMBOLS', 'EURUSD,GBPUSD').split(','))
    timeframe: str = os.getenv('TIMEFRAME', '1d')
    strategy_id: str = os.getenv('STRATEGY_ID', 'default_strategy')
    magic_number: int = int(os.getenv('MAGIC_NUMBER', '123456'))
    
    # Safety Features
    enable_kill_switch: bool = os.getenv('ENABLE_KILL_SWITCH', 'true').lower() == 'true'
    kill_switch_file: str = os.getenv('KILL_SWITCH_FILE', 'EMERGENCY_STOP')
    require_approval: bool = os.getenv('REQUIRE_APPROVAL', 'false').lower() == 'true'
    
    # Logging & Monitoring
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_dir: Path = field(default_factory=lambda: Path(os.getenv('LOG_DIR', './logs')))
    audit_db_path: Path = field(default_factory=lambda: Path(os.getenv('AUDIT_DB_PATH', './data/audit.db')))
    max_log_size_mb: int = int(os.getenv('MAX_LOG_SIZE_MB', '100'))
    log_backup_count: int = int(os.getenv('LOG_BACKUP_COUNT', '10'))
    
    # Alerts
    enable_alerts: bool = os.getenv('ENABLE_ALERTS', 'false').lower() == 'true'
    alert_webhook_url: Optional[str] = os.getenv('ALERT_WEBHOOK_URL', None)
    telegram_bot_token: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN', None)
    telegram_chat_id: Optional[str] = os.getenv('TELEGRAM_CHAT_ID', None)
    
    # Backtesting Bridge
    backtest_module_path: Path = field(default_factory=lambda: Path(os.getenv(
        'BACKTEST_MODULE_PATH', 
        '../Backtest'
    )))
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        # Create directories if they don't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.audit_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Validate MT5 credentials
        if not self.dry_run:
            if not self.mt5_login or not self.mt5_password or not self.mt5_server:
                raise ValueError(
                    "MT5 credentials missing. Set MT5_LOGIN, MT5_PASSWORD, and MT5_SERVER "
                    "environment variables or enable DRY_RUN mode."
                )
        
        # Validate risk parameters
        if not 0 < self.default_risk_pct <= 100:
            raise ValueError(f"Invalid risk percentage: {self.default_risk_pct}")
        
        if not 0 < self.max_daily_loss_pct <= 100:
            raise ValueError(f"Invalid max daily loss: {self.max_daily_loss_pct}")
        
        # Strip whitespace from symbols
        self.symbols = [s.strip() for s in self.symbols]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)"""
        config_dict = {}
        for key, value in self.__dict__.items():
            if 'password' in key.lower() or 'token' in key.lower():
                config_dict[key] = '***REDACTED***'
            elif isinstance(value, Path):
                config_dict[key] = str(value)
            elif isinstance(value, list):
                config_dict[key] = value.copy()
            else:
                config_dict[key] = value
        return config_dict
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'LiveConfig':
        """Create config from dictionary"""
        return cls(**config_dict)


def setup_logging(config: LiveConfig) -> logging.Logger:
    """Setup structured logging with rotation"""
    from logging.handlers import RotatingFileHandler
    import json
    
    logger = logging.getLogger('LiveTrader')
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # Console handler (formatted)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler (JSON)
    log_file = config.log_dir / 'live_trader.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.max_log_size_mb * 1024 * 1024,
        backupCount=config.log_backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    
    # JSON formatter for structured logs
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                'timestamp': self.formatTime(record, self.datefmt),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Add extra fields if present
            if hasattr(record, 'extra_data'):
                log_obj.update(record.extra_data)
            
            return json.dumps(log_obj)
    
    file_handler.setFormatter(JsonFormatter())
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# Constants for MT5 integration
class MT5Constants:
    """MetaTrader5 constants and mappings"""
    
    # Trade actions
    TRADE_ACTION_DEAL = 1  # Place trade at market price
    TRADE_ACTION_PENDING = 5  # Place pending order
    TRADE_ACTION_SLTP = 6  # Modify SL/TP
    TRADE_ACTION_MODIFY = 7  # Modify pending order
    TRADE_ACTION_REMOVE = 8  # Remove pending order
    TRADE_ACTION_CLOSE_BY = 10  # Close by opposite position
    
    # Order types
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    ORDER_TYPE_SELL_STOP_LIMIT = 7
    
    # Order filling types
    ORDER_FILLING_FOK = 0  # Fill or Kill
    ORDER_FILLING_IOC = 1  # Immediate or Cancel
    ORDER_FILLING_RETURN = 2  # Return (market execution)
    ORDER_FILLING_BOC = 3  # Book or Cancel
    
    # Order time types
    ORDER_TIME_GTC = 0  # Good till cancelled
    ORDER_TIME_DAY = 1  # Good till current trading day
    ORDER_TIME_SPECIFIED = 2  # Good till specified date
    ORDER_TIME_SPECIFIED_DAY = 3  # Good till specified day
    
    # Trade return codes
    RETCODE_SUCCESS_CODES = {
        10008: 'TRADE_RETCODE_DONE',  # Request completed
        10009: 'TRADE_RETCODE_DONE_PARTIAL',  # Partially executed
    }
    
    RETCODE_ERROR_CODES = {
        10004: 'TRADE_RETCODE_REQUOTE',  # Requote
        10006: 'TRADE_RETCODE_REJECT',  # Request rejected
        10007: 'TRADE_RETCODE_CANCEL',  # Request cancelled
        10010: 'TRADE_RETCODE_PLACED',  # Order placed
        10011: 'TRADE_RETCODE_TIMEOUT',  # Request timeout
        10013: 'TRADE_RETCODE_INVALID',  # Invalid request
        10014: 'TRADE_RETCODE_INVALID_VOLUME',  # Invalid volume
        10015: 'TRADE_RETCODE_INVALID_PRICE',  # Invalid price
        10016: 'TRADE_RETCODE_INVALID_STOPS',  # Invalid stops
        10017: 'TRADE_RETCODE_TRADE_DISABLED',  # Trade disabled
        10018: 'TRADE_RETCODE_MARKET_CLOSED',  # Market closed
        10019: 'TRADE_RETCODE_NO_MONEY',  # Insufficient funds
        10020: 'TRADE_RETCODE_PRICE_CHANGED',  # Price changed
        10021: 'TRADE_RETCODE_PRICE_OFF',  # No quotes
        10022: 'TRADE_RETCODE_INVALID_EXPIRATION',  # Invalid expiration
        10023: 'TRADE_RETCODE_ORDER_CHANGED',  # Order state changed
        10024: 'TRADE_RETCODE_TOO_MANY_REQUESTS',  # Too many requests
        10025: 'TRADE_RETCODE_NO_CHANGES',  # No changes
        10026: 'TRADE_RETCODE_SERVER_DISABLES_AT',  # Autotrading disabled by server
        10027: 'TRADE_RETCODE_CLIENT_DISABLES_AT',  # Autotrading disabled by client
        10028: 'TRADE_RETCODE_LOCKED',  # Request locked for processing
        10029: 'TRADE_RETCODE_FROZEN',  # Order/position frozen
        10030: 'TRADE_RETCODE_INVALID_FILL',  # Invalid fill type
        10031: 'TRADE_RETCODE_CONNECTION',  # No connection
        10032: 'TRADE_RETCODE_ONLY_REAL',  # Only real accounts allowed
        10033: 'TRADE_RETCODE_LIMIT_ORDERS',  # Order limit reached
        10034: 'TRADE_RETCODE_LIMIT_VOLUME',  # Volume limit reached
        10035: 'TRADE_RETCODE_INVALID_ORDER',  # Invalid or prohibited order type
        10036: 'TRADE_RETCODE_POSITION_CLOSED',  # Position already closed
        10038: 'TRADE_RETCODE_INVALID_CLOSE_VOLUME',  # Invalid close volume
        10039: 'TRADE_RETCODE_CLOSE_ORDER_EXIST',  # Close order already exists
        10040: 'TRADE_RETCODE_LIMIT_POSITIONS',  # Position limit reached
    }
    
    @staticmethod
    def get_retcode_message(retcode: int) -> str:
        """Get human-readable message for return code"""
        if retcode in MT5Constants.RETCODE_SUCCESS_CODES:
            return MT5Constants.RETCODE_SUCCESS_CODES[retcode]
        elif retcode in MT5Constants.RETCODE_ERROR_CODES:
            return MT5Constants.RETCODE_ERROR_CODES[retcode]
        else:
            return f'UNKNOWN_RETCODE_{retcode}'
    
    @staticmethod
    def is_success(retcode: int) -> bool:
        """Check if return code indicates success"""
        return retcode in MT5Constants.RETCODE_SUCCESS_CODES
