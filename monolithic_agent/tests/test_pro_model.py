"""
Test if gemini-1.5-pro-latest model is accessible.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Get a pro key
api_key = os.getenv('GEMINI_KEY_pro_01')
if not api_key:
    print("❌ No GEMINI_KEY_pro_01 found in .env")
    exit(1)

print(f"✓ Found API key: {api_key[:10]}...")

# Configure genai
genai.configure(api_key=api_key)

# Try to create model
try:
    model = genai.GenerativeModel('gemini-2.5-pro')
    print(f"✓ Model 'gemini-2.5-pro' created successfully")
    
    # Try to generate content
    response = model.generate_content("Say 'Hello, this is a test' in exactly those words.")
    print(f"✓ Generation successful!")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
