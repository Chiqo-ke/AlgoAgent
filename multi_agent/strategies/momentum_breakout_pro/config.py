# Configuration settings for Momentum Breakout Pro Strategy

# MT5 Configuration
MT5_CONFIG = {
    'server': 'MetaQuotes-Demo',  # Change to your broker's server
    'login': 12345678,  # Your demo account login
    'password': 'your_password',  # Your demo account password
    'timeout': 60000,
    'portable': False
}

# Strategy Parameters
STRATEGY_CONFIG = {
    'strategy_name': 'Momentum Breakout Pro',
    'symbols': ['EURUSD', 'AAPL', 'MSFT'],
    'primary_timeframe': 'M15',  # 15-minute primary timeframe
    'trend_timeframe': 'H4',     # 4-hour trend bias
    'confirmation_timeframe': 'H1',  # 1-hour confirmation
    
    # Technical Indicator Settings
    'ema_trend_period': 50,      # 4H trend EMA
    'ema_short_period': 20,      # 15M short-term EMA
    'atr_period': 14,            # ATR calculation period
    'rsi_period': 14,            # RSI calculation period
    'bb_period': 20,             # Bollinger Bands period
    'bb_std_dev': 2.0,           # Bollinger Bands standard deviation
    'volume_sma_period': 20,     # Volume moving average
    'volume_short_period': 5,    # Short-term volume average
    'breakout_period': 20,       # Period for high/low calculation
    
    # Entry Criteria
    'volume_surge_multiplier': 1.5,     # Volume surge detection
    'volume_confirmation_multiplier': 1.8,  # Volume confirmation
    'rsi_long_min': 45,          # RSI minimum for long entry
    'rsi_long_max': 75,          # RSI maximum for long entry  
    'rsi_short_min': 25,         # RSI minimum for short entry
    'rsi_short_max': 55,         # RSI maximum for short entry
    'bb_compression_percentile': 40,     # BB width compression threshold
    'breakout_proximity': 0.005,         # 0.5% proximity to breakout level
    'resistance_support_buffer': 0.02,   # 2% buffer for R/S levels
    
    # Pattern Recognition
    'candle_close_threshold': 0.75,      # Candle close in top/bottom 75%
    'min_gap_atr_multiplier': 1.5,      # Minimum gap size relative to ATR
    'atr_expansion_periods': 2,          # Periods for ATR expansion check
}

# Symbol-Specific Parameters
SYMBOL_CONFIGS = {
    'EURUSD': {
        'max_spread_pips': 2.5,
        'trading_hours': {'start': 12, 'end': 16},  # UTC hours (London/NY overlap)
        'min_gap_pips': 25,
        'atr_threshold_pips': 15,
        'point_value': 0.0001,
    },
    'AAPL': {
        'max_spread_percent': 0.0003,  # 0.03% of price
        'trading_hours': {'start': 14.5, 'end': 20.5},  # UTC hours (9:30-15:30 EST)
        'min_gap_dollars': 2.50,
        'atr_threshold_dollars': 1.00,
        'point_value': 0.01,
    },
    'MSFT': {
        'max_spread_percent': 0.0003,  # 0.03% of price
        'trading_hours': {'start': 14.5, 'end': 20.5},  # UTC hours (9:30-15:30 EST)
        'min_gap_dollars': 3.00,
        'atr_threshold_dollars': 1.25,
        'point_value': 0.01,
    }
}

# Risk Management Configuration
RISK_CONFIG = {
    'risk_per_trade': 0.02,         # 2% risk per trade
    'max_positions': 3,             # Maximum concurrent positions
    'max_symbol_positions': 1,      # Maximum positions per symbol
    'stop_loss_atr_multiplier': 1.5,    # Stop loss distance in ATR
    'min_stop_loss_percent': 0.008,     # Minimum stop loss (0.8% forex)
    'min_stop_loss_percent_stocks': 0.012,  # Minimum stop loss (1.2% stocks)
    'max_stop_loss_percent': 0.025,     # Maximum stop loss (2.5%)
    
    # Take Profit Targets
    'tp1_ratio': 1.5,               # First target at 1.5R
    'tp1_position_percent': 0.5,    # Close 50% at first target
    'tp2_ratio': 2.5,               # Second target at 2.5R  
    'tp2_position_percent': 0.3,    # Close 30% at second target
    'tp3_trailing_atr': 1.2,        # Trailing stop for remaining 20%
    
    # Time-Based Rules
    'max_hold_hours': 48,           # Maximum hold time in hours
    'friday_close_enabled': True,   # Close positions before Friday close
    'max_spread_filter': True,      # Enable spread filtering
    
    # Portfolio Risk
    'max_daily_loss_percent': 0.06,     # 6% daily loss limit
    'max_drawdown_percent': 0.12,       # 12% maximum drawdown
    'max_correlation': 0.6,             # Maximum position correlation
    'max_sector_exposure': 0.4,         # 40% maximum sector exposure
}

# Trading Session Configuration  
TRADING_SESSIONS = {
    'EURUSD': {
        'london_start': 8,   # UTC
        'london_end': 17,
        'ny_start': 13,
        'ny_end': 22,
        'overlap_start': 13,  # London/NY overlap
        'overlap_end': 17,
    },
    'STOCKS': {
        'premarket_start': 9,     # UTC (4 AM EST)
        'market_open': 14.5,      # UTC (9:30 AM EST)
        'market_close': 21,       # UTC (4 PM EST)
        'aftermarket_end': 1,     # UTC (8 PM EST next day)
        'avoid_first_30min': True,
    }
}

# Backtesting Configuration
BACKTEST_CONFIG = {
    'start_date': '2022-01-01',
    'end_date': '2024-12-31',
    'initial_balance': 100000,
    'commission_forex': 0,           # Usually included in spread
    'commission_stocks': 7,          # $7 per round trip
    'slippage_pips': 0.5,           # 0.5 pips average slippage
    'slippage_stocks': 0.02,        # $0.02 average slippage
    
    # Transaction Cost Modeling
    'spread_eurusd': 0.8,           # 0.8 pips average
    'spread_aapl': 0.015,           # $0.015 average
    'spread_msft': 0.015,           # $0.015 average
    
    # Performance Targets
    'target_win_rate': 0.60,        # 60% target win rate
    'target_profit_factor': 1.4,    # Target profit factor
    'target_sharpe_ratio': 1.2,     # Target Sharpe ratio
    'target_max_dd': 0.12,          # Target maximum drawdown
}

# News and Risk Events Configuration
NEWS_CONFIG = {
    'high_impact_buffer_minutes': 30,   # Avoid trading 30min before/after high impact news
    'economic_calendar_enabled': True,
    'major_events': [
        'FOMC', 'NFP', 'CPI', 'GDP', 'ECB', 'BOE',
        'EARNINGS', 'FED_SPEECH', 'ECB_SPEECH'
    ]
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'momentum_breakout_pro.log',
    'max_file_size': '10MB',
    'backup_count': 5,
    'console_output': True
}

# Alert and Monitoring Configuration
ALERT_CONFIG = {
    'email_enabled': False,
    'discord_enabled': False,
    'telegram_enabled': False,
    'alert_on_entry': True,
    'alert_on_exit': True,
    'alert_on_error': True,
    'performance_alerts': {
        'daily_loss_threshold': 0.03,      # Alert if daily loss > 3%
        'drawdown_threshold': 0.08,        # Alert if drawdown > 8%
        'consecutive_losses': 5,           # Alert after 5 consecutive losses
    }
}

# Development and Testing Flags
DEV_CONFIG = {
    'debug_mode': False,
    'paper_trading': True,
    'log_all_signals': True,
    'save_trade_screenshots': False,
    'performance_monitoring': True,
    'real_time_plotting': False,
}