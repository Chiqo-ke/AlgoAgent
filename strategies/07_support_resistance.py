"""
Support/Resistance Strategy
Identifies support/resistance levels and trades bounces
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SupportResistanceStrategy:
    def __init__(self, symbol='EURUSD=X', lookback=50, threshold=0.0015):
        self.symbol = symbol
        self.lookback = lookback
        self.threshold = threshold  # 0.15% tolerance
        self.position = None
        self.entry_price = 0
        self.support_levels = []
        self.resistance_levels = []
        
    def find_support_resistance(self, data, window=20):
        """Find support and resistance levels"""
        highs = data['High'].rolling(window=window, center=True).max()
        lows = data['Low'].rolling(window=window, center=True).min()
        
        # Find local maxima (resistance)
        resistance = []
        for i in range(window, len(data) - window):
            if data['High'].iloc[i] == highs.iloc[i]:
                resistance.append(data['High'].iloc[i])
        
        # Find local minima (support)
        support = []
        for i in range(window, len(data) - window):
            if data['Low'].iloc[i] == lows.iloc[i]:
                support.append(data['Low'].iloc[i])
        
        # Cluster levels
        def cluster_levels(levels, threshold):
            if not levels:
                return []
            levels = sorted(levels)
            clustered = [levels[0]]
            for level in levels[1:]:
                if abs(level - clustered[-1]) / clustered[-1] > threshold:
                    clustered.append(level)
            return clustered
        
        self.support_levels = cluster_levels(support, self.threshold)
        self.resistance_levels = cluster_levels(resistance, self.threshold)
        
        return self.support_levels, self.resistance_levels
    
    def on_bar(self, bar, price):
        """Process each bar - unified for backtest and live"""
        signal = None
        
        # Check if price is near support
        near_support = False
        for level in self.support_levels:
            if abs(price - level) / level < self.threshold:
                near_support = True
                break
        
        # Check if price is near resistance
        near_resistance = False
        for level in self.resistance_levels:
            if abs(price - level) / level < self.threshold:
                near_resistance = True
                break
        
        # Entry: Bounce from support
        if self.position is None and near_support:
            signal = 'BUY'
            self.position = 'LONG'
            self.entry_price = price
        
        # Exit: Hit resistance
        elif self.position == 'LONG' and near_resistance:
            signal = 'SELL'
            self.position = None
                
        return signal
    
    def should_enter(self, bar, price):
        """Check entry conditions"""
        for level in self.support_levels:
            if abs(price - level) / level < self.threshold:
                return self.position is None
        return False
    
    def should_exit(self, bar, price):
        """Check exit conditions"""
        for level in self.resistance_levels:
            if abs(price - level) / level < self.threshold:
                return self.position == 'LONG'
        return False

def run_backtest(symbol='EURUSD=X', start_date='2025-02-03', end_date='2026-02-03'):
    """Run backtest with real market data"""
    print(f"\n{'='*60}")
    print(f"SUPPORT/RESISTANCE STRATEGY BACKTEST")
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
    strategy = SupportResistanceStrategy(symbol=symbol)
    
    # Find initial support/resistance
    strategy.find_support_resistance(data[:strategy.lookback])
    
    # Run backtest
    trades = []
    equity = [10000]
    current_capital = 10000
    position_size = 0
    
    for i in range(strategy.lookback, len(data)):
        bar = data.iloc[i]
        price = bar['Close']
        
        # Update support/resistance periodically
        if i % 50 == 0:
            strategy.find_support_resistance(data[i-strategy.lookback:i])
        
        signal = strategy.on_bar(bar, price)
        
        if signal == 'BUY':
            position_size = current_capital / bar['Close']
            trades.append({
                'Date': data.index[i],
                'Type': 'BUY',
                'Price': bar['Close'],
                'Capital': current_capital
            })
        elif signal == 'SELL' and position_size > 0:
            current_capital = position_size * bar['Close']
            pnl = current_capital - trades[-1]['Capital']
            trades.append({
                'Date': data.index[i],
                'Type': 'SELL',
                'Price': bar['Close'],
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
            'Strategy': 'Support/Resistance',
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
    print(f"Support Levels Found: {len(strategy.support_levels)}")
    print(f"Resistance Levels Found: {len(strategy.resistance_levels)}")
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
        'Strategy': 'Support/Resistance',
        'Total Trades': total_trades,
        'Win Rate': f"{win_rate:.2f}%",
        'ROI': f"{roi:.2f}%",
        'Max Drawdown': f"{max_drawdown:.2f}%",
        'Sharpe Ratio': f"{sharpe:.2f}"
    }

if __name__ == '__main__':
    result = run_backtest()
