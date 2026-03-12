"""
Test key selection with debug output
"""
import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "Backtest"))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import and configure logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

print("=" * 60)
print("KEY SELECTION TEST")
print("=" * 60)

from key_rotation import KeyManager

km = KeyManager()

print(f"\nKeys loaded: {len(km.keys)}")
print(f"Secrets loaded: {len(km.key_secrets)}")

print("\nKey Details:")
for key_id, metadata in km.keys.items():
    has_secret = key_id in km.key_secrets
    print(f"  {key_id}:")
    print(f"    Model: {metadata.model_name}")
    print(f"    Active: {metadata.active}")
    print(f"    Has Secret: {has_secret}")

print("\n" + "=" * 60)
print("TRYING TO SELECT KEY")
print("=" * 60)

# Test 1: Try with the requested model
print("\nTest 1: Requesting 'gemini-2.5-flash' (as GeminiStrategyGenerator does)")
result = km.select_key(model_preference='gemini-2.5-flash', tokens_needed=5000)
print(f"Result: {result}")

# Test 2: Try with available model
print("\nTest 2: Requesting 'gemini-2.0-flash' (actually in keys.json)")
result = km.select_key(model_preference='gemini-2.0-flash', tokens_needed=5000)
print(f"Result: {result}")

# Test 3: Try without model preference
print("\nTest 3: No model preference (should pick any)")
result = km.select_key(tokens_needed=5000)
print(f"Result: {result}")

print("\n" + "=" * 60)
