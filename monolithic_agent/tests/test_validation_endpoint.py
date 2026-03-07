"""
Test the validate_strategy_with_ai endpoint with Copilot
"""
import os
import requests
import json

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

import django
django.setup()

def test_validation_endpoint():
    """Test strategy validation with Copilot AI insights"""
    
    url = "http://127.0.0.1:8000/api/strategies/api/validate_strategy_with_ai/"
    
    payload = {
        "strategy_text": "Create a simple RSI strategy with 14-period RSI, buy below 30, sell above 70. with take profit 40 pips from entry and stop loss 15 pips from entry",
        "input_type": "freetext",
        "use_gemini": False,  # Disable Gemini
        "ai_provider": "copilot",  # Use Copilot
        "strict_mode": False
    }
    
    print("=" * 60)
    print("Testing Strategy Validation with Copilot")
    print("=" * 60)
    print(f"\nEndpoint: {url}")
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    print("\nSending request...")
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ Validation successful!")
            print(f"\nStatus: {data.get('status')}")
            print(f"AI Provider: {data.get('ai_provider', 'N/A')}")
            print(f"Classification: {data.get('classification', {})}")
            print(f"Confidence: {data.get('confidence', 'N/A')}")
            
            # Check for AI insights
            if 'ai_insights' in data:
                print("\n📊 AI Insights:")
                print("-" * 60)
                print(data['ai_insights'][:500] + "..." if len(data['ai_insights']) > 500 else data['ai_insights'])
            else:
                print("\n⚠️  No AI insights in response")
            
            # Check canonical JSON
            if 'canonical_json' in data:
                print("\n📋 Canonical JSON generated: ✓")
            
            # Full response
            print("\n" + "=" * 60)
            print("Full Response:")
            print("=" * 60)
            print(json.dumps(data, indent=2, default=str)[:2000])
            
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_validation_endpoint()
