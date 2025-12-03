"""
Test the Indicator Registry and verify the agent can access pre-built indicators
"""

import sys
import os
from pathlib import Path

# Add the monolithic_agent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from Backtest.indicator_registry import (
    INDICATOR_REGISTRY,
    get_available_indicators,
    get_indicator_info,
    get_indicator_import,
    format_registry_for_prompt
)


def test_indicator_registry():
    """Test that indicator registry is properly configured"""
    
    print("=" * 70)
    print("INDICATOR REGISTRY TEST")
    print("=" * 70)
    
    # Test 1: Check registry structure
    print("\n✓ Test 1: Registry Structure")
    assert len(INDICATOR_REGISTRY) > 0, "Registry is empty"
    print(f"  Registry contains {len(INDICATOR_REGISTRY)} indicators")
    
    # Test 2: Check available indicators
    print("\n✓ Test 2: Available Indicators")
    available = get_available_indicators()
    print(f"  Available: {', '.join(available)}")
    assert 'ema' in available, "EMA indicator not available"
    assert 'rsi' in available, "RSI indicator not available"
    assert 'sma' in available, "SMA indicator not available"
    
    # Test 3: Check indicator info
    print("\n✓ Test 3: Indicator Information")
    ema_info = get_indicator_info('ema')
    assert ema_info is not None, "EMA info not found"
    assert ema_info['name'] == 'Exponential Moving Average'
    assert ema_info['module'] == 'data_api.indicators'
    print(f"  EMA Info:")
    print(f"    - Name: {ema_info['name']}")
    print(f"    - Module: {ema_info['module']}")
    print(f"    - Function: {ema_info['function']}")
    
    # Test 4: Check import statements
    print("\n✓ Test 4: Import Statements")
    ema_import = get_indicator_import('ema')
    print(f"  EMA Import: {ema_import}")
    assert 'from data_api.indicators import' in ema_import
    
    # Test 5: Check examples
    print("\n✓ Test 5: Usage Examples")
    ema_example = get_indicator_info('ema')['example']
    print(f"  EMA Example: {ema_example}")
    assert 'self.I' in ema_example
    assert 'calculate_ema' in ema_example
    
    # Test 6: Check prompt formatting
    print("\n✓ Test 6: Prompt Formatting")
    prompt = format_registry_for_prompt()
    assert len(prompt) > 100, "Prompt is too short"
    assert 'EMA' in prompt
    assert 'RSI' in prompt
    assert 'available for use' in prompt
    print(f"  Formatted prompt length: {len(prompt)} characters")
    
    # Test 7: All indicators have required fields
    print("\n✓ Test 7: Indicator Completeness")
    required_fields = ['name', 'module', 'function', 'params', 'returns', 'import', 'example', 'available']
    for indicator_name, indicator_info in INDICATOR_REGISTRY.items():
        for field in required_fields:
            assert field in indicator_info, f"{indicator_name} missing {field}"
    print(f"  All {len(INDICATOR_REGISTRY)} indicators have required fields")
    
    # Test 8: Registry can be used to generate imports
    print("\n✓ Test 8: Dynamic Import Generation")
    indicators_to_use = ['ema', 'rsi', 'macd']
    imports = []
    for ind in indicators_to_use:
        import_stmt = get_indicator_import(ind)
        if import_stmt:
            imports.append(import_stmt)
    print(f"  Generated {len(imports)} import statements")
    assert len(imports) == 3
    for imp in imports:
        print(f"    {imp}")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
    
    print("\nIndicators Available to Agent:")
    for name in available:
        info = get_indicator_info(name)
        print(f"  • {info['name']} ({name})")
    
    return True


if __name__ == '__main__':
    try:
        test_indicator_registry()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
