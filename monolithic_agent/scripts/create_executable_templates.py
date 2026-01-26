import os
import django
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monolithic_agent.settings')
django.setup()

from strategy_api.models import StrategyTemplate

EXECUTABLE_TEMPLATES = [
    {
        'name': 'System Momentum Strategy',
        'category': 'momentum',
        'description': 'EMA crossover momentum strategy',
        'strategy_code': '''from backtesting import Strategy
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
''',
        'is_system_template': True,
        'is_active': True
    },
    {
        'name': 'System Mean Reversion Strategy',
        'category': 'mean_reversion',
        'description': 'RSI-based mean reversion strategy',
        'strategy_code': '''from backtesting import Strategy
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
''',
        'is_system_template': True,
        'is_active': True
    }
]

for template_data in EXECUTABLE_TEMPLATES:
    template, created = StrategyTemplate.objects.update_or_create(
        name=template_data['name'],
        defaults=template_data
    )
    print(f"{'Created' if created else 'Updated'} executable template: {template.name}")

print(f"\n✓ Total executable templates: {StrategyTemplate.objects.filter(is_system_template=True).count()}")