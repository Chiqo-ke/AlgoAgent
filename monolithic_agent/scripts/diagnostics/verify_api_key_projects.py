"""
API Key Project Verification Script
====================================

This script tests if multiple API keys belong to the same Google Cloud project.
If they do, they share quotas and rotation won't help.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=" * 80)
print("API KEY PROJECT VERIFICATION")
print("=" * 80)
print()
print("Testing if your API keys belong to the SAME or DIFFERENT projects...")
print()

# Get all API keys
keys_to_test = {}

# From GEMINI_KEY_* variables
for key_name in os.environ:
    if key_name.startswith('GEMINI_KEY_'):
        key_id = key_name.replace('GEMINI_KEY_', '').lower()
        keys_to_test[key_id] = {
            'env_var': key_name,
            'api_key': os.getenv(key_name)
        }

print(f"Found {len(keys_to_test)} API keys to test")
print()

# Test each key by making a simple API call
# The project ID is embedded in the error response or can be inferred
project_map = {}

for key_id, key_info in list(keys_to_test.items())[:5]:  # Test first 5 keys
    api_key = key_info['api_key']
    print(f"Testing key: {key_id} ({api_key[:15]}...{api_key[-4:]})")
    
    try:
        # Make a simple API call to get quota/project info
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"  ✅ Key is valid ({len(models)} models accessible)")
            
            # Try to infer project from response headers or model names
            # Google API responses sometimes include project hints
            project_hint = None
            if 'x-goog-api-key' in response.headers:
                project_hint = response.headers.get('x-goog-api-key')
            
            project_map[key_id] = {
                'valid': True,
                'models': len(models),
                'project_hint': project_hint or 'unknown'
            }
            
        elif response.status_code == 429:
            print(f"  ⚠️  Key hit rate limit (429) - QUOTA EXHAUSTED")
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', '')
            
            # Extract project/model info from error
            if 'model:' in error_msg:
                model_part = error_msg.split('model:')[1].split(',')[0].strip()
                print(f"     Model: {model_part}")
            
            project_map[key_id] = {
                'valid': True,
                'rate_limited': True,
                'error': error_msg[:100]
            }
            
        else:
            print(f"  ❌ Error: {response.status_code}")
            error_data = response.json() if response.text else {}
            print(f"     {error_data.get('error', {}).get('message', response.text)[:100]}")
            
            project_map[key_id] = {
                'valid': False,
                'error': response.status_code
            }
            
    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:100]}")
        project_map[key_id] = {
            'valid': False,
            'error': str(e)[:100]
        }
    
    print()

print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print()

# Count valid keys
valid_keys = [k for k, v in project_map.items() if v.get('valid')]
rate_limited_keys = [k for k, v in project_map.items() if v.get('rate_limited')]

print(f"Valid keys: {len(valid_keys)}")
print(f"Rate-limited keys: {len(rate_limited_keys)}")
print()

if len(rate_limited_keys) >= 2:
    print("🔴 CRITICAL FINDING:")
    print()
    print(f"   {len(rate_limited_keys)} out of {len(keys_to_test)} tested keys are RATE LIMITED")
    print()
    print("   This strongly suggests all keys belong to the SAME Google Cloud Project!")
    print()
    print("   When multiple keys from the same project hit 429 errors simultaneously,")
    print("   it means they're sharing the same quota pool.")
    print()
    print("   SOLUTION: You need API keys from DIFFERENT Google Cloud projects.")
    print()
    print("   How to create keys in different projects:")
    print("   1. Go to: https://console.cloud.google.com")
    print("   2. Create a NEW project (not the existing one)")
    print("   3. Enable Gemini API for that project")
    print("   4. Generate API key in that project")
    print("   5. Repeat for multiple projects")
    print("   6. Update .env with keys from different projects")
    print()
elif len(rate_limited_keys) == 1:
    print("⚠️  WARNING:")
    print()
    print(f"   1 key is rate limited, but others are working.")
    print("   This might indicate:")
    print("   - Keys are from different projects (GOOD)")
    print("   - OR one key was used more heavily than others")
    print()
    print("   Monitor if other keys start hitting 429 errors too.")
    print("   If they do, they're likely from the same project.")
    print()
else:
    print("✅ GOOD NEWS:")
    print()
    print("   No keys are currently rate limited.")
    print("   However, this doesn't guarantee they're from different projects.")
    print()
    print("   To verify:")
    print("   1. Go to: https://aistudio.google.com/apikey")
    print("   2. Check the project name for each API key")
    print("   3. If they show different project names, you're good!")
    print("   4. If they show the same project, you need keys from different projects")
    print()

print("=" * 80)
print("KEY DETAILS")
print("=" * 80)
print()
print(json.dumps(project_map, indent=2))
print()
