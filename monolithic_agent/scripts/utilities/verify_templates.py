"""Quick script to verify template updates"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monolithic_agent.settings')
django.setup()

from strategy_api.models import StrategyTemplate

templates = StrategyTemplate.objects.filter(is_system_template=True)

print(f"\n{'='*60}")
print(f"Found {templates.count()} system templates")
print(f"{'='*60}\n")

for template in templates:
    print(f"\n--- {template.name} ---")
    code = template.template_code
    
    # Check for required components
    has_yfinance = 'import yfinance' in code
    has_backtest_import = 'from backtesting import' in code and 'Backtest' in code
    has_main_block = 'if __name__ == "__main__"' in code
    has_download = 'yf.download' in code
    has_bt_run = 'bt.run()' in code
    has_metrics = 'Return [Avg]:' in code
    
    print(f"  ✓ yfinance import: {has_yfinance}")
    print(f"  ✓ Backtest import: {has_backtest_import}")
    print(f"  ✓ __main__ block: {has_main_block}")
    print(f"  ✓ Data download: {has_download}")
    print(f"  ✓ bt.run() call: {has_bt_run}")
    print(f"  ✓ Metrics output: {has_metrics}")
    
    all_good = all([has_yfinance, has_backtest_import, has_main_block, 
                    has_download, has_bt_run, has_metrics])
    
    if all_good:
        print(f"  ✅ Template is COMPLETE")
    else:
        print(f"  ❌ Template is INCOMPLETE")
    
    # Show last 200 chars to verify execution block
    print(f"\n  Last 200 chars:")
    print(f"  {code[-200:]}")

print(f"\n{'='*60}\n")
