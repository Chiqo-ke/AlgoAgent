"""
VWAP (Volume Weighted Average Price) Strategy
Buy when price crosses above VWAP, Sell when price crosses below VWAP
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class VWAPStrategy:
    def __init__(self, symbol='EURUSD=X'):
        self.symbol = symbol
        self.position = None
        self.entry_price = 0
        self.prev_price = None
        self.prev_vwap = None
        
    def calculate_vwap(self, data):
        """Calculate VWAP"""
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        
        # For intraday VWAP, reset daily
        data['Date'] = data.index.date
        
        vwap_list = []
        for date in data['Date'].unique():
            day_data = data[data['Date'] == date]
            cumulative_tp_volume = (typical_price.loc[day_data.index] * day_data['Volume']).cumsum()
            cumulative_volume = day_data['Volume'].cumsum()
            vwap = cumulative_tp_volume / cumulative_volume
            vwap_list.extend(vwap.values)
        
        return pd.Series(vwap_list, index=data.index)
    
    def on_bar(self, bar, vwap, price):
        """Process each bar - unified for backtest and live"""
        signal = None
        
        if pd.isna(vwap) or self.prev_price is None or self.prev_vwap is None:
            self.prev_price = price
            self.prev_vwap = vwap
            return signal
        
        # Entry: Price crosses above VWAP
        if self.position is None:
            if self.prev_price <= self.prev_vwap and price > vwap:
                signal = 'BUY'
                self.position = 'LONG'
                self.entry_price = price
        
        # Exit: Price crosses below VWAP
        elif self.position == 'LONG':
            if self.prev_price >= self.prev_vwap and price < vwap:
                signal = 'SELL'
                self.position = None
        
        self.prev_price = price
        self.prev_vwap = vwap
        return signal
    
    def should_enter(self, bar, vwap, price):
        """Check entry conditions"""
        if self.prev_price is None:
            return False
        return self.position is None and self.prev_price <= self.prev_vwap and price > vwap
    
    def should_exit(self, bar, vwap, price):
        """Check exit conditions"""
        if self.prev_price is None:
            return False
        return self.position == 'LONG' and self.prev_price >= self.prev_vwap and price < vwap

def run_backtest(symbol='EURUSD=X', start_date='2025-02-03', end_date='2026-02-03'):
    """Run backtest with real market data"""
    print(f"\n{'='*60}")
    print(f"VWAP STRATEGY BACKTEST")
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
    strategy = VWAPStrategy(symbol=symbol)
    
    # Calculate VWAP
    data['VWAP'] = strategy.calculate_vwap(data)
    
    # Run backtest
    trades = []
    equity = [10000]
    current_capital = 10000
    position_size = 0
    
    for i in range(len(data)):
        bar = data.iloc[i]
        vwap = data['VWAP'].iloc[i]
        price = bar['Close']
        
        signal = strategy.on_bar(bar, vwap, price)
        
        if signal == 'BUY':
            position_size = current_capital / bar['Close']
            trades.append({
                'Date': data.index[i],
                'Type': 'BUY',
                'Price': bar['Close'],
                'VWAP': vwap,
                'Capital': current_capital
            })
        elif signal == 'SELL' and position_size > 0:
            current_capital = position_size * bar['Close']
            pnl = current_capital - trades[-1]['Capital']
            trades.append({
                'Date': data.index[i],
                'Type': 'SELL',
                'Price': bar['Close'],
                'VWAP': vwap,
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
            'Strategy': 'VWAP',
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
        'Strategy': 'VWAP',
        'Total Trades': total_trades,
        'Win Rate': f"{win_rate:.2f}%",
        'ROI': f"{roi:.2f}%",
        'Max Drawdown': f"{max_drawdown:.2f}%",
        'Sharpe Ratio': f"{sharpe:.2f}"
    }

if __name__ == '__main__':
    result = run_backtest()
