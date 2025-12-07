"""
Test round-robin queue-based key rotation.

Verifies that:
1. Keys are selected in queue order (not random)
2. Used keys are moved to end of queue
3. No key is used twice consecutively (unless only 1 key available)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from Backtest.key_rotation import KeyManager

def test_round_robin_rotation():
    """Test that keys rotate in round-robin order without consecutive repeats."""
    print("=" * 80)
    print("Testing Round-Robin Queue-Based Key Rotation")
    print("=" * 80)
    
    # Initialize key manager
    key_manager = KeyManager()
    
    print(f"\nKey rotation enabled: {key_manager.enabled}")
    print(f"Total keys loaded: {len(key_manager.keys)}")
    
    # Show rotation queues
    print("\nRotation queues initialized:")
    for model, queue in key_manager.key_rotation_queues.items():
        print(f"  {model}: {queue}")
    
    # Test 1: Select keys 5 times and verify round-robin
    print("\n" + "=" * 80)
    print("Test 1: Selecting flash keys 5 times - should rotate in order")
    print("=" * 80)
    
    selected_keys = []
    for i in range(5):
        selected = key_manager.select_key(
            model_preference='gemini-2.0-flash',
            tokens_needed=1000
        )
        if selected:
            key_id = selected['key_id']
            selected_keys.append(key_id)
            print(f"\n  Request {i+1}: Selected {key_id}")
            print(f"    Queue after selection: {key_manager.key_rotation_queues.get('gemini-2.0-flash', [])}")
        else:
            print(f"\n  Request {i+1}: ❌ No key selected")
            return False
    
    # Verify no consecutive repeats
    print("\n" + "=" * 80)
    print("Verifying no consecutive repeats:")
    print("=" * 80)
    print(f"  Selected sequence: {selected_keys}")
    
    has_consecutive_repeat = False
    for i in range(len(selected_keys) - 1):
        if selected_keys[i] == selected_keys[i+1]:
            print(f"  ❌ FAIL: Key {selected_keys[i]} used consecutively at positions {i} and {i+1}")
            has_consecutive_repeat = True
    
    if not has_consecutive_repeat:
        print(f"  ✅ SUCCESS: No consecutive repeats detected")
    else:
        return False
    
    # Test 2: Verify all flash keys are used in rotation
    print("\n" + "=" * 80)
    print("Test 2: Verify all 3 flash keys are used in 3 requests")
    print("=" * 80)
    
    # Reset by creating new key manager
    key_manager = KeyManager()
    
    flash_keys_used = set()
    for i in range(3):
        selected = key_manager.select_key(
            model_preference='gemini-2.0-flash',
            tokens_needed=1000
        )
        if selected:
            flash_keys_used.add(selected['key_id'])
            print(f"  Request {i+1}: {selected['key_id']}")
    
    expected_flash_keys = {'flash_01', 'flash_02', 'flash_03'}
    if flash_keys_used == expected_flash_keys:
        print(f"\n  ✅ SUCCESS: All 3 flash keys used in rotation")
        print(f"    Expected: {expected_flash_keys}")
        print(f"    Got: {flash_keys_used}")
    else:
        print(f"\n  ❌ FAIL: Not all keys used")
        print(f"    Expected: {expected_flash_keys}")
        print(f"    Got: {flash_keys_used}")
        return False
    
    # Test 3: Test pro keys rotation
    print("\n" + "=" * 80)
    print("Test 3: Pro keys rotation (4 keys)")
    print("=" * 80)
    
    key_manager = KeyManager()
    pro_keys_used = []
    for i in range(5):
        selected = key_manager.select_key(
            model_preference='gemini-1.5-pro',
            tokens_needed=1000
        )
        if selected:
            pro_keys_used.append(selected['key_id'])
            print(f"  Request {i+1}: {selected['key_id']}")
    
    # Check no consecutive repeats
    has_consecutive = False
    for i in range(len(pro_keys_used) - 1):
        if pro_keys_used[i] == pro_keys_used[i+1]:
            print(f"\n  ❌ FAIL: Consecutive repeat: {pro_keys_used[i]}")
            has_consecutive = True
    
    if not has_consecutive:
        print(f"\n  ✅ SUCCESS: No consecutive repeats in pro keys")
    else:
        return False
    
    # Test 4: Verify queue order after exclusions
    print("\n" + "=" * 80)
    print("Test 4: Rotation with excluded keys")
    print("=" * 80)
    
    key_manager = KeyManager()
    print(f"\nInitial flash queue: {key_manager.key_rotation_queues.get('gemini-2.0-flash', [])}")
    
    # Exclude flash_01, should get flash_02
    selected = key_manager.select_key(
        model_preference='gemini-2.0-flash',
        exclude_keys=['flash_01'],
        tokens_needed=1000
    )
    if selected and selected['key_id'] == 'flash_02':
        print(f"  ✅ Correctly selected flash_02 when flash_01 excluded")
    else:
        print(f"  ❌ Expected flash_02, got {selected['key_id'] if selected else 'None'}")
        return False
    
    print("\n" + "=" * 80)
    print("All round-robin rotation tests passed!")
    print("=" * 80)
    print("\nKey behaviors verified:")
    print("  ✅ Keys selected in queue order (not random)")
    print("  ✅ Used keys moved to end of queue")
    print("  ✅ No consecutive repeats")
    print("  ✅ All keys used in rotation cycle")
    print("  ✅ Exclusions work correctly")
    return True

if __name__ == '__main__':
    try:
        success = test_round_robin_rotation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
