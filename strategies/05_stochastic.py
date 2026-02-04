"""
Stochastic Oscillator Strategy
Buy when %K crosses above %D in oversold zone (<20), Sell when %K crosses below %D in overbought zone (>80)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class StochasticStrategy:
    def __init__(self, symbol='EURUSD=X', k_period=14, d_period=3, oversold=20, overbought=80):
        self.symbol = symbol
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought
        self.position = None
        self.entry_price = 0
        self.prev_k = None
        self.prev_d = None
        
    def calculate_stochastic(self, data):
        """Calculate Stochastic Oscillator"""
        # %K
        low_min = data['Low'].rolling(window=self.k_period).min()
        high_max = data['High'].rolling(window=self.k_period).max()
        k = 100 * (data['Close'] - low_min) / (high_max - low_min)
        
        # %D (SMA of %K)
        d = k.rolling(window=self.d_period).mean()
        
        return k, d
    
    def on_bar(self, bar, k, d):
        """Process each bar - unified for backtest and live"""
        signal = None
        
        if pd.isna(k) or pd.isna(d):
            return signal
        
        # Detect crossover
        if self.prev_k is not None and self.prev_d is not None:
            # Bullish: %K crosses above %D in oversold
            if self.prev_k <= self.prev_d and k > d and k < self.oversold:
                if self.position is None:
                    signal = 'BUY'
                    self.position = 'LONG'
                    self.entry_price = bar['Close']
            
            # Bearish: %K crosses below %D in overbought
            elif self.prev_k >= self.prev_d and k < d and k > self.overbought:
                if self.position == 'LONG':
                    signal = 'SELL'
                    self.position = None
        
        self.prev_k = k
        self.prev_d = d
        return signal
    
    def should_enter(self, bar, k, d):
        """Check entry conditions"""
        if self.prev_k is None:
            return False
        return self.position is None and self.prev_k <= self.prev_d and k > d and k < self.oversold
    
    def should_exit(self, bar, k, d):
        """Check exit conditions"""
        if self.prev_k is None:
            return False
        return self.position == 'LONG' and self.prev_k >= self.prev_d and k < d and k > self.overbought

def run_backtest(symbol='EURUSD=X', start_date='2025-02-03', end_date='2026-02-03'):
    """Run backtest with real market data"""
    print(f"\n{'='*60}")
    print(f"STOCHASTIC OSCILLATOR STRATEGY BACKTEST")
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
    strategy = StochasticStrategy(symbol=symbol)
    
    # Calculate Stochastic
    data['%K'], data['%D'] = strategy.calculate_stochastic(data)
    
    # Run backtest
    trades = []
    equity = [10000]
    current_capital = 10000
    position_size = 0
    
    for i in range(len(data)):
        bar = data.iloc[i]
        k = data['%K'].iloc[i]
        d = data['%D'].iloc[i]
        
        signal = strategy.on_bar(bar, k, d)
        
        if signal == 'BUY':
            position_size = current_capital / bar['Close']
            trades.append({
                'Date': data.index[i],
                'Type': 'BUY',
                'Price': bar['Close'],
                '%K': k,
                '%D': d,
                'Capital': current_capital
            })
        elif signal == 'SELL' and position_size > 0:
            current_capital = position_size * bar['Close']
            pnl = current_capital - trades[-1]['Capital']
            trades.append({
                'Date': data.index[i],
                'Type': 'SELL',
                'Price': bar['Close'],
                '%K': k,
                '%D': d,
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
            'Strategy': 'Stochastic Oscillator',
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
        'Strategy': 'Stochastic Oscillator',
        'Total Trades': total_trades,
        'Win Rate': f"{win_rate:.2f}%",
        'ROI': f"{roi:.2f}%",
        'Max Drawdown': f"{max_drawdown:.2f}%",
        'Sharpe Ratio': f"{sharpe:.2f}"
    }

if __name__ == '__main__':
    result = run_backtest()
