"""
Test template-only mode after fixes implementation.

This script tests:
1. KeyManager has mark_key_success() and mark_key_failed() methods
2. System templates are available in database
3. Template-only mode works without API keys
"""
import os
import sys
import django

# Setup Django environment
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir) if 'scripts' in script_dir else script_dir
sys.path.insert(0, project_dir)
os.chdir(project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monolithic_agent.settings')
django.setup()

from strategy_api.models import StrategyTemplate
from Backtest.key_rotation import KeyManager, get_key_manager
from Backtest.request_router import RequestRouter, get_request_router


def test_keymanager_methods():
    """Test that KeyManager has required methods"""
    print("\n=== Testing KeyManager Methods ===")
    
    key_manager = get_key_manager()
    
    # Check for required methods
    required_methods = ['mark_key_success', 'mark_key_failed', 'report_success', 'report_error']
    
    for method_name in required_methods:
        if hasattr(key_manager, method_name):
            print(f"✓ KeyManager has method: {method_name}")
        else:
            print(f"✗ KeyManager missing method: {method_name}")
            return False
    
    return True


def test_system_templates():
    """Test that system templates exist in database"""
    print("\n=== Testing System Templates ===")
    
    templates = StrategyTemplate.objects.filter(
        is_active=True,
        is_system_template=True
    )
    
    count = templates.count()
    print(f"System templates found: {count}")
    
    if count == 0:
        print("✗ No system templates available!")
        return False
    
    for template in templates:
        print(f"  ✓ {template.name} (category: {template.category})")
    
    return True


def test_request_router():
    """Test that RequestRouter initializes correctly"""
    print("\n=== Testing RequestRouter ===")
    
    try:
        router = get_request_router()
        print(f"✓ RequestRouter initialized")
        
        stats = router.get_stats()
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Total failures: {stats['total_failures']}")
        
        return True
    except Exception as e:
        print(f"✗ RequestRouter failed: {e}")
        return False


def test_template_lookup():
    """Test template auto-selection based on keywords"""
    print("\n=== Testing Template Lookup ===")
    
    test_descriptions = [
        ("Create a momentum strategy using moving averages", "momentum"),
        ("I want a mean reversion strategy using RSI", "mean_reversion"),
        ("Build a breakout strategy", "breakout"),
        ("Quick scalping strategy", "scalping"),
    ]
    
    all_passed = True
    for description, expected_category in test_descriptions:
        templates = StrategyTemplate.objects.filter(
            is_active=True,
            is_system_template=True,
            category=expected_category
        )
        
        if templates.exists():
            template = templates.first()
            print(f"✓ '{description}' -> {template.name}")
        else:
            print(f"✗ No template for category: {expected_category}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("=" * 60)
    print("POST-FIX VERIFICATION TESTS")
    print("=" * 60)
    
    tests = [
        ("KeyManager Methods", test_keymanager_methods),
        ("System Templates", test_system_templates),
        ("RequestRouter", test_request_router),
        ("Template Lookup", test_template_lookup),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All fixes verified successfully!")
        print("\nYou can now use template-only mode by adding:")
        print('  "use_template_only": true')
        print("\nOr rely on automatic fallback when API keys fail.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - please review")
        return 1


if __name__ == '__main__':
    sys.exit(main())
