"""Test script to verify Gemini API key is valid."""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded .env from {env_path}")
else:
    print(f"❌ .env not found at {env_path}")

# Check for API keys
gemini_key = os.getenv('GEMINI_API_KEY')
google_key = os.getenv('GOOGLE_API_KEY')

print(f"\nAPI Keys found:")
print(f"  GEMINI_API_KEY: {'✓ Present' if gemini_key else '❌ Missing'}")
if gemini_key:
    print(f"    Length: {len(gemini_key)}")
    print(f"    Starts with: {gemini_key[:10]}...")
print(f"  GOOGLE_API_KEY: {'✓ Present' if google_key else '❌ Missing'}")
if google_key:
    print(f"    Length: {len(google_key)}")
    print(f"    Starts with: {google_key[:10]}...")

# Test the API key
print(f"\n{'='*60}")
print("Testing Gemini API key...")
print('='*60)

try:
    import google.generativeai as genai
    
    # Use whichever key is available
    test_key = gemini_key or google_key
    
    if not test_key:
        print("❌ No API key available to test")
    else:
        print(f"Configuring genai with key: {test_key[:10]}...")
        genai.configure(api_key=test_key)
        
        print("Creating model...")
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        print("Sending test prompt...")
        response = model.generate_content("Say 'Hello, API key is valid!' in one short sentence.")
        
        print(f"\n✅ SUCCESS! API Response:")
        print(f"   {response.text}")
        
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    print(f"\nError type: {type(e).__name__}")
