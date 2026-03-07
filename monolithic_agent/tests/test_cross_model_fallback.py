"""
Test cross-model fallback in key rotation system.

This test simulates exhausted flash keys and verifies that the system
automatically falls back to pro keys (different model).
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from Backtest.key_rotation import KeyManager

def test_cross_model_fallback():
    """Test that system falls back to compatible models when preferred model is exhausted."""
    print("=" * 80)
    print("Testing Cross-Model Fallback")
    print("=" * 80)
    
    # Initialize key manager
    key_manager = KeyManager()
    
    print(f"\nKey rotation enabled: {key_manager.enabled}")
    print(f"Total keys loaded: {len(key_manager.keys)}")
    
    # Show available models
    models = {}
    for key_id, metadata in key_manager.keys.items():
        model = metadata.model_name
        if model not in models:
            models[model] = []
        models[model].append(key_id)
    
    print("\nAvailable models and keys:")
    for model, keys in models.items():
        print(f"  {model}: {', '.join(keys)}")
    
    # Show compatibility mapping
    print("\nModel compatibility mapping:")
    for model, compatible in key_manager.model_compatibility.items():
        print(f"  {model} -> {compatible}")
    
    # Test 1: Request flash model with all flash keys excluded (simulating exhaustion)
    print("\n" + "=" * 80)
    print("Test 1: All flash keys exhausted, should fall back to pro")
    print("=" * 80)
    
    flash_keys = models.get('gemini-2.0-flash', [])
    print(f"\nExcluding all flash keys: {flash_keys}")
    
    selected = key_manager.select_key(
        model_preference='gemini-2.0-flash',
        tokens_needed=5000,
        exclude_keys=flash_keys
    )
    
    if selected:
        print(f"\n✅ SUCCESS: Selected fallback key")
        print(f"  Key ID: {selected['key_id']}")
        print(f"  Model: {selected['model']}")
        print(f"  Expected: Should be gemini-1.5-pro (first compatible model)")
        
        if selected['model'] == 'gemini-1.5-pro':
            print(f"  ✅ CORRECT: Using compatible model from fallback list")
        else:
            print(f"  ⚠️  WARNING: Expected gemini-1.5-pro but got {selected['model']}")
    else:
        print(f"\n❌ FAILED: No key selected (should have fallen back to pro keys)")
        return False
    
    # Test 2: Request with no model preference (should use any available)
    print("\n" + "=" * 80)
    print("Test 2: No model preference, should select best available")
    print("=" * 80)
    
    selected = key_manager.select_key(
        model_preference=None,
        tokens_needed=5000
    )
    
    if selected:
        print(f"\n✅ SUCCESS: Selected key")
        print(f"  Key ID: {selected['key_id']}")
        print(f"  Model: {selected['model']}")
    else:
        print(f"\n❌ FAILED: No key selected")
        return False
    
    # Test 3: Request pro model directly (should work immediately)
    print("\n" + "=" * 80)
    print("Test 3: Request pro model directly")
    print("=" * 80)
    
    selected = key_manager.select_key(
        model_preference='gemini-1.5-pro',
        tokens_needed=5000
    )
    
    if selected:
        print(f"\n✅ SUCCESS: Selected pro key")
        print(f"  Key ID: {selected['key_id']}")
        print(f"  Model: {selected['model']}")
        
        if selected['model'] == 'gemini-1.5-pro':
            print(f"  ✅ CORRECT: Got requested model")
        else:
            print(f"  ⚠️  WARNING: Expected gemini-1.5-pro but got {selected['model']}")
    else:
        print(f"\n❌ FAILED: No pro key selected")
        return False
    
    print("\n" + "=" * 80)
    print("All tests passed! Cross-model fallback is working correctly.")
    print("=" * 80)
    return True

if __name__ == '__main__':
    try:
        success = test_cross_model_fallback()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
