"""
Test if GeminiStrategyGenerator uses key rotation
"""
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("Testing GeminiStrategyGenerator Key Rotation")
print("="*70)

print(f"\n1. Environment Variables:")
print(f"   ENABLE_KEY_ROTATION: {os.getenv('ENABLE_KEY_ROTATION')}")
print(f"   REDIS_URL: {os.getenv('REDIS_URL')}")
print(f"   SECRET_STORE_TYPE: {os.getenv('SECRET_STORE_TYPE')}")

try:
    from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
    
    print(f"\n2. Initializing GeminiStrategyGenerator...")
    generator = GeminiStrategyGenerator()
    
    print(f"\n3. Key Rotation Status:")
    print(f"   use_key_rotation: {generator.use_key_rotation}")
    print(f"   selected_key_id: {generator.selected_key_id}")
    print(f"   key_manager available: {generator.key_manager is not None}")
    
    if generator.use_key_rotation and generator.key_manager:
        print(f"\n✅ SUCCESS: Key rotation is ENABLED and ACTIVE")
        print(f"   Using key: {generator.selected_key_id}")
    else:
        print(f"\n❌ WARNING: Key rotation is DISABLED")
        print(f"   Using single key: GEMINI_API_KEY")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
