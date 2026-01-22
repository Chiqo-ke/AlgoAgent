"""
Django management command to create system templates.
"""
from django.core.management.base import BaseCommand
from strategy_api.models import StrategyTemplate


class Command(BaseCommand):
    help = 'Create system templates for strategy generation fallback'
    
    def create_momentum_template(self):
        """Create momentum strategy template"""
        template_code = '''import yfinance as yf
import pandas as pd
from backtesting import Strategy, Backtest
from backtesting.lib import crossover
import talib as ta

class MomentumStrategy(Strategy):
    ema_short = 50
    ema_long = 100
    
    def init(self):
        close = self.data.Close
        self.ema_short_line = self.I(ta.EMA, close, self.ema_short)
        self.ema_long_line = self.I(ta.EMA, close, self.ema_long)
    
    def next(self):
        if crossover(self.ema_short_line, self.ema_long_line):
            if not self.position:
                self.buy()
        elif crossover(self.ema_long_line, self.ema_short_line):
            if self.position:
                self.position.close()

if __name__ == "__main__":
    # Download historical data
    data = yf.download('AAPL', period='1y', interval='1d', progress=False)
    
    # Flatten column index if MultiIndex (yfinance issue with single ticker)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Run backtest
    bt = Backtest(data, MomentumStrategy, cash=10000, commission=0.002)
    stats = bt.run()
    
    # Print metrics in parseable format
    print(f"Return [Avg]: {stats['Return [%]']:.2f}%")
    print(f"Sharpe Ratio: {stats.get('Sharpe Ratio', 0):.2f}")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate: {stats.get('Win Rate [%]', 0):.2f}%")
    print(f"Total Trades: {stats['# Trades']}")
'''
        
        template, created = StrategyTemplate.objects.update_or_create(
            name='System Momentum Strategy',
            defaults={
                'description': 'A momentum-based trading strategy that buys on strong positive momentum and exits on weakness',
                'category': 'momentum',
                'template_code': template_code,
                'is_system_template': True,
                'is_active': True,
                'latest_strategy_code': template_code,
                'parameters_schema': {
                    'keywords': 'momentum,trend,rate of change,price momentum,uptrend,trend following,ema,crossover'
                }
            }
        )
        
        return template, created
    
    def create_mean_reversion_template(self):
        """Create mean reversion strategy template"""
        template_code = '''import yfinance as yf
import pandas as pd
from backtesting import Strategy, Backtest
import talib as ta

class MeanReversionStrategy(Strategy):
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    
    def init(self):
        close = self.data.Close
        self.rsi = self.I(ta.RSI, close, self.rsi_period)
    
    def next(self):
        if self.rsi < self.rsi_oversold:
            if not self.position:
                self.buy()
        elif self.rsi > self.rsi_overbought:
            if self.position:
                self.position.close()

if __name__ == "__main__":
    # Download historical data
    data = yf.download('AAPL', period='1y', interval='1d', progress=False)
    
    # Flatten column index if MultiIndex (yfinance issue with single ticker)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Run backtest
    bt = Backtest(data, MeanReversionStrategy, cash=10000, commission=0.002)
    stats = bt.run()
    
    # Print metrics in parseable format
    print(f"Return [Avg]: {stats['Return [%]']:.2f}%")
    print(f"Sharpe Ratio: {stats.get('Sharpe Ratio', 0):.2f}")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate: {stats.get('Win Rate [%]', 0):.2f}%")
    print(f"Total Trades: {stats['# Trades']}")
'''
        
        template, created = StrategyTemplate.objects.update_or_create(
            name='System Mean Reversion Strategy',
            defaults={
                'description': 'A mean reversion strategy that buys when price drops significantly below average and exits on reversion',
                'category': 'mean_reversion',
                'template_code': template_code,
                'is_system_template': True,
                'is_active': True,
                'latest_strategy_code': template_code,
                'parameters_schema': {
                    'keywords': 'mean reversion,oversold,overbought,bollinger,statistical arbitrage,reversion,oscillator,rsi'
                }
            }
        )
        
        return template, created
    
    def create_breakout_template(self):
        """Create breakout strategy template"""
        template_code = '''import yfinance as yf
import pandas as pd
from backtesting import Strategy, Backtest
import talib as ta
import numpy as np

class BreakoutStrategy(Strategy):
    lookback_period = 20
    
    def init(self):
        self.highest = self.I(ta.MAX, self.data.High, self.lookback_period)
        self.lowest = self.I(ta.MIN, self.data.Low, self.lookback_period)
    
    def next(self):
        price = self.data.Close[-1]
        
        # Buy on breakout above resistance
        if price > self.highest[-2]:  # Previous period's high
            if not self.position:
                self.buy()
        
        # Sell on breakdown below support
        elif price < self.lowest[-2]:  # Previous period's low
            if self.position:
                self.position.close()

if __name__ == "__main__":
    # Download historical data
    data = yf.download('AAPL', period='1y', interval='1d', progress=False)
    
    # Flatten column index if MultiIndex (yfinance issue with single ticker)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Run backtest
    bt = Backtest(data, BreakoutStrategy, cash=10000, commission=0.002)
    stats = bt.run()
    
    # Print metrics in parseable format
    print(f"Return [Avg]: {stats['Return [%]']:.2f}%")
    print(f"Sharpe Ratio: {stats.get('Sharpe Ratio', 0):.2f}")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate: {stats.get('Win Rate [%]', 0):.2f}%")
    print(f"Total Trades: {stats['# Trades']}")
'''
        
        template, created = StrategyTemplate.objects.update_or_create(
            name='System Breakout Strategy',
            defaults={
                'description': 'A breakout strategy that enters on price breaking above resistance levels',
                'category': 'breakout',
                'template_code': template_code,
                'is_system_template': True,
                'is_active': True,
                'latest_strategy_code': template_code,
                'parameters_schema': {
                    'keywords': 'breakout,resistance,support,channel,range,volatility breakout,consolidation'
                }
            }
        )
        
        return template, created
    
    def create_scalping_template(self):
        """Create scalping strategy template"""
        template_code = '''import yfinance as yf
import pandas as pd
from backtesting import Strategy, Backtest
from backtesting.lib import crossover
import talib as ta

class ScalpingStrategy(Strategy):
    short_window = 5
    long_window = 20
    take_profit_pct = 0.01  # 1%
    stop_loss_pct = 0.005   # 0.5%
    
    def init(self):
        close = self.data.Close
        self.short_ma = self.I(ta.SMA, close, self.short_window)
        self.long_ma = self.I(ta.SMA, close, self.long_window)
        self.entry_price = None
    
    def next(self):
        price = self.data.Close[-1]
        
        # Entry: MA crossover
        if crossover(self.short_ma, self.long_ma):
            if not self.position:
                self.buy()
                self.entry_price = price
        
        # Exit: Take profit or stop loss
        elif self.position and self.entry_price:
            pnl_pct = (price - self.entry_price) / self.entry_price
            
            if pnl_pct >= self.take_profit_pct or pnl_pct <= -self.stop_loss_pct:
                self.position.close()
                self.entry_price = None

if __name__ == "__main__":
    # Download historical data
    data = yf.download('AAPL', period='1y', interval='1d', progress=False)
    
    # Flatten column index if MultiIndex (yfinance issue with single ticker)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Run backtest
    bt = Backtest(data, ScalpingStrategy, cash=10000, commission=0.002)
    stats = bt.run()
    
    # Print metrics in parseable format
    print(f"Return [Avg]: {stats['Return [%]']:.2f}%")
    print(f"Sharpe Ratio: {stats.get('Sharpe Ratio', 0):.2f}")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate: {stats.get('Win Rate [%]', 0):.2f}%")
    print(f"Total Trades: {stats['# Trades']}")
'''
        
        template, created = StrategyTemplate.objects.update_or_create(
            name='System Scalping Strategy',
            defaults={
                'description': 'A short-term scalping strategy using moving average crossovers with tight profit targets',
                'category': 'scalping',
                'template_code': template_code,
                'is_system_template': True,
                'is_active': True,
                'latest_strategy_code': template_code,
                'parameters_schema': {
                    'keywords': 'scalping,short term,quick profit,moving average,crossover,day trading,intraday,sma'
                }
            }
        )
        
        return template, created
    
    def handle(self, *args, **options):
        """Main command execution"""
        self.stdout.write("Creating system templates...")
        self.stdout.write("-" * 60)
        
        templates = [
            ('Momentum', self.create_momentum_template),
            ('Mean Reversion', self.create_mean_reversion_template),
            ('Breakout', self.create_breakout_template),
            ('Scalping', self.create_scalping_template),
        ]
        
        created_count = 0
        updated_count = 0
        
        for name, func in templates:
            template, created = func()
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Created: {name} template"))
            else:
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Updated: {name} template"))
        
        self.stdout.write("-" * 60)
        self.stdout.write(self.style.SUCCESS(f"\nSummary:"))
        self.stdout.write(f"  Created: {created_count} templates")
        self.stdout.write(f"  Updated: {updated_count} templates")
        
        total = StrategyTemplate.objects.filter(is_system_template=True).count()
        self.stdout.write(f"  Total system templates: {total}")
        self.stdout.write(self.style.SUCCESS("\nSystem templates are now available for fallback!"))
