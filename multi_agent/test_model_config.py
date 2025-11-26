"""
Quick test script to verify model configuration and workload selection.
"""
import sys
import os
from pathlib import Path

# Add multi_agent to path
sys.path.insert(0, str(Path(__file__).parent))

def test_key_loading():
    """Test that keys load correctly with valid model names."""
    print("=" * 60)
    print("TEST 1: Key Loading")
    print("=" * 60)
    
    try:
        from keys.manager import get_key_manager, reset_key_manager
        
        # Reset to ensure fresh load
        reset_key_manager()
        
        # Get manager (will load keys.json)
        km = get_key_manager()
        
        print(f"✅ Loaded {len(km.keys)} keys")
        print()
        
        # Show key details
        for key in km.keys.values():
            workload = key.tags.get('workload', 'none')
            priority = key.tags.get('priority', 'N/A')
            print(f"  • {key.key_id}")
            print(f"    Model: {key.model_name}")
            print(f"    Workload: {workload}")
            print(f"    Priority: {priority}")
            print(f"    Limits: {key.rpm} RPM, {key.tpm} TPM")
            print()
        
        # Verify no "any" models
        any_models = [k for k in km.keys.values() if k.model_name == "any"]
        if any_models:
            print(f"❌ ERROR: Found {len(any_models)} keys with invalid 'any' model")
            return False
        else:
            print("✅ No invalid 'any' model names found")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workload_selection():
    """Test workload-based key selection."""
    print("\n" + "=" * 60)
    print("TEST 2: Workload Selection")
    print("=" * 60)
    
    try:
        from keys.manager import get_key_manager
        
        km = get_key_manager()
        
        # Test each workload type
        workloads = ["light", "medium", "heavy"]
        
        for workload in workloads:
            print(f"\nTesting workload='{workload}':")
            
            # Try to select key (won't actually reserve since Redis might not be running)
            candidates = [
                k for k in km.keys.values()
                if k.tags.get('workload') == workload
            ]
            
            if candidates:
                print(f"  ✅ Found {len(candidates)} key(s):")
                for key in candidates:
                    print(f"     - {key.key_id} ({key.model_name})")
            else:
                print(f"  ⚠️  No keys with workload='{workload}'")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_safety_settings():
    """Test that safety settings are properly configured."""
    print("\n" + "=" * 60)
    print("TEST 3: Safety Settings")
    print("=" * 60)
    
    try:
        from llm.providers import GeminiClient
        
        print("Verifying GeminiClient safety settings...")
        
        # Check if safety_settings are in the code
        import inspect
        source = inspect.getsource(GeminiClient.chat_completion)
        
        if "BLOCK_NONE" in source:
            print("✅ Safety filters configured to BLOCK_NONE")
            
            # Count how many categories
            count = source.count("BLOCK_NONE")
            print(f"✅ {count} safety categories set to BLOCK_NONE")
        else:
            print("❌ ERROR: Safety filters not properly configured")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_names():
    """Verify all model names are valid Gemini models."""
    print("\n" + "=" * 60)
    print("TEST 4: Model Name Validation")
    print("=" * 60)
    
    try:
        from keys.manager import get_key_manager
        
        km = get_key_manager()
        
        valid_models = [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-exp-1206",
            "gemini-pro"
        ]
        
        print(f"Valid Gemini models: {', '.join(valid_models)}")
        print()
        
        all_valid = True
        for key in km.keys.values():
            if key.model_name in valid_models:
                print(f"✅ {key.key_id}: {key.model_name}")
            else:
                print(f"❌ {key.key_id}: {key.model_name} (INVALID)")
                all_valid = False
        
        if all_valid:
            print("\n✅ All model names are valid")
        else:
            print("\n❌ Some model names are invalid")
        
        return all_valid
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("GEMINI MODEL CONFIGURATION TEST")
    print("=" * 60)
    print()
    
    results = {
        "Key Loading": test_key_loading(),
        "Workload Selection": test_workload_selection(),
        "Safety Settings": test_safety_settings(),
        "Model Name Validation": test_model_names()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed!")
        print("\nYou can now use:")
        print("  • workload='light' for gemini-2.0-flash-exp")
        print("  • workload='medium' for gemini-1.5-pro")
        print("  • workload='heavy' for gemini-exp-1206")
        print("\nSafety filters are disabled for code generation.")
    else:
        print("\n⚠️  Some tests failed. Please review errors above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
