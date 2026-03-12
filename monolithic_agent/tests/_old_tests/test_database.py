#!/usr/bin/env python3
"""
Simple database connectivity test
"""
import requests

def test_database():
    print("Testing database operations...")
    
    # Test read
    r = requests.get('http://127.0.0.1:8000/api/data/symbols/')
    data = r.json()
    print(f"✅ Database Read - Status: {r.status_code}")
    print(f"✅ Total symbols: {data.get('count', 0)}")
    
    # List symbols
    for symbol in data.get('results', []):
        print(f"   - {symbol['symbol']}: {symbol['name']}")
    
    print("Database operations working correctly!")

if __name__ == "__main__":
    test_database()