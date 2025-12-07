"""
Test secret loading from environment
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("SECRET LOADING TEST")
print("=" * 60)

key_ids = ['flash_01', 'flash_02', 'flash_03', 'pro_01', 'pro_02', 'pro_03', 'pro_04', 'pro_05']

print("\nTrying different environment variable formats:")
for key_id in key_ids:
    print(f"\n{key_id}:")
    
    # Format 1: GEMINI_KEY_{key_id.replace('-', '_')}
    env_var_underscore = f"GEMINI_KEY_{key_id.replace('-', '_')}"
    val1 = os.getenv(env_var_underscore)
    print(f"  {env_var_underscore}: {val1[:20]}..." if val1 else f"  {env_var_underscore}: NOT FOUND")
    
    # Format 2: GEMINI_KEY_{key_id}
    env_var_hyphen = f"GEMINI_KEY_{key_id}"
    val2 = os.getenv(env_var_hyphen)
    print(f"  {env_var_hyphen}: {val2[:20]}..." if val2 else f"  {env_var_hyphen}: NOT FOUND")
    
    # Format 3: API_KEY_{key_id.replace('-', '_')}
    env_var_alt = f"API_KEY_{key_id.replace('-', '_')}"
    val3 = os.getenv(env_var_alt)
    print(f"  {env_var_alt}: {val3[:20]}..." if val3 else f"  {env_var_alt}: NOT FOUND")
    
    # What is actually found?
    secret = val1 or val2 or val3
    if secret:
        print(f"  ✓ Secret found: {secret[:20]}...")
    else:
        print(f"  ✗ NO SECRET FOUND")

print("\n" + "=" * 60)
