"""
Test Bot Verification System
=============================

Test the bot verification and performance tracking system.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monolithic_agent.settings')
django.setup()

from strategy_api.bot_verification_service import BotVerificationService
from strategy_api.models import Strategy
from strategy_api.bot_performance import BotPerformance


def test_single_bot():
    """Test verification of a single bot (algo9999999888877)"""
    print("\n" + "="*80)
    print("TEST 1: Verify Single Bot (algo9999999888877)")
    print("="*80)
    
    # Find the strategy
    try:
        strategy = Strategy.objects.filter(name__icontains='9999999888877').first()
        
        if not strategy:
            print("❌ Strategy 'algo9999999888877' not found in database")
            print("Creating test strategy...")
            strategy = Strategy.objects.create(
                name='algo9999999888877',
                description='Test strategy with working trades',
                status='active'
            )
            print(f"✅ Created strategy: {strategy.name}")
        else:
            print(f"✅ Found strategy: {strategy.name} (ID: {strategy.id})")
        
        # Run verification
        service = BotVerificationService()
        performance = service.verify_strategy(strategy.id)
        
        if performance:
            print(f"\n✅ Verification Complete!")
            print(f"   Status: {performance.verification_status}")
            print(f"   Verified: {performance.is_verified}")
            print(f"   Total Trades: {performance.total_trades}")
            print(f"   Return: {performance.total_return}%")
            print(f"   Win Rate: {performance.win_rate}%")
            print(f"   Notes: {performance.verification_notes}")
            
            badge = performance.get_verification_badge()
            print(f"\n   Badge: {badge['icon']} {badge['label']}")
            print(f"   Description: {badge['description']}")
        else:
            print("❌ Verification failed - no performance data returned")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_list_verified_bots():
    """Test listing all verified bots"""
    print("\n" + "="*80)
    print("TEST 2: List All Verified Bots")
    print("="*80)
    
    try:
        service = BotVerificationService()
        verified_bots = service.get_verified_bots()
        
        print(f"\n✅ Found {verified_bots.count()} verified bots:\n")
        
        for i, performance in enumerate(verified_bots, 1):
            print(f"{i}. {performance.strategy.name}")
            print(f"   Trades: {performance.total_trades}")
            print(f"   Return: {performance.total_return}%")
            print(f"   Win Rate: {performance.win_rate}%")
            print(f"   Verified: {performance.verified_at}")
            print()
        
        if verified_bots.count() == 0:
            print("⚠️  No verified bots found. Run test_single_bot() first.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_bulk_verification():
    """Test bulk verification of all active strategies"""
    print("\n" + "="*80)
    print("TEST 3: Bulk Verification")
    print("="*80)
    
    try:
        active_strategies = Strategy.objects.filter(status='active')
        print(f"Found {active_strategies.count()} active strategies")
        
        if active_strategies.count() == 0:
            print("⚠️  No active strategies found")
            return
        
        service = BotVerificationService()
        results = service.verify_all_bots(force_retest=False)
        
        print(f"\n✅ Bulk Verification Complete!")
        print(f"   Total: {results['total']}")
        print(f"   ✅ Verified: {results['verified']}")
        print(f"   ⏳ Testing: {results['testing']}")
        print(f"   ❌ Failed: {results['failed']}")
        
        if results['errors']:
            print(f"\n⚠️  Errors:")
            for error in results['errors']:
                print(f"   - {error}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_performance_tracking():
    """Test performance tracking features"""
    print("\n" + "="*80)
    print("TEST 4: Performance Tracking")
    print("="*80)
    
    try:
        all_performance = BotPerformance.objects.all().select_related('strategy')
        
        print(f"\n📊 Performance Tracking Summary:")
        print(f"   Total tracked bots: {all_performance.count()}")
        
        by_status = {}
        for perf in all_performance:
            status = perf.verification_status
            by_status[status] = by_status.get(status, 0) + 1
        
        print(f"\n   By Status:")
        for status, count in by_status.items():
            print(f"      {status}: {count}")
        
        # Show top performers
        top_performers = all_performance.filter(
            is_verified=True
        ).order_by('-total_return')[:5]
        
        if top_performers:
            print(f"\n   🏆 Top 5 Performers:")
            for i, perf in enumerate(top_performers, 1):
                print(f"      {i}. {perf.strategy.name}")
                print(f"         Return: {perf.total_return}% | "
                      f"Trades: {perf.total_trades} | "
                      f"Win Rate: {perf.win_rate}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\n🤖 BOT VERIFICATION SYSTEM - TEST SUITE")
    print("="*80)
    
    # Run all tests
    test_single_bot()
    test_list_verified_bots()
    # test_bulk_verification()  # Uncomment when ready to test all bots
    test_performance_tracking()
    
    print("\n" + "="*80)
    print("✅ All Tests Complete!")
    print("="*80 + "\n")
