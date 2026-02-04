"""
Price Action (Candlestick Patterns) Strategy
Detects bullish/bearish engulfing, hammer, shooting star patterns
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class PriceActionStrategy:
    def __init__(self, symbol='EURUSD=X'):
        self.symbol = symbol
        self.position = None
        self.entry_price = 0
        
    def detect_bullish_engulfing(self, prev_bar, curr_bar):
        """Detect bullish engulfing pattern"""
        prev_body = prev_bar['Close'] - prev_bar['Open']
        curr_body = curr_bar['Close'] - curr_bar['Open']
        
        # Previous bearish, current bullish and engulfs
        return (prev_body < 0 and curr_body > 0 and 
                curr_bar['Open'] < prev_bar['Close'] and 
                curr_bar['Close'] > prev_bar['Open'])
    
    def detect_bearish_engulfing(self, prev_bar, curr_bar):
        """Detect bearish engulfing pattern"""
        prev_body = prev_bar['Close'] - prev_bar['Open']
        curr_body = curr_bar['Close'] - curr_bar['Open']
        
        # Previous bullish, current bearish and engulfs
        return (prev_body > 0 and curr_body < 0 and 
                curr_bar['Open'] > prev_bar['Close'] and 
                curr_bar['Close'] < prev_bar['Open'])
    
    def detect_hammer(self, bar):
        """Detect hammer pattern (bullish reversal)"""
        body = abs(bar['Close'] - bar['Open'])
        lower_shadow = min(bar['Open'], bar['Close']) - bar['Low']
        upper_shadow = bar['High'] - max(bar['Open'], bar['Close'])
        
        # Lower shadow 2x body, small upper shadow
        return lower_shadow > 2 * body and upper_shadow < body * 0.3
    
    def detect_shooting_star(self, bar):
        """Detect shooting star pattern (bearish reversal)"""
        body = abs(bar['Close'] - bar['Open'])
        upper_shadow = bar['High'] - max(bar['Open'], bar['Close'])
        lower_shadow = min(bar['Open'], bar['Close']) - bar['Low']
        
        # Upper shadow 2x body, small lower shadow
        return upper_shadow > 2 * body and lower_shadow < body * 0.3
    
    def on_bar(self, prev_bar, curr_bar):
        """Process each bar - unified for backtest and live"""
        signal = None
        
        # Entry signals
        if self.position is None:
            if self.detect_bullish_engulfing(prev_bar, curr_bar) or self.detect_hammer(curr_bar):
                signal = 'BUY'
                self.position = 'LONG'
                self.entry_price = curr_bar['Close']
        
        # Exit signals
        elif self.position == 'LONG':
            if self.detect_bearish_engulfing(prev_bar, curr_bar) or self.detect_shooting_star(curr_bar):
                signal = 'SELL'
                self.position = None
                
        return signal
    
    def should_enter(self, prev_bar, curr_bar):
        """Check entry conditions"""
        return self.position is None and (
            self.detect_bullish_engulfing(prev_bar, curr_bar) or 
            self.detect_hammer(curr_bar)
        )
    
    def should_exit(self, prev_bar, curr_bar):
        """Check exit conditions"""
        return self.position == 'LONG' and (
            self.detect_bearish_engulfing(prev_bar, curr_bar) or 
            self.detect_shooting_star(curr_bar)
        )

def run_backtest(symbol='EURUSD=X', start_date='2025-02-03', end_date='2026-02-03'):
    """Run backtest with real market data"""
    print(f"\n{'='*60}")
    print(f"PRICE ACTION (CANDLESTICK) STRATEGY BACKTEST")
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
    strategy = PriceActionStrategy(symbol=symbol)
    
    # Run backtest
    trades = []
    equity = [10000]
    current_capital = 10000
    position_size = 0
    
    for i in range(1, len(data)):
        prev_bar = data.iloc[i-1]
        curr_bar = data.iloc[i]
        
        signal = strategy.on_bar(prev_bar, curr_bar)
        
        if signal == 'BUY':
            position_size = current_capital / curr_bar['Close']
            trades.append({
                'Date': data.index[i],
                'Type': 'BUY',
                'Price': curr_bar['Close'],
                'Capital': current_capital
            })
        elif signal == 'SELL' and position_size > 0:
            current_capital = position_size * curr_bar['Close']
            pnl = current_capital - trades[-1]['Capital']
            trades.append({
                'Date': data.index[i],
                'Type': 'SELL',
                'Price': curr_bar['Close'],
                'Capital': current_capital,
                'PnL': pnl
            })
            position_size = 0
        
        if position_size > 0:
            equity.append(position_size * curr_bar['Close'])
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
            'Strategy': 'Price Action (Candlestick)',
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
        'Strategy': 'Price Action (Candlestick)',
        'Total Trades': total_trades,
        'Win Rate': f"{win_rate:.2f}%",
        'ROI': f"{roi:.2f}%",
        'Max Drawdown': f"{max_drawdown:.2f}%",
        'Sharpe Ratio': f"{sharpe:.2f}"
    }

if __name__ == '__main__':
    result = run_backtest()
