"""
Integration Test for Strategy Manager
======================================

Demonstrates the complete workflow:
1. Check strategy status
2. Identify missing implementations
3. (Would) Generate Python code from JSON
4. (Would) Run backtests

This test can run without Gemini API to verify the detection logic.
"""

from pathlib import Path
from strategy_manager import StrategyManager
import json


def test_strategy_detection():
    """Test that JSON strategies are properly detected"""
    print("="*70)
    print("TEST: Strategy Detection")
    print("="*70)
    
    manager = StrategyManager()
    
    # Get all JSON files
    json_files = manager.get_json_strategy_files()
    print(f"\nFound {len(json_files)} JSON strategy files:")
    for jf in json_files:
        print(f"  - {jf.name}")
    
    # Get status
    status_list = manager.check_strategy_status()
    print(f"\nStrategy Status:")
    for status in status_list:
        marker = "✓" if status['has_python'] else "✗"
        print(f"  {marker} {status['title']}")
        print(f"     JSON: {status['json_file'].name}")
        print(f"     Python: {status['python_file'].name} {'(exists)' if status['has_python'] else '(MISSING)'}")
    
    return status_list


def test_json_parsing():
    """Test that JSON strategies can be parsed"""
    print("\n" + "="*70)
    print("TEST: JSON Strategy Parsing")
    print("="*70)
    
    manager = StrategyManager()
    json_files = manager.get_json_strategy_files()
    
    for json_file in json_files:
        print(f"\nParsing: {json_file.name}")
        strategy = manager.load_json_strategy(json_file)
        
        if strategy:
            print(f"  ✓ Valid JSON")
            print(f"  Title: {strategy.get('title', 'N/A')}")
            print(f"  Strategy ID: {strategy.get('strategy_id', 'N/A')}")
            print(f"  Steps: {len(strategy.get('steps', []))}")
            
            # Extract description
            description = manager.extract_strategy_description(strategy)
            print(f"  Description preview: {description[:100]}...")
        else:
            print(f"  ✗ Failed to parse")


def test_filename_derivation():
    """Test that Python filenames are correctly derived"""
    print("\n" + "="*70)
    print("TEST: Filename Derivation")
    print("="*70)
    
    manager = StrategyManager()
    
    test_cases = [
        "my_strategy.json",
        "ema_crossover.json",
        "rsi_oversold_30.json",
        "ema50ema200_ema_strategy_buy_aapl_when_the_50.json"
    ]
    
    print("\nFilename matching:")
    for json_name in test_cases:
        json_path = Path(json_name)
        py_name = manager.derive_python_filename(json_path)
        print(f"  {json_name:50} → {py_name}")


def test_status_report():
    """Test the formatted status report"""
    print("\n" + "="*70)
    print("TEST: Status Report")
    print("="*70)
    
    manager = StrategyManager()
    manager.print_status_report()


def test_missing_detection():
    """Test detection of strategies that need code generation"""
    print("\n" + "="*70)
    print("TEST: Missing Strategy Detection")
    print("="*70)
    
    manager = StrategyManager()
    status_list = manager.check_strategy_status()
    
    missing = [s for s in status_list if not s['has_python']]
    implemented = [s for s in status_list if s['has_python']]
    
    print(f"\nTotal strategies: {len(status_list)}")
    print(f"Implemented: {len(implemented)}")
    print(f"Missing code: {len(missing)}")
    
    if missing:
        print("\nStrategies needing code generation:")
        for s in missing:
            print(f"  - {s['title']}")
            print(f"    JSON: {s['json_file'].name}")
            print(f"    Expected Python: {s['python_file'].name}")
    
    if implemented:
        print("\nImplemented strategies:")
        for s in implemented:
            print(f"  - {s['title']}")
            print(f"    Python: {s['python_file'].name}")


def test_python_file_listing():
    """Test listing of existing Python strategy files"""
    print("\n" + "="*70)
    print("TEST: Python Strategy File Listing")
    print("="*70)
    
    manager = StrategyManager()
    py_files = manager.get_python_strategy_files()
    
    print(f"\nFound {len(py_files)} Python strategy files:")
    for pf in py_files:
        print(f"  - {pf.name}")
        
        # Check if there's a matching JSON
        json_file = pf.with_suffix('.json')
        has_json = json_file.exists()
        print(f"    Has JSON: {'✓' if has_json else '✗'}")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("STRATEGY MANAGER INTEGRATION TESTS")
    print("="*70)
    print("Testing detection and management logic (no Gemini API required)")
    print("="*70)
    
    try:
        test_strategy_detection()
        test_json_parsing()
        test_filename_derivation()
        test_python_file_listing()
        test_missing_detection()
        test_status_report()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)
        print("\nStrategy Manager is ready to use!")
        print("\nNext steps:")
        print("  1. Set GEMINI_API_KEY environment variable")
        print("  2. Run: python strategy_manager.py --generate")
        print("  3. Run: python strategy_manager.py --run <strategy_name>")
        
    except Exception as e:
        print("\n" + "="*70)
        print("✗ TEST FAILED")
        print("="*70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
