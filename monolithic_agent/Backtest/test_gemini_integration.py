"""
Test Gemini API Integration with SimBroker
===========================================

Verifies that:
1. Gemini API key is configured
2. Can connect to Gemini
3. Can generate strategy code
4. Generated code uses SimBroker API correctly

Run: python test_gemini_integration.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_environment():
    """Test that environment is configured"""
    print("=" * 60)
    print("TEST 1: Environment Configuration")
    print("=" * 60)
    
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("   Please set it in .env file or environment variables")
        return False
    
    # Mask API key for display
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
    print(f"✅ GEMINI_API_KEY found: {masked_key}")
    return True


def test_gemini_package():
    """Test that google-generativeai is installed"""
    print("\n" + "=" * 60)
    print("TEST 2: Google Generative AI Package")
    print("=" * 60)
    
    try:
        import google.generativeai as genai
        print(f"✅ google-generativeai installed")
        return True
    except ImportError:
        print("❌ google-generativeai not installed")
        print("   Run: pip install google-generativeai")
        return False


def test_gemini_connection():
    """Test connection to Gemini API"""
    print("\n" + "=" * 60)
    print("TEST 3: Gemini API Connection")
    print("=" * 60)
    
    try:
        from gemini_strategy_generator import GeminiStrategyGenerator
        
        generator = GeminiStrategyGenerator()
        print("✅ GeminiStrategyGenerator initialized")
        print(f"✅ Model: {generator.model.model_name}")
        return True
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_simple_generation():
    """Test generating a simple strategy"""
    print("\n" + "=" * 60)
    print("TEST 4: Generate Simple Strategy")
    print("=" * 60)
    
    try:
        from gemini_strategy_generator import GeminiStrategyGenerator
        
        generator = GeminiStrategyGenerator()
        
        print("Generating test strategy (this may take 10-30 seconds)...")
        print("Description: Buy when RSI < 30, sell when RSI > 70")
        
        code = generator.generate_strategy(
            description="Buy when RSI < 30, sell when RSI > 70",
            strategy_name="TestRSIStrategy"
        )
        
        print(f"\n✅ Strategy generated ({len(code)} characters)")
        
        # Show first few lines
        lines = code.split('\n')[:10]
        print("\nFirst 10 lines:")
        print("-" * 60)
        for line in lines:
            print(line)
        print("-" * 60)
        
        return True, code
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_validation(code: str):
    """Test validation of generated code"""
    print("\n" + "=" * 60)
    print("TEST 5: Validate Generated Code")
    print("=" * 60)
    
    try:
        from gemini_strategy_generator import GeminiStrategyGenerator
        
        generator = GeminiStrategyGenerator()
        validation = generator.validate_generated_code(code)
        
        print(f"Valid: {validation['valid']}")
        print(f"Has required imports: {validation['has_required_imports']}")
        print(f"Uses stable API: {validation['uses_stable_api']}")
        
        if validation['issues']:
            print("\nIssues found:")
            for issue in validation['issues']:
                print(f"  ❌ {issue}")
        else:
            print("\n✅ No issues found")
        
        if validation['warnings']:
            print("\nWarnings:")
            for warning in validation['warnings']:
                print(f"  ⚠️  {warning}")
        
        return validation['valid']
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


def test_save_strategy(code: str):
    """Test saving generated strategy"""
    print("\n" + "=" * 60)
    print("TEST 6: Save Strategy to File")
    print("=" * 60)
    
    try:
        output_file = Path(__file__).parent / "test_generated_strategy.py"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"✅ Strategy saved to: {output_file}")
        print(f"   File size: {output_file.stat().st_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Save failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("GEMINI API INTEGRATION TEST SUITE")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Environment
    results['environment'] = test_environment()
    if not results['environment']:
        print("\n⛔ Cannot proceed without API key")
        return
    
    # Test 2: Package
    results['package'] = test_gemini_package()
    if not results['package']:
        print("\n⛔ Cannot proceed without google-generativeai package")
        return
    
    # Test 3: Connection
    results['connection'] = test_gemini_connection()
    if not results['connection']:
        print("\n⛔ Cannot proceed without API connection")
        return
    
    # Test 4: Generation
    results['generation'], code = test_simple_generation()
    
    if results['generation'] and code:
        # Test 5: Validation
        results['validation'] = test_validation(code)
        
        # Test 6: Save
        results['save'] = test_save_strategy(code)
    else:
        results['validation'] = False
        results['save'] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name.upper()}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nGemini is successfully integrated with SimBroker!")
        print("\nNext steps:")
        print("1. Review generated strategy: test_generated_strategy.py")
        print("2. Generate your own strategies:")
        print("   python gemini_strategy_generator.py 'Your strategy description' -o my_strategy.py")
        print("3. Run the generated strategy:")
        print("   python my_strategy.py")
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        print("\nPlease fix the issues above before proceeding")
    
    print()


if __name__ == "__main__":
    main()
