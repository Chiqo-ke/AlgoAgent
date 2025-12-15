"""
List all available Gemini models.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Get a pro key
api_key = os.getenv('GEMINI_KEY_pro_01')
genai.configure(api_key=api_key)

print("Available models:")
print("=" * 80)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"\n✓ {model.name}")
        print(f"  Display name: {model.display_name}")
        print(f"  Supported methods: {model.supported_generation_methods}")
