"""
RSI Momentum Strategy
Buy when RSI < 30 (oversold), Sell when RSI > 70 (overbought)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class RSIStrategy:
    def __init__(self, symbol='EURUSD=X', period=14, oversold=30, overbought=70):
        self.symbol = symbol
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.position = None
        self.entry_price = 0
        
    def calculate_rsi(self, data, period=14):
        """Calculate RSI indicator"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def on_bar(self, bar, rsi):
        """Process each bar - unified for backtest and live"""
        signal = None
        
        if pd.isna(rsi):
            return signal
            
        # Entry logic
        if self.position is None:
            if rsi < self.oversold:
                signal = 'BUY'
                self.position = 'LONG'
                self.entry_price = bar['Close']
        
        # Exit logic
        elif self.position == 'LONG':
            if rsi > self.overbought:
                signal = 'SELL'
                self.position = None
                
        return signal
    
    def should_enter(self, bar, rsi):
        """Check entry conditions"""
        return self.position is None and rsi < self.oversold
    
    def should_exit(self, bar, rsi):
        """Check exit conditions"""
        return self.position == 'LONG' and rsi > self.overbought

def run_backtest(symbol='EURUSD=X', start_date='2025-02-03', end_date='2026-02-03'):
    """Run backtest with real market data"""
    print(f"\n{'='*60}")
    print(f"RSI MOMENTUM STRATEGY BACKTEST")
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
    strategy = RSIStrategy(symbol=symbol)
    
    # Calculate RSI
    data['RSI'] = strategy.calculate_rsi(data, strategy.period)
    
    # Run backtest
    trades = []
    equity = [10000]  # Starting capital
    current_capital = 10000
    position_size = 0
    
    for i in range(len(data)):
        bar = data.iloc[i]
        rsi = data['RSI'].iloc[i]
        
        signal = strategy.on_bar(bar, rsi)
        
        if signal == 'BUY':
            position_size = current_capital / bar['Close']
            trades.append({
                'Date': data.index[i],
                'Type': 'BUY',
                'Price': bar['Close'],
                'RSI': rsi,
                'Capital': current_capital
            })
        elif signal == 'SELL' and position_size > 0:
            current_capital = position_size * bar['Close']
            pnl = current_capital - trades[-1]['Capital']
            trades.append({
                'Date': data.index[i],
                'Type': 'SELL',
                'Price': bar['Close'],
                'RSI': rsi,
                'Capital': current_capital,
                'PnL': pnl
            })
            position_size = 0
        
        # Track equity
        if position_size > 0:
            equity.append(position_size * bar['Close'])
        else:
            equity.append(current_capital)
    
    # Close any open position
    if position_size > 0:
        current_capital = position_size * data['Close'].iloc[-1]
        equity[-1] = current_capital
    
    # Calculate metrics
    trades_df = pd.DataFrame(trades)
    
    if len(trades_df) < 2:
        print("\nNot enough trades executed.")
        return {
            'Strategy': 'RSI Momentum',
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
    
    # Calculate max drawdown
    equity_series = pd.Series(equity)
    rolling_max = equity_series.expanding().max()
    drawdown = (equity_series - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()
    
    # Calculate Sharpe ratio
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    
    # Print results
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
        'Strategy': 'RSI Momentum',
        'Total Trades': total_trades,
        'Win Rate': f"{win_rate:.2f}%",
        'ROI': f"{roi:.2f}%",
        'Max Drawdown': f"{max_drawdown:.2f}%",
        'Sharpe Ratio': f"{sharpe:.2f}"
    }

if __name__ == '__main__':
    result = run_backtest()
