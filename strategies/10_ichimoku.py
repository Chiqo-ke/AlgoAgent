"""
Ichimoku Cloud Strategy
Buy when price above cloud and Tenkan crosses above Kijun, Sell when opposite
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class IchimokuStrategy:
    def __init__(self, symbol='EURUSD=X'):
        self.symbol = symbol
        self.position = None
        self.entry_price = 0
        self.prev_tenkan = None
        self.prev_kijun = None
        
    def calculate_ichimoku(self, data):
        """Calculate Ichimoku Cloud components"""
        # Tenkan-sen (Conversion Line): 9-period
        period9_high = data['High'].rolling(window=9).max()
        period9_low = data['Low'].rolling(window=9).min()
        tenkan = (period9_high + period9_low) / 2
        
        # Kijun-sen (Base Line): 26-period
        period26_high = data['High'].rolling(window=26).max()
        period26_low = data['Low'].rolling(window=26).min()
        kijun = (period26_high + period26_low) / 2
        
        # Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, shifted 26 ahead
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        
        # Senkou Span B (Leading Span B): 52-period, shifted 26 ahead
        period52_high = data['High'].rolling(window=52).max()
        period52_low = data['Low'].rolling(window=52).min()
        senkou_b = ((period52_high + period52_low) / 2).shift(26)
        
        # Chikou Span (Lagging Span): Close shifted 26 behind
        chikou = data['Close'].shift(-26)
        
        return tenkan, kijun, senkou_a, senkou_b, chikou
    
    def on_bar(self, bar, tenkan, kijun, senkou_a, senkou_b, price):
        """Process each bar - unified for backtest and live"""
        signal = None
        
        # Convert to floats to avoid Series comparison issues
        try:
            tenkan = float(tenkan) if not pd.isna(tenkan) else None
            kijun = float(kijun) if not pd.isna(kijun) else None
            senkou_a = float(senkou_a) if not pd.isna(senkou_a) else None
            senkou_b = float(senkou_b) if not pd.isna(senkou_b) else None
            price = float(price) if not pd.isna(price) else None
        except (TypeError, ValueError):
            self.prev_tenkan = tenkan
            self.prev_kijun = kijun
            return signal
        
        if tenkan is None or kijun is None or senkou_a is None or senkou_b is None or price is None:
            self.prev_tenkan = tenkan
            self.prev_kijun = kijun
            return signal
        
        # Determine if price is above or below cloud
        cloud_top = max(senkou_a, senkou_b)
        cloud_bottom = min(senkou_a, senkou_b)
        above_cloud = price > cloud_top
        below_cloud = price < cloud_bottom
        
        # Entry: Tenkan crosses above Kijun while above cloud
        if self.position is None and above_cloud:
            if self.prev_tenkan is not None and self.prev_kijun is not None:
                if self.prev_tenkan <= self.prev_kijun and tenkan > kijun:
                    signal = 'BUY'
                    self.position = 'LONG'
                    self.entry_price = price
        
        # Exit: Tenkan crosses below Kijun or price below cloud
        elif self.position == 'LONG':
            if below_cloud or (self.prev_tenkan is not None and self.prev_kijun is not None and 
                              self.prev_tenkan >= self.prev_kijun and tenkan < kijun):
                signal = 'SELL'
                self.position = None
        
        self.prev_tenkan = tenkan
        self.prev_kijun = kijun
        return signal
    
    def should_enter(self, bar, tenkan, kijun, senkou_a, senkou_b, price):
        """Check entry conditions"""
        if self.prev_tenkan is None:
            return False
        try:
            senkou_a = float(senkou_a) if not pd.isna(senkou_a) else None
            senkou_b = float(senkou_b) if not pd.isna(senkou_b) else None
            if senkou_a is None or senkou_b is None:
                return False
            cloud_top = max(senkou_a, senkou_b)
        except (TypeError, ValueError):
            return False
        above_cloud = price > cloud_top
        return (self.position is None and above_cloud and 
                self.prev_tenkan <= self.prev_kijun and tenkan > kijun)
    
    def should_exit(self, bar, tenkan, kijun, senkou_a, senkou_b, price):
        """Check exit conditions"""
        if self.prev_tenkan is None:
            return False
        try:
            senkou_a = float(senkou_a) if not pd.isna(senkou_a) else None
            senkou_b = float(senkou_b) if not pd.isna(senkou_b) else None
            if senkou_a is None or senkou_b is None:
                return False
            cloud_bottom = min(senkou_a, senkou_b)
        except (TypeError, ValueError):
            return False
        below_cloud = price < cloud_bottom
        return (self.position == 'LONG' and 
                (below_cloud or (self.prev_tenkan >= self.prev_kijun and tenkan < kijun)))

def run_backtest(symbol='EURUSD=X', start_date='2025-02-03', end_date='2026-02-03'):
    """Run backtest with real market data"""
    print(f"\n{'='*60}")
    print(f"ICHIMOKU CLOUD STRATEGY BACKTEST")
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
    strategy = IchimokuStrategy(symbol=symbol)
    
    # Calculate Ichimoku
    data['Tenkan'], data['Kijun'], data['Senkou_A'], data['Senkou_B'], data['Chikou'] = strategy.calculate_ichimoku(data)
    
    # Run backtest
    trades = []
    equity = [10000]
    current_capital = 10000
    position_size = 0
    
    for i in range(len(data)):
        bar = data.iloc[i]
        tenkan = data['Tenkan'].iloc[i]
        kijun = data['Kijun'].iloc[i]
        senkou_a = data['Senkou_A'].iloc[i]
        senkou_b = data['Senkou_B'].iloc[i]
        price = bar['Close']
        
        signal = strategy.on_bar(bar, tenkan, kijun, senkou_a, senkou_b, price)
        
        if signal == 'BUY':
            position_size = current_capital / bar['Close']
            trades.append({
                'Date': data.index[i],
                'Type': 'BUY',
                'Price': bar['Close'],
                'Tenkan': tenkan,
                'Kijun': kijun,
                'Capital': current_capital
            })
        elif signal == 'SELL' and position_size > 0:
            current_capital = position_size * bar['Close']
            pnl = current_capital - trades[-1]['Capital']
            trades.append({
                'Date': data.index[i],
                'Type': 'SELL',
                'Price': bar['Close'],
                'Tenkan': tenkan,
                'Kijun': kijun,
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
            'Strategy': 'Ichimoku Cloud',
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
        'Strategy': 'Ichimoku Cloud',
        'Total Trades': total_trades,
        'Win Rate': f"{win_rate:.2f}%",
        'ROI': f"{roi:.2f}%",
        'Max Drawdown': f"{max_drawdown:.2f}%",
        'Sharpe Ratio': f"{sharpe:.2f}"
    }

if __name__ == '__main__':
    result = run_backtest()
