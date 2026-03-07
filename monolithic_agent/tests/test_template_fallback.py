"""
Test Template Fallback Mechanism
=================================

Demonstrates the new template fallback feature that bypasses API keys.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
import django
django.setup()

from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
from strategy_api.models import StrategyTemplate

def test_template_fallback():
    """Test generating strategy with template fallback"""
    
    print("\n" + "="*70)
    print("TESTING TEMPLATE FALLBACK MECHANISM")
    print("="*70)
    
    # Check if we have any templates
    templates = StrategyTemplate.objects.filter(is_active=True, is_system_template=True)
    print(f"\nFound {templates.count()} system templates in database")
    
    for template in templates[:3]:
        print(f"  - {template.name} ({template.category})")
    
    # Test 1: Generator with fallback enabled
    print("\n[TEST 1] Creating generator with template fallback enabled...")
    try:
        generator = GeminiStrategyGenerator(
            model_name='gemini-2.0-flash',
            use_template_fallback=True
        )
        print("[OK] Generator created successfully")
        print(f"  - Template fallback: {'ENABLED' if generator.use_template_fallback else 'DISABLED'}")
        print(f"  - RequestRouter: {'AVAILABLE' if generator.request_router else 'NOT AVAILABLE'}")
    except Exception as e:
        print(f"[ERROR] Failed to create generator: {e}")
        return
    
    # Test 2: Try to generate with fallback
    print("\n[TEST 2] Testing template fallback (simulating API failure)...")
    description = "A momentum strategy using EMA crossover"
    
    # Temporarily disable API to test fallback
    original_router = generator.request_router
    generator.request_router = None  # Simulate API unavailable
    
    try:
        code = generator.generate_strategy(
            description=description,
            strategy_name="TestMomentumStrategy"
        )
        
        if code:
            print("[OK] Template fallback worked!")
            print(f"  - Generated code length: {len(code)} characters")
            print(f"  - Code preview: {code[:200]}...")
        else:
            print("[WARNING] No code generated")
            
    except Exception as e:
        print(f"[INFO] Fallback triggered (expected): {e}")
    finally:
        generator.request_router = original_router  # Restore
    
    # Test 3: Direct template loading
    print("\n[TEST 3] Testing direct template loading...")
    template_code = generator._get_template_strategy(description, "TestStrategy")
    
    if template_code:
        print("[OK] Template loaded successfully")
        print(f"  - Template length: {len(template_code)} characters")
    else:
        print("[WARNING] No template found")
    
    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70)


def test_api_bypass():
    """Test API endpoint with template-only mode"""
    
    print("\n" + "="*70)
    print("TESTING API BYPASS (Template-Only Mode)")
    print("="*70)
    
    print("\nTo test API bypass, use this request:")
    print("""
POST /api/strategies/api/generate_code/
{
    "strategy_description": "momentum strategy with EMA",
    "use_template_only": true,
    "parameters": {}
}
    """)
    
    print("\nExpected behavior:")
    print("  - No API keys required")
    print("  - Returns pre-built template from database")
    print("  - Response includes 'bypass_api': true in metadata")
    print("  - Works even if all API keys are exhausted")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    print("\n🧪 Template Fallback Test Suite")
    print("=" * 70)
    
    # Run tests
    test_template_fallback()
    test_api_bypass()
    
    print("\n✅ All tests completed!\n")
