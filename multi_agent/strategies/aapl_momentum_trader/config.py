# Configuration settings for AAPL Momentum Trading Strategy

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
    'symbol': 'AAPL',
    'timeframe': 'H1',  # 1 hour timeframe
    'rsi_period': 14,
    'sma_period': 20,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    'rsi_long_threshold': 50,
    'rsi_short_threshold': 50
}

# Risk Management
RISK_CONFIG = {
    'risk_per_trade': 0.02,  # 2% risk per trade
    'max_positions': 1,
    'stop_loss_pips': 100,
    'take_profit_ratio': 2,  # 2:1 reward to risk
    'max_spread': 5  # Max spread in pips
}

# TradingView Configuration (if using TV data)
TV_CONFIG = {
    'username': 'your_tv_username',
    'password': 'your_tv_password',
    'exchange': 'NASDAQ',
    'symbol': 'AAPL'
}

# Backtesting Configuration
BACKTEST_CONFIG = {
    'start_date': '2023-01-01',
    'end_date': '2024-12-31',
    'initial_balance': 10000,
    'commission': 0.0001,  # 0.01%
    'slippage': 1  # 1 pip
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'file': 'aapl_momentum.log'
}