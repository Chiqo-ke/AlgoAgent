"""
Test BotPerformance API endpoint
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

print("=" * 60)
print("API ENDPOINT TEST: BotPerformance")
print("=" * 60)

# Test bot-performance endpoint
url = f"{API_BASE}/strategies/bot-performance/"
print(f"\n1. Testing GET {url}")

try:
    response = requests.get(url)
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Handle both paginated and non-paginated responses
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
            print(f"   ✓ Paginated response")
            print(f"   Total count: {data.get('count', 'N/A')}")
            print(f"   Results: {len(results)} records")
        elif isinstance(data, list):
            results = data
            print(f"   ✓ Direct list response")
        else:
            results = []
            print(f"   ⚠ Unexpected response format: {type(data)}")
    else:
        print(f"   ✗ Failed to fetch data: {response.text}")

except Exception as e:
    print(f"   ✗ Exception occurred: {str(e)}")

print("=" * 60)