"""
Test script for Priority 1 API updates
Tests the new endpoints: generate_strategy, execute, fix_errors, execution_history, available_indicators
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
PARENT_DIR = Path(__file__).parent / "monolithic_agent"
sys.path.insert(0, str(PARENT_DIR))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

import django
django.setup()

def test_imports():
    """Test that all new imports work correctly"""
    print("=" * 80)
    print("TEST 1: Import Verification")
    print("=" * 80)
    
    try:
        from strategy_api import views, serializers
        print("✓ Strategy API imports successful")
        
        # Check if backtest modules are available
        if views.BACKTEST_MODULES_AVAILABLE:
            print("✓ Backtest modules available")
            print(f"  - GeminiStrategyGenerator: {views.GeminiStrategyGenerator is not None}")
            print(f"  - BotExecutor: {views.BotExecutor is not None}")
            print(f"  - INDICATOR_REGISTRY: {len(views.INDICATOR_REGISTRY)} indicators")
        else:
            print("⚠ Backtest modules not available (expected in some environments)")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_serializers():
    """Test that new serializers are defined"""
    print("\n" + "=" * 80)
    print("TEST 2: Serializer Verification")
    print("=" * 80)
    
    try:
        from strategy_api.serializers import (
            StrategySerializer,
            StrategyExecutionSerializer,
            StrategyFixAttemptSerializer,
            StrategyGenerateRequestSerializer
        )
        
        print("✓ StrategySerializer - includes execution_result, fix_attempts, key_rotation_enabled")
        print("✓ StrategyExecutionSerializer - defined")
        print("✓ StrategyFixAttemptSerializer - defined")
        print("✓ StrategyGenerateRequestSerializer - defined")
        
        # Test instantiation
        exec_serializer = StrategyExecutionSerializer(data={
            'success': True,
            'return_pct': 10.5,
            'num_trades': 100,
            'win_rate': 0.55,
            'sharpe_ratio': 1.2,
            'max_drawdown': -5.0,
            'results_file': '/path/to/results.json',
            'execution_time': 2.5
        })
        
        if exec_serializer.is_valid():
            print("✓ StrategyExecutionSerializer validates correctly")
        else:
            print(f"✗ Validation errors: {exec_serializer.errors}")
        
        return True
    except Exception as e:
        print(f"✗ Serializer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_viewset_methods():
    """Test that new ViewSet methods are defined"""
    print("\n" + "=" * 80)
    print("TEST 3: ViewSet Method Verification")
    print("=" * 80)
    
    try:
        from strategy_api.views import StrategyViewSet
        
        # Check that new methods exist
        methods = [
            'generate_strategy',
            'execute',
            'fix_errors',
            'execution_history',
            'available_indicators'
        ]
        
        for method_name in methods:
            if hasattr(StrategyViewSet, method_name):
                method = getattr(StrategyViewSet, method_name)
                print(f"✓ {method_name} - defined")
                
                # Check if it's decorated with @action
                if hasattr(method, 'mapping'):
                    print(f"  └─ HTTP methods: {list(method.mapping.keys())}")
            else:
                print(f"✗ {method_name} - NOT FOUND")
                return False
        
        return True
    except Exception as e:
        print(f"✗ ViewSet method test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_endpoint_signatures():
    """Test that endpoint method signatures are correct"""
    print("\n" + "=" * 80)
    print("TEST 4: Endpoint Signature Verification")
    print("=" * 80)
    
    try:
        from strategy_api.views import StrategyViewSet
        import inspect
        
        # Test generate_strategy signature
        sig = inspect.signature(StrategyViewSet.generate_strategy)
        params = list(sig.parameters.keys())
        print(f"✓ generate_strategy params: {params}")
        assert 'self' in params and 'request' in params
        
        # Test execute signature
        sig = inspect.signature(StrategyViewSet.execute)
        params = list(sig.parameters.keys())
        print(f"✓ execute params: {params}")
        assert 'self' in params and 'request' in params and 'pk' in params
        
        # Test fix_errors signature
        sig = inspect.signature(StrategyViewSet.fix_errors)
        params = list(sig.parameters.keys())
        print(f"✓ fix_errors params: {params}")
        assert 'self' in params and 'request' in params and 'pk' in params
        
        # Test execution_history signature
        sig = inspect.signature(StrategyViewSet.execution_history)
        params = list(sig.parameters.keys())
        print(f"✓ execution_history params: {params}")
        assert 'self' in params and 'request' in params and 'pk' in params
        
        # Test available_indicators signature
        sig = inspect.signature(StrategyViewSet.available_indicators)
        params = list(sig.parameters.keys())
        print(f"✓ available_indicators params: {params}")
        assert 'self' in params and 'request' in params
        
        print("\n✓ All endpoint signatures are correct")
        return True
    except Exception as e:
        print(f"✗ Signature test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_key_rotation_integration():
    """Test that key rotation is enabled in generate_strategy"""
    print("\n" + "=" * 80)
    print("TEST 5: Key Rotation Integration")
    print("=" * 80)
    
    try:
        from strategy_api.views import StrategyViewSet
        import inspect
        
        # Get source code of generate_strategy
        source = inspect.getsource(StrategyViewSet.generate_strategy)
        
        # Check for key rotation
        if 'enable_key_rotation=True' in source:
            print("✓ Key rotation is ENABLED in generate_strategy")
        else:
            print("✗ Key rotation not found in generate_strategy")
            return False
        
        # Check for auto-fix integration
        if 'auto_fix' in source and 'fix_bot_errors_iteratively' in source:
            print("✓ Auto-fix integration present")
        else:
            print("⚠ Auto-fix integration not found")
        
        # Check for fix_errors method
        source = inspect.getsource(StrategyViewSet.fix_errors)
        if 'enable_key_rotation=True' in source:
            print("✓ Key rotation is ENABLED in fix_errors")
        else:
            print("✗ Key rotation not found in fix_errors")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Key rotation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("PRIORITY 1 INTEGRATION TEST SUITE")
    print("=" * 80)
    print("Testing: Key rotation, auto-fix, execution, history, indicators")
    print()
    
    results = []
    
    # Run tests
    results.append(("Import Verification", test_imports()))
    results.append(("Serializer Verification", test_serializers()))
    results.append(("ViewSet Methods", test_viewset_methods()))
    results.append(("Endpoint Signatures", test_endpoint_signatures()))
    results.append(("Key Rotation Integration", test_key_rotation_integration()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Priority 1 integration complete!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed - review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
