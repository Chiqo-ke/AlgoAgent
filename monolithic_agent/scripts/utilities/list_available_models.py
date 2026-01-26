
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Define the absolute path to the .env file
dotenv_path = r'c:\Users\nyaga\Documents\AlgoAgent\monolithic_agent\.env'
print(f"Loading .env file from: {dotenv_path}")

# Load environment variables from the specified .env file
load_dotenv(dotenv_path=dotenv_path)

# Use a specific key for the test to ensure we have one
api_key = os.getenv("API_KEY_flash_01") 

if not api_key:
    print("API key 'API_KEY_flash_01' not found in the .env file.")
    print("Please ensure the .env file is correctly formatted and the key exists.")
else:
    try:
        print("Configuring Gemini with the found API key...")
        genai.configure(api_key=api_key)

        print("\nFetching available models that support 'generateContent'...")
        
        found_models = False
        for m in genai.list_models():
          if 'generateContent' in m.supported_generation_methods:
            print(f"  - {m.name}")
            found_models = True
            
        if not found_models:
            print("No models supporting 'generateContent' were found for this API key.")

    except Exception as e:
        print(f"\nAn error occurred while trying to list models: {e}")
