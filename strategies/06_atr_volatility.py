"""
ATR Volatility Breakout Strategy
Buy when price breaks above (High - ATR*multiplier), Sell when price breaks below (Low + ATR*multiplier)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ATRStrategy:
    def __init__(self, symbol='EURUSD=X', atr_period=14, multiplier=2.0):
        self.symbol = symbol
        self.atr_period = atr_period
        self.multiplier = multiplier
        self.position = None
        self.entry_price = 0
        self.stop_loss = 0
        
    def calculate_atr(self, data):
        """Calculate Average True Range"""
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(self.atr_period).mean()
        
        return atr
    
    def on_bar(self, bar, atr, prev_high, prev_low):
        """Process each bar - unified for backtest and live"""
        signal = None
        
        if pd.isna(atr):
            return signal
        
        # Calculate breakout levels
        upper_level = prev_high + (atr * self.multiplier)
        lower_level = prev_low - (atr * self.multiplier)
        
        # Entry: Volatility breakout
        if self.position is None:
            if bar['Close'] > upper_level:
                signal = 'BUY'
                self.position = 'LONG'
                self.entry_price = bar['Close']
                self.stop_loss = bar['Close'] - (atr * self.multiplier)
        
        # Exit: Stop loss or reverse breakout
        elif self.position == 'LONG':
            if bar['Close'] < self.stop_loss or bar['Close'] < lower_level:
                signal = 'SELL'
                self.position = None
                
        return signal
    
    def should_enter(self, bar, atr, prev_high):
        """Check entry conditions"""
        upper_level = prev_high + (atr * self.multiplier)
        return self.position is None and bar['Close'] > upper_level
    
    def should_exit(self, bar, atr, prev_low):
        """Check exit conditions"""
        lower_level = prev_low - (atr * self.multiplier)
        return self.position == 'LONG' and (bar['Close'] < self.stop_loss or bar['Close'] < lower_level)

def run_backtest(symbol='EURUSD=X', start_date='2025-02-03', end_date='2026-02-03'):
    """Run backtest with real market data"""
    print(f"\n{'='*60}")
    print(f"ATR VOLATILITY BREAKOUT STRATEGY BACKTEST")
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
    strategy = ATRStrategy(symbol=symbol)
    
    # Calculate ATR
    data['ATR'] = strategy.calculate_atr(data)
    data['Prev_High'] = data['High'].shift(1)
    data['Prev_Low'] = data['Low'].shift(1)
    
    # Run backtest
    trades = []
    equity = [10000]
    current_capital = 10000
    position_size = 0
    
    for i in range(1, len(data)):
        bar = data.iloc[i]
        atr = data['ATR'].iloc[i]
        prev_high = data['Prev_High'].iloc[i]
        prev_low = data['Prev_Low'].iloc[i]
        
        signal = strategy.on_bar(bar, atr, prev_high, prev_low)
        
        if signal == 'BUY':
            position_size = current_capital / bar['Close']
            trades.append({
                'Date': data.index[i],
                'Type': 'BUY',
                'Price': bar['Close'],
                'ATR': atr,
                'Capital': current_capital
            })
        elif signal == 'SELL' and position_size > 0:
            current_capital = position_size * bar['Close']
            pnl = current_capital - trades[-1]['Capital']
            trades.append({
                'Date': data.index[i],
                'Type': 'SELL',
                'Price': bar['Close'],
                'ATR': atr,
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
            'Strategy': 'ATR Volatility Breakout',
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
        'Strategy': 'ATR Volatility Breakout',
        'Total Trades': total_trades,
        'Win Rate': f"{win_rate:.2f}%",
        'ROI': f"{roi:.2f}%",
        'Max Drawdown': f"{max_drawdown:.2f}%",
        'Sharpe Ratio': f"{sharpe:.2f}"
    }

if __name__ == '__main__':
    result = run_backtest()
