#!/usr/bin/env python
"""
Django Server Health Check Script
Checks if the Django server is running and accessible
"""

import requests
import sys

def check_server():
    base_url = "http://127.0.0.1:8000"
    
    print("🔍 Checking Django Server...")
    print(f"   Base URL: {base_url}")
    print("-" * 50)
    
    # Check if server is reachable
    try:
        response = requests.get(f"{base_url}/api/", timeout=5)
        print(f"✅ Server is reachable!")
        print(f"   Status Code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Server is NOT reachable!")
        print("   Make sure Django is running: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Check auth endpoints
    endpoints_to_check = [
        "/api/auth/login/",
        "/api/auth/register/",
        "/api/strategies/api/health/",
        "/api/data/api/health/",
        "/api/backtests/api/health/",
    ]
    
    print("\n📋 Checking Endpoints:")
    for endpoint in endpoints_to_check:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code < 500 else "⚠️"
            print(f"{status} {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    # Check CORS headers
    print("\n🌐 Checking CORS Configuration:")
    try:
        response = requests.options(
            f"{base_url}/api/auth/login/",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
            timeout=5
        )
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        if cors_header:
            print(f"✅ CORS Headers Present: {cors_header}")
        else:
            print("⚠️ No CORS headers found - might cause issues!")
    except Exception as e:
        print(f"❌ CORS check failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Server is running and accessible!")
    print("   You can now start your frontend.")
    return True

if __name__ == "__main__":
    if not check_server():
        sys.exit(1)
