"""
Check quota status for all API keys.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

keys_to_test = {
    'flash_01': os.getenv('GEMINI_KEY_flash_01'),
    'flash_02': os.getenv('GEMINI_KEY_flash_02'),
    'flash_03': os.getenv('GEMINI_KEY_flash_03'),
    'pro_01': os.getenv('GEMINI_KEY_pro_01'),
    'pro_02': os.getenv('GEMINI_KEY_pro_02'),
    'pro_03': os.getenv('GEMINI_KEY_pro_03'),
    'pro_04': os.getenv('GEMINI_KEY_pro_04'),
}

print("=" * 80)
print("API KEY QUOTA STATUS CHECK")
print("=" * 80)

for key_id, api_key in keys_to_test.items():
    if not api_key:
        print(f"\n{key_id}: ❌ NOT CONFIGURED")
        continue
    
    print(f"\n{key_id} ({api_key[:10]}...):")
    genai.configure(api_key=api_key)
    
    # Try gemini-2.0-flash for flash keys
    model_name = 'gemini-2.0-flash' if 'flash' in key_id else 'gemini-2.5-pro'
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Test")
        print(f"  ✅ AVAILABLE - quota OK ({model_name})")
    except Exception as e:
        if '429' in str(e) and 'limit: 0' in str(e):
            print(f"  ❌ EXHAUSTED - quota limit: 0 ({model_name})")
        elif '429' in str(e):
            print(f"  ⚠️  RATE LIMITED - temporary ({model_name})")
        else:
            print(f"  ❌ ERROR: {str(e)[:100]}")

print("\n" + "=" * 80)
print("SUMMARY:")
print("If all keys show 'EXHAUSTED', quotas will reset at midnight PST.")
print("=" * 80)
