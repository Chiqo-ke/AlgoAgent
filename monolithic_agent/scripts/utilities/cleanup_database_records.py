"""
Database Cleanup Script

Removes strategy and backtest records from the Django database.
Preserves user accounts and other important data.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
django.setup()

from django.db import connection
from datetime import datetime


def get_table_counts():
    """Get record counts for key tables."""
    with connection.cursor() as cursor:
        tables_to_check = [
            'strategy_api_strategy',
            'strategy_api_strategyvalidation',
            'strategy_api_strategychatmessage',
            'strategy_api_strategychat',
            'strategy_api_latestbacktestresult',
            'strategy_api_strategytemplate',
            'backtest_api_backtestrun',
            'backtest_api_backtestresult',
            'backtest_api_backtestconfig',
            'backtest_api_trade',
        ]
        
        counts = {}
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                counts[table] = count
            except Exception as e:
                counts[table] = f"Error: {e}"
        
        return counts


def cleanup_database():
    """Clean up strategy and backtest records."""
    print("\n" + "=" * 60)
    print("🗄️  DATABASE CLEANUP")
    print("=" * 60)
    
    # Show current counts
    print("\n📊 Current record counts:")
    counts_before = get_table_counts()
    for table, count in counts_before.items():
        print(f"  {table}: {count}")
    
    print("\n🧹 Cleaning database records...")
    
    deleted_counts = {}
    
    # Disable foreign key constraints temporarily
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF")
    
    with connection.cursor() as cursor:
        # Delete in correct order to avoid FK constraints
        
        # 1. Delete strategy chat messages (references chats)
        try:
            cursor.execute("DELETE FROM strategy_api_strategychatmessage")
            deleted_counts['strategy_api_strategychatmessage'] = cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} strategy chat messages")
        except Exception as e:
            print(f"  ⚠️  Strategy chat messages: {e}")
        
        # 2. Delete strategy chats (references strategies)
        try:
            cursor.execute("DELETE FROM strategy_api_strategychat")
            deleted_counts['strategy_api_strategychat'] = cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} strategy chats")
        except Exception as e:
            print(f"  ⚠️  Strategy chats: {e}")
        
        # 3. Delete strategy validations
        try:
            cursor.execute("DELETE FROM strategy_api_strategyvalidation")
            deleted_counts['strategy_api_strategyvalidation'] = cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} strategy validations")
        except Exception as e:
            print(f"  ⚠️  Strategy validations: {e}")
        
        # 4. Delete latest backtest results
        try:
            cursor.execute("DELETE FROM strategy_api_latestbacktestresult")
            deleted_counts['strategy_api_latestbacktestresult'] = cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} latest backtest results")
        except Exception as e:
            print(f"  ⚠️  Latest backtest results: {e}")
        
        # 5. Delete backtest trades
        try:
            cursor.execute("DELETE FROM backtest_api_trade")
            deleted_counts['backtest_api_trade'] = cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} backtest trades")
        except Exception as e:
            print(f"  ⚠️  Backtest trades: {e}")
        
        # 6. Delete backtest results
        try:
            cursor.execute("DELETE FROM backtest_api_backtestresult")
            deleted_counts['backtest_api_backtestresult'] = cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} backtest results")
        except Exception as e:
            print(f"  ⚠️  Backtest results: {e}")
        
        # 7. Delete backtest runs
        try:
            cursor.execute("DELETE FROM backtest_api_backtestrun")
            deleted_counts['backtest_api_backtestrun'] = cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} backtest runs")
        except Exception as e:
            print(f"  ⚠️  Backtest runs: {e}")
        
        # 8. Delete backtest configs
        try:
            cursor.execute("DELETE FROM backtest_api_backtestconfig")
            deleted_counts['backtest_api_backtestconfig'] = cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} backtest configs")
        except Exception as e:
            print(f"  ⚠️  Backtest configs: {e}")
        
        # 9. Delete strategy templates (user-generated)
        try:
            cursor.execute("DELETE FROM strategy_api_strategytemplate")
            deleted_counts['strategy_api_strategytemplate'] = cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} strategy templates")
        except Exception as e:
            print(f"  ⚠️  Strategy templates: {e}")
        
        # 10. Finally delete strategies
        try:
            cursor.execute("DELETE FROM strategy_api_strategy")
            deleted_counts['strategy_api_strategy'] = cursor.rowcount
            print(f"  ✓ Deleted {cursor.rowcount} strategies")
        except Exception as e:
            print(f"  ❌ Error deleting strategies: {e}")
    
    # Re-enable foreign key constraints
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = ON")
    
    # Show final counts
    print("\n📊 Final record counts:")
    counts_after = get_table_counts()
    for table, count in counts_after.items():
        print(f"  {table}: {count}")
    
    print("\n" + "=" * 60)
    print("✅ DATABASE CLEANUP COMPLETE!")
    print("=" * 60)
    print(f"\n📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Summary
    print("\n📋 Summary:")
    total_deleted = sum(v for v in deleted_counts.values() if isinstance(v, int))
    print(f"  Total records deleted: {total_deleted}")
    print("\n💾 Preserved:")
    print("  • User accounts")
    print("  • Authentication data")
    print("  • System configuration")
    print("=" * 60)


if __name__ == '__main__':
    print("\n⚠️  This will delete all strategy and backtest records from the database.")
    print("User accounts and system data will be preserved.")
    response = input("\nContinue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        cleanup_database()
    else:
        print("❌ Database cleanup cancelled.")
