"""
Quick URL Check - Verify endpoints are accessible
"""
import requests

BASE_URL = "http://localhost:8000"

def check_endpoint(url, method="GET"):
    """Check if an endpoint exists"""
    try:
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json={})
        
        print(f"✓ {url} - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"✗ {url} - Error: {e}")
        return False

print("Checking AlgoAgent API Endpoints...\n")

# Check main endpoints
check_endpoint(f"{BASE_URL}/api/")
check_endpoint(f"{BASE_URL}/api/strategies/")
check_endpoint(f"{BASE_URL}/api/strategies/chat/")
check_endpoint(f"{BASE_URL}/api/strategies/templates/")
check_endpoint(f"{BASE_URL}/api/strategies/strategies/")

print("\nIf you see 200 or 405 (Method Not Allowed), the endpoints exist!")
print("404 means the endpoint is not found - check URL configuration.")
