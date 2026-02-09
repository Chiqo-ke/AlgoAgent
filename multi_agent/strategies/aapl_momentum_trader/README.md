# AAPL Momentum Trading Strategy

A comprehensive algorithmic trading system for Apple Inc. (AAPL) stock using momentum-based signals with RSI and SMA indicators. Supports both backtesting and live trading via MetaTrader 5.

## Features

- **Multi-Mode Operation**: Backtest, Demo, and Live trading modes
- **Technical Indicators**: RSI (14-period) and SMA (20-period)
- **Risk Management**: 2% risk per trade with dynamic position sizing
- **Data Sources**: Yahoo Finance (backtesting) and MT5 (live trading)
- **Comprehensive Logging**: Detailed trade and performance logging
- **Position Management**: Automated stop loss and take profit management

## Strategy Logic

### Entry Conditions
- **Long Entry**: RSI > 50 AND Price > SMA(20)
- **Short Entry**: RSI < 50 AND Price < SMA(20)

### Risk Management
- **Position Size**: 2% risk per trade
- **Stop Loss**: 100 pips or 1.5x ATR (dynamic)
- **Take Profit**: 2:1 risk-reward ratio
- **Maximum Positions**: 1 concurrent position
- **Maximum Spread**: 5 pips

## Installation

### Prerequisites
```bash
pip install pandas numpy matplotlib seaborn yfinance MetaTrader5
```

### Project Structure
```
aapl_momentum_trader/
├── config.py              # Configuration settings
├── data_manager.py        # Data acquisition and management
├── indicators.py          # Technical indicators and signals
├── risk_management.py     # Risk and position management
├── backtester.py          # Backtesting engine
├── mt5_trader.py          # MetaTrader 5 integration
├── main.py               # Main strategy controller
└── README.md             # This file
```

## Configuration

Edit `config.py` to customize:

### MT5 Settings
```python
MT5_CONFIG = {
    'server': 'MetaQuotes-Demo',
    'login': YOUR_ACCOUNT_LOGIN,
    'password': 'YOUR_PASSWORD',
    'timeout': 60000,
    'portable': False
}
```

### Strategy Parameters
```python
STRATEGY_CONFIG = {
    'symbol': 'AAPL',
    'timeframe': 'H1',
    'rsi_period': 14,
    'sma_period': 20,
    'rsi_long_threshold': 50,
    'rsi_short_threshold': 50
}
```

### Risk Settings
```python
RISK_CONFIG = {
    'risk_per_trade': 0.02,  # 2% per trade
    'max_positions': 1,
    'stop_loss_pips': 100,
    'take_profit_ratio': 2,
    'max_spread': 5
}
```

## Usage

### Backtesting
```bash
python main.py --mode backtest
```

### Demo Trading
```bash
python main.py --mode demo
```

### Live Trading
```bash
python main.py --mode live
```

## Example Output

### Backtest Results
```
AAPL MOMENTUM TRADING STRATEGY - BACKTEST RESULTS
================================================

PERFORMANCE SUMMARY
------------------
Initial Balance:     $10,000.00
Final Equity:        $12,500.00
Total Return:        25.00%
Total P&L:          $2,500.00
Max Drawdown:       -8.50%
Sharpe Ratio:       1.250

TRADE STATISTICS
---------------
Total Trades:       45
Winning Trades:     28
Losing Trades:      17
Win Rate:           62.2%
Profit Factor:      1.85

Average Win:        $180.50
Average Loss:       $95.25
Largest Win:        $450.00
Largest Loss:       $200.00
```

## Key Components

### 1. Data Manager (`data_manager.py`)
- Supports multiple data sources (Yahoo Finance, MT5)
- Data validation and cleaning
- Real-time and historical data acquisition

### 2. Signal Generator (`indicators.py`)
- RSI and SMA calculation
- Signal strength assessment
- Entry/exit signal generation

### 3. Risk Manager (`risk_management.py`)
- Position sizing based on account risk
- Stop loss and take profit calculation
- Trade validation logic

### 4. Position Manager (`risk_management.py`)
- Track open and closed positions
- Calculate unrealized/realized P&L
- Trading statistics and performance metrics

### 5. MT5 Trader (`mt5_trader.py`)
- Direct integration with MetaTrader 5
- Order placement and management
- Real-time market data access

### 6. Backtester (`backtester.py`)
- Historical strategy testing
- Performance analysis and reporting
- Equity curve and drawdown visualization

## Risk Disclaimer

This trading algorithm is for educational and research purposes. Trading involves substantial risk and may not be suitable for all investors. Past performance does not guarantee future results.

**Important Considerations:**
- Always test on demo accounts before live trading
- Never risk more than you can afford to lose
- Market conditions can change rapidly
- Algorithm performance may vary in different market conditions

## License

This project is for educational purposes. Use at your own risk.

## Support

For issues and questions:
1. Check the logs in `aapl_momentum.log`
2. Verify MT5 connection settings
3. Ensure all dependencies are installed
4. Test with demo account first