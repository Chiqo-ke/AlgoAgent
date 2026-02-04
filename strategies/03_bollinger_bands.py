"""
Bollinger Bands Breakout Strategy
Buy when price breaks above upper band, Sell when price breaks below lower band
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class BollingerBandsStrategy:
    def __init__(self, symbol='EURUSD=X', period=20, std_dev=2):
        self.symbol = symbol
        self.period = period
        self.std_dev = std_dev
        self.position = None
        self.entry_price = 0
        
    def calculate_bollinger_bands(self, data):
        """Calculate Bollinger Bands"""
        sma = data['Close'].rolling(window=self.period).mean()
        std = data['Close'].rolling(window=self.period).std()
        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)
        return sma, upper_band, lower_band
    
    def on_bar(self, bar, upper, lower, prev_close):
        """Process each bar - unified for backtest and live"""
        signal = None
        
        if pd.isna(upper) or pd.isna(lower):
            return signal
        
        # Entry: Price breaks above upper band
        if self.position is None:
            if prev_close <= upper and bar['Close'] > upper:
                signal = 'BUY'
                self.position = 'LONG'
                self.entry_price = bar['Close']
        
        # Exit: Price breaks below lower band
        elif self.position == 'LONG':
            if prev_close >= lower and bar['Close'] < lower:
                signal = 'SELL'
                self.position = None
                
        return signal
    
    def should_enter(self, bar, upper, prev_close):
        """Check entry conditions"""
        return self.position is None and prev_close <= upper and bar['Close'] > upper
    
    def should_exit(self, bar, lower, prev_close):
        """Check exit conditions"""
        return self.position == 'LONG' and prev_close >= lower and bar['Close'] < lower

def run_backtest(symbol='EURUSD=X', start_date='2025-02-03', end_date='2026-02-03'):
    """Run backtest with real market data"""
    print(f"\n{'='*60}")
    print(f"BOLLINGER BANDS BREAKOUT STRATEGY BACKTEST")
    print(f"{'='*60}")
    print(f"Symbol: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    
    # Fetch data
    print("\nFetching market data...")
    data = yf.download(symbol, start=start_date, end=end_date, interval='1h', progress=False)
    
    if data.empty:
        print("ERROR: No data retrieved. Trying daily interval...")
        data = yf.download(symbol, start=start_date, end=end_date, interval='1d', progress=False)
    
    if data.empty:
        print("ERROR: Still no data. Check symbol or date range.")
        return None
    
    print(f"Data points: {len(data)}")
    
    # Initialize strategy
    strategy = BollingerBandsStrategy(symbol=symbol)
    
    # Calculate Bollinger Bands
    data['SMA'], data['Upper'], data['Lower'] = strategy.calculate_bollinger_bands(data)
    data['Prev_Close'] = data['Close'].shift(1)
    
    # Run backtest
    trades = []
    equity = [10000]
    current_capital = 10000
    position_size = 0
    
    for i in range(1, len(data)):
        bar = data.iloc[i]
        upper = data['Upper'].iloc[i]
        lower = data['Lower'].iloc[i]
        prev_close = data['Prev_Close'].iloc[i]
        
        signal = strategy.on_bar(bar, upper, lower, prev_close)
        
        if signal == 'BUY':
            position_size = current_capital / bar['Close']
            trades.append({
                'Date': data.index[i],
                'Type': 'BUY',
                'Price': bar['Close'],
                'Upper': upper,
                'Capital': current_capital
            })
        elif signal == 'SELL' and position_size > 0:
            current_capital = position_size * bar['Close']
            pnl = current_capital - trades[-1]['Capital']
            trades.append({
                'Date': data.index[i],
                'Type': 'SELL',
                'Price': bar['Close'],
                'Lower': lower,
                'Capital': current_capital,
                'PnL': pnl
            })
            position_size = 0
        
        if position_size > 0:
            equity.append(position_size * bar['Close'])
        else:
            equity.append(current_capital)
    
    if position_size > 0:
        current_capital = position_size * data['Close'].iloc[-1]
        equity[-1] = current_capital
    
    # Calculate metrics
    trades_df = pd.DataFrame(trades)
    
    if len(trades_df) < 2:
        print("\nNot enough trades executed.")
        return {
            'Strategy': 'Bollinger Bands Breakout',
            'Total Trades': 0,
            'Win Rate': 0,
            'ROI': 0,
            'Max Drawdown': 0,
            'Sharpe Ratio': 0
        }
    
    sell_trades = trades_df[trades_df['Type'] == 'SELL']
    total_trades = len(sell_trades)
    winning_trades = len(sell_trades[sell_trades['PnL'] > 0]) if 'PnL' in sell_trades.columns else 0
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    final_capital = equity[-1]
    roi = ((final_capital - 10000) / 10000) * 100
    
    equity_series = pd.Series(equity)
    rolling_max = equity_series.expanding().max()
    drawdown = (equity_series - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()
    
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    
    print(f"\n{'='*60}")
    print("BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {winning_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Starting Capital: $10,000")
    print(f"Final Capital: ${final_capital:,.2f}")
    print(f"ROI: {roi:.2f}%")
    print(f"Max Drawdown: {max_drawdown:.2f}%")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"{'='*60}\n")
    
    return {
        'Strategy': 'Bollinger Bands Breakout',
        'Total Trades': total_trades,
        'Win Rate': f"{win_rate:.2f}%",
        'ROI': f"{roi:.2f}%",
        'Max Drawdown': f"{max_drawdown:.2f}%",
        'Sharpe Ratio': f"{sharpe:.2f}"
    }

if __name__ == '__main__':
    result = run_backtest()
