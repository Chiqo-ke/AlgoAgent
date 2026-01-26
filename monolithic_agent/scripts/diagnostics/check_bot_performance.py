"""
Check BotPerformance data in database
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
django.setup()

from strategy_api.bot_performance import BotPerformance
from strategy_api.models import Strategy

print("=" * 60)
print("DATABASE CHECK: BotPerformance Table")
print("=" * 60)

# Check BotPerformance records
bot_count = BotPerformance.objects.count()
print(f"\n✓ Total BotPerformance records: {bot_count}")

if bot_count > 0:
    print("\nExisting BotPerformance Records:")
    print("-" * 60)
    for perf in BotPerformance.objects.all()[:10]:
        strategy_name = perf.strategy.name if perf.strategy else "N/A"
        print(f"  ID: {perf.id}")
        print(f"  Strategy: {strategy_name} (ID: {perf.strategy_id})")
        print(f"  Status: {perf.verification_status}")
        print(f"  Verified: {perf.is_verified}")
        print(f"  Total Trades: {perf.total_trades}")
        print(f"  Win Rate: {perf.win_rate}%")
        print(f"  Total Return: {perf.total_return}%")
        print(f"  Sharpe Ratio: {perf.sharpe_ratio}")
        print(f"  Max Drawdown: {perf.max_drawdown}%")
        print(f"  Updated: {perf.updated_at}")
        print("-" * 60)
else:
    print("\n⚠ No BotPerformance records found!")
    print("\nTo create test data, run a bot verification:")
    print("  python manage.py shell")
    print("  from strategy_api.bot_verification_service import BotVerificationService")
    print("  service = BotVerificationService()")
    print("  service.verify_strategy(strategy_id=<your_strategy_id>)")

# Check Strategy records
strategy_count = Strategy.objects.count()
print(f"\n✓ Total Strategy records: {strategy_count}")

if strategy_count > 0:
    print("\nStrategies that could have performance data:")
    print("-" * 60)
    for strat in Strategy.objects.all()[:5]:
        perf_count = strat.performance_history.count()
        print(f"  ID: {strat.id} | Name: {strat.name} | Performance records: {perf_count}")

print("\n" + "=" * 60)
