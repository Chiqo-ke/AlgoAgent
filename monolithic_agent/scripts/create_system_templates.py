"""
Create system templates for strategy generation fallback.

This script populates the StrategyTemplate model with pre-built strategies
that can be used when API keys are unavailable or exhausted.
"""
import os
import sys
import django

# Setup Django environment - navigate to parent directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, project_dir)
os.chdir(project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monolithic_agent.settings')
django.setup()

from strategy_api.models import StrategyTemplate


def create_momentum_template():
    """Create momentum strategy template"""
    template_code = '''
import pandas as pd
import numpy as np
from datetime import datetime

def initialize(context):
    """Initialize the strategy"""
    context.lookback_period = 20
    context.position_size = 0.95
    
def handle_data(context, data):
    """Main strategy logic - Momentum strategy"""
    # Get price history
    prices = data.history(context.symbol, 'close', context.lookback_period + 1, '1d')
    
    if len(prices) < context.lookback_period:
        return
    
    # Calculate momentum (rate of change)
    momentum = (prices.iloc[-1] / prices.iloc[0]) - 1
    
    # Get current position
    current_position = context.portfolio.positions.get(context.symbol, 0)
    current_price = data.current(context.symbol, 'close')
    
    # Entry signal: Strong positive momentum
    if momentum > 0.05 and current_position == 0:
        # Calculate shares to buy
        cash = context.portfolio.cash
        shares = int((cash * context.position_size) / current_price)
        
        if shares > 0:
            context.order(context.symbol, shares)
            print(f"{data.current_dt}: BUY {shares} shares at ${current_price:.2f} (momentum: {momentum:.2%})")
    
    # Exit signal: Negative momentum or weak positive
    elif momentum < 0.02 and current_position > 0:
        context.order(context.symbol, -current_position)
        print(f"{data.current_dt}: SELL {current_position} shares at ${current_price:.2f} (momentum: {momentum:.2%})")

def analyze(context, perf):
    """Called at the end of each day"""
    pass
'''
    
    template, created = StrategyTemplate.objects.update_or_create(
        name='System Momentum Strategy',
        defaults={
            'description': 'A momentum-based trading strategy that buys on strong positive momentum and exits on weakness',
            'strategy_type': 'momentum',
            'code': template_code,
            'is_system_template': True,
            'is_active': True,
            'keywords': 'momentum,trend,rate of change,price momentum,uptrend,trend following'
        }
    )
    
    return template, created


def create_mean_reversion_template():
    """Create mean reversion strategy template"""
    template_code = '''
import pandas as pd
import numpy as np
from datetime import datetime

def initialize(context):
    """Initialize the strategy"""
    context.lookback_period = 20
    context.entry_threshold = 2.0  # Standard deviations
    context.exit_threshold = 0.5
    context.position_size = 0.95
    
def handle_data(context, data):
    """Main strategy logic - Mean Reversion strategy"""
    # Get price history
    prices = data.history(context.symbol, 'close', context.lookback_period + 1, '1d')
    
    if len(prices) < context.lookback_period:
        return
    
    # Calculate moving average and standard deviation
    mean_price = prices.mean()
    std_price = prices.std()
    current_price = data.current(context.symbol, 'close')
    
    # Calculate z-score (how many standard deviations from mean)
    z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
    
    # Get current position
    current_position = context.portfolio.positions.get(context.symbol, 0)
    
    # Entry signal: Price significantly below mean
    if z_score < -context.entry_threshold and current_position == 0:
        # Calculate shares to buy
        cash = context.portfolio.cash
        shares = int((cash * context.position_size) / current_price)
        
        if shares > 0:
            context.order(context.symbol, shares)
            print(f"{data.current_dt}: BUY {shares} shares at ${current_price:.2f} (z-score: {z_score:.2f})")
    
    # Exit signal: Price returned to near mean
    elif z_score > -context.exit_threshold and current_position > 0:
        context.order(context.symbol, -current_position)
        print(f"{data.current_dt}: SELL {current_position} shares at ${current_price:.2f} (z-score: {z_score:.2f})")

def analyze(context, perf):
    """Called at the end of each day"""
    pass
'''
    
    template, created = StrategyTemplate.objects.update_or_create(
        name='System Mean Reversion Strategy',
        defaults={
            'description': 'A mean reversion strategy that buys when price drops significantly below average and exits on reversion',
            'strategy_type': 'mean_reversion',
            'code': template_code,
            'is_system_template': True,
            'is_active': True,
            'keywords': 'mean reversion,oversold,overbought,bollinger,statistical arbitrage,reversion,oscillator'
        }
    )
    
    return template, created


def create_breakout_template():
    """Create breakout strategy template"""
    template_code = '''
import pandas as pd
import numpy as np
from datetime import datetime

def initialize(context):
    """Initialize the strategy"""
    context.lookback_period = 20
    context.breakout_threshold = 1.02  # 2% above high
    context.position_size = 0.95
    
def handle_data(context, data):
    """Main strategy logic - Breakout strategy"""
    # Get price history
    high_prices = data.history(context.symbol, 'high', context.lookback_period + 1, '1d')
    low_prices = data.history(context.symbol, 'low', context.lookback_period + 1, '1d')
    
    if len(high_prices) < context.lookback_period:
        return
    
    # Calculate resistance (highest high) and support (lowest low)
    resistance = high_prices[:-1].max()  # Exclude current bar
    support = low_prices[:-1].min()
    
    current_price = data.current(context.symbol, 'close')
    current_position = context.portfolio.positions.get(context.symbol, 0)
    
    # Entry signal: Breakout above resistance
    breakout_level = resistance * context.breakout_threshold
    if current_price > breakout_level and current_position == 0:
        # Calculate shares to buy
        cash = context.portfolio.cash
        shares = int((cash * context.position_size) / current_price)
        
        if shares > 0:
            context.order(context.symbol, shares)
            print(f"{data.current_dt}: BUY {shares} shares at ${current_price:.2f} (breakout above ${resistance:.2f})")
    
    # Exit signal: Price falls below support
    elif current_price < support and current_position > 0:
        context.order(context.symbol, -current_position)
        print(f"{data.current_dt}: SELL {current_position} shares at ${current_price:.2f} (broke support ${support:.2f})")

def analyze(context, perf):
    """Called at the end of each day"""
    pass
'''
    
    template, created = StrategyTemplate.objects.update_or_create(
        name='System Breakout Strategy',
        defaults={
            'description': 'A breakout strategy that enters on price breaking above resistance levels',
            'strategy_type': 'breakout',
            'code': template_code,
            'is_system_template': True,
            'is_active': True,
            'keywords': 'breakout,resistance,support,channel,range,volatility breakout,consolidation'
        }
    )
    
    return template, created


def create_scalping_template():
    """Create scalping strategy template"""
    template_code = '''
import pandas as pd
import numpy as np
from datetime import datetime

def initialize(context):
    """Initialize the strategy"""
    context.short_window = 5
    context.long_window = 20
    context.profit_target = 0.01  # 1% profit target
    context.stop_loss = 0.005  # 0.5% stop loss
    context.position_size = 0.95
    
def handle_data(context, data):
    """Main strategy logic - Scalping strategy"""
    # Get price history
    prices = data.history(context.symbol, 'close', context.long_window + 1, '1d')
    
    if len(prices) < context.long_window:
        return
    
    # Calculate short and long moving averages
    short_ma = prices.iloc[-context.short_window:].mean()
    long_ma = prices.mean()
    
    current_price = data.current(context.symbol, 'close')
    current_position = context.portfolio.positions.get(context.symbol, 0)
    
    # Entry signal: Short MA crosses above long MA
    if short_ma > long_ma and current_position == 0:
        # Calculate shares to buy
        cash = context.portfolio.cash
        shares = int((cash * context.position_size) / current_price)
        
        if shares > 0:
            context.order(context.symbol, shares)
            context.entry_price = current_price
            print(f"{data.current_dt}: BUY {shares} shares at ${current_price:.2f} (MA cross)")
    
    # Exit signals: Profit target or stop loss
    elif current_position > 0:
        profit_pct = (current_price - context.entry_price) / context.entry_price
        
        # Take profit
        if profit_pct >= context.profit_target:
            context.order(context.symbol, -current_position)
            print(f"{data.current_dt}: SELL {current_position} shares at ${current_price:.2f} (profit: {profit_pct:.2%})")
        
        # Stop loss
        elif profit_pct <= -context.stop_loss:
            context.order(context.symbol, -current_position)
            print(f"{data.current_dt}: SELL {current_position} shares at ${current_price:.2f} (stop loss: {profit_pct:.2%})")

def analyze(context, perf):
    """Called at the end of each day"""
    pass
'''
    
    template, created = StrategyTemplate.objects.update_or_create(
        name='System Scalping Strategy',
        defaults={
            'description': 'A short-term scalping strategy using moving average crossovers with tight profit targets',
            'strategy_type': 'scalping',
            'code': template_code,
            'is_system_template': True,
            'is_active': True,
            'keywords': 'scalping,short term,quick profit,moving average,crossover,day trading,intraday'
        }
    )
    
    return template, created


def main():
    """Create all system templates"""
    print("Creating system templates...")
    print("-" * 60)
    
    templates = [
        ('Momentum', create_momentum_template),
        ('Mean Reversion', create_mean_reversion_template),
        ('Breakout', create_breakout_template),
        ('Scalping', create_scalping_template),
    ]
    
    created_count = 0
    updated_count = 0
    
    for name, func in templates:
        template, created = func()
        if created:
            created_count += 1
            print(f"✓ Created: {name} template")
        else:
            updated_count += 1
            print(f"✓ Updated: {name} template")
    
    print("-" * 60)
    print(f"\nSummary:")
    print(f"  Created: {created_count} templates")
    print(f"  Updated: {updated_count} templates")
    print(f"  Total system templates: {StrategyTemplate.objects.filter(is_system_template=True).count()}")
    print("\nSystem templates are now available for fallback!")


if __name__ == '__main__':
    main()
