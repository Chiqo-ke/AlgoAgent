"""
Test Script for Ownership-Based Access Control
===============================================

This script tests the ownership-based access control implementation
to ensure users can only access their own resources.

Run this after the backend server is running:
    python test_ownership_access_control.py

Requirements:
    - Backend running on http://localhost:8000
    - requests library installed (pip install requests)
"""

import requests
import json
from typing import Dict, Optional

# Configuration
BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/api/auth"
STRATEGY_URL = f"{BASE_URL}/api/strategies"
BACKTEST_URL = f"{BASE_URL}/api/backtests"


class TestUser:
    """Helper class to manage test user authentication"""
    
    def __init__(self, username: str, email: str, password: str):
        self.username = username
        self.email = email
        self.password = password
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[int] = None
    
    def headers(self) -> Dict[str, str]:
        """Return headers with authentication"""
        if not self.access_token:
            raise ValueError(f"User {self.username} is not logged in")
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }


def register_user(user: TestUser) -> bool:
    """Register a new user"""
    print(f"\n📝 Registering user: {user.username}")
    
    response = requests.post(
        f"{AUTH_URL}/register/",
        json={
            "username": user.username,
            "email": user.email,
            "password": user.password,
            "first_name": "Test",
            "last_name": "User"
        }
    )
    
    if response.status_code == 201:
        data = response.json()
        user.access_token = data['tokens']['access']
        user.refresh_token = data['tokens']['refresh']
        user.user_id = data['user']['id']
        print(f"✅ User {user.username} registered successfully (ID: {user.user_id})")
        return True
    else:
        print(f"❌ Failed to register {user.username}: {response.text}")
        return False


def login_user(user: TestUser) -> bool:
    """Login existing user"""
    print(f"\n🔑 Logging in user: {user.username}")
    
    response = requests.post(
        f"{AUTH_URL}/login/",
        json={
            "username": user.username,
            "password": user.password
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        user.access_token = data['tokens']['access']
        user.refresh_token = data['tokens']['refresh']
        user.user_id = data['user']['id']
        print(f"✅ User {user.username} logged in successfully")
        return True
    else:
        print(f"❌ Failed to login {user.username}: {response.text}")
        return False


def create_strategy(user: TestUser, name: str) -> Optional[int]:
    """Create a strategy for a user"""
    print(f"\n📦 Creating strategy '{name}' for {user.username}")
    
    strategy_code = """
def initialize(context):
    context.symbol = "AAPL"

def handle_data(context, data):
    if data.can_trade(context.symbol):
        context.order_target_percent(context.symbol, 1.0)
"""
    
    response = requests.post(
        f"{STRATEGY_URL}/",
        headers=user.headers(),
        json={
            "name": name,
            "description": f"Test strategy created by {user.username}",
            "strategy_code": strategy_code,
            "parameters": {"symbol": "AAPL"},
            "status": "draft"
        }
    )
    
    if response.status_code == 201:
        data = response.json()
        strategy_id = data['id']
        print(f"✅ Strategy '{name}' created successfully (ID: {strategy_id})")
        return strategy_id
    else:
        print(f"❌ Failed to create strategy: {response.text}")
        return None


def list_strategies(user: TestUser) -> list:
    """List all strategies visible to user"""
    print(f"\n📋 Listing strategies for {user.username}")
    
    response = requests.get(
        f"{STRATEGY_URL}/",
        headers=user.headers()
    )
    
    if response.status_code == 200:
        strategies = response.json()
        print(f"✅ Found {len(strategies)} strategies")
        for strategy in strategies:
            print(f"   - {strategy['name']} (ID: {strategy['id']})")
        return strategies
    else:
        print(f"❌ Failed to list strategies: {response.text}")
        return []


def get_strategy(user: TestUser, strategy_id: int) -> Optional[Dict]:
    """Try to get a specific strategy"""
    print(f"\n🔍 {user.username} attempting to access strategy ID {strategy_id}")
    
    response = requests.get(
        f"{STRATEGY_URL}/{strategy_id}/",
        headers=user.headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Successfully accessed strategy: {data['name']}")
        return data
    elif response.status_code == 404:
        print(f"🚫 Strategy not found (expected for other users' strategies)")
        return None
    elif response.status_code == 403:
        print(f"🚫 Access forbidden (expected for other users' strategies)")
        return None
    else:
        print(f"❌ Unexpected error: {response.status_code} - {response.text}")
        return None


def update_strategy(user: TestUser, strategy_id: int, new_name: str) -> bool:
    """Try to update a strategy"""
    print(f"\n✏️  {user.username} attempting to update strategy ID {strategy_id}")
    
    response = requests.patch(
        f"{STRATEGY_URL}/{strategy_id}/",
        headers=user.headers(),
        json={"name": new_name}
    )
    
    if response.status_code == 200:
        print(f"✅ Successfully updated strategy to: {new_name}")
        return True
    elif response.status_code in [403, 404]:
        print(f"🚫 Update forbidden/not found (expected for other users' strategies)")
        return False
    else:
        print(f"❌ Unexpected error: {response.status_code} - {response.text}")
        return False


def delete_strategy(user: TestUser, strategy_id: int) -> bool:
    """Try to delete a strategy"""
    print(f"\n🗑️  {user.username} attempting to delete strategy ID {strategy_id}")
    
    response = requests.delete(
        f"{STRATEGY_URL}/{strategy_id}/",
        headers=user.headers()
    )
    
    if response.status_code == 204:
        print(f"✅ Successfully deleted strategy")
        return True
    elif response.status_code in [403, 404]:
        print(f"🚫 Delete forbidden/not found (expected for other users' strategies)")
        return False
    else:
        print(f"❌ Unexpected error: {response.status_code} - {response.text}")
        return False


def test_unauthenticated_access():
    """Test that unauthenticated requests are rejected"""
    print("\n" + "="*60)
    print("🔒 Testing unauthenticated access (should fail)")
    print("="*60)
    
    response = requests.get(f"{STRATEGY_URL}/")
    
    if response.status_code == 401:
        print("✅ Unauthenticated access correctly rejected")
        return True
    else:
        print(f"❌ Unexpected response for unauthenticated request: {response.status_code}")
        return False


def run_ownership_tests():
    """Run comprehensive ownership access control tests"""
    
    print("\n" + "="*60)
    print("🧪 OWNERSHIP-BASED ACCESS CONTROL TEST SUITE")
    print("="*60)
    
    # Create test users
    user_a = TestUser("test_user_a", "usera@test.com", "testpass123")
    user_b = TestUser("test_user_b", "userb@test.com", "testpass123")
    
    # Test 1: Unauthenticated access
    test_unauthenticated_access()
    
    # Test 2: Register users
    print("\n" + "="*60)
    print("👥 Test 2: User Registration")
    print("="*60)
    
    if not register_user(user_a):
        # Try logging in if already exists
        if not login_user(user_a):
            print("❌ Cannot proceed without User A")
            return
    
    if not register_user(user_b):
        # Try logging in if already exists
        if not login_user(user_b):
            print("❌ Cannot proceed without User B")
            return
    
    # Test 3: Create strategies
    print("\n" + "="*60)
    print("📦 Test 3: Strategy Creation")
    print("="*60)
    
    strategy_a1 = create_strategy(user_a, "User A Strategy 1")
    strategy_a2 = create_strategy(user_a, "User A Strategy 2")
    strategy_b1 = create_strategy(user_b, "User B Strategy 1")
    
    if not all([strategy_a1, strategy_a2, strategy_b1]):
        print("❌ Failed to create all strategies")
        return
    
    # Test 4: List strategies (isolation check)
    print("\n" + "="*60)
    print("📋 Test 4: Strategy List Isolation")
    print("="*60)
    
    strategies_a = list_strategies(user_a)
    strategies_b = list_strategies(user_b)
    
    # User A should see 2 strategies
    if len(strategies_a) == 2:
        print("✅ User A correctly sees only their 2 strategies")
    else:
        print(f"❌ User A should see 2 strategies, but sees {len(strategies_a)}")
    
    # User B should see 1 strategy
    if len(strategies_b) == 1:
        print("✅ User B correctly sees only their 1 strategy")
    else:
        print(f"❌ User B should see 1 strategy, but sees {len(strategies_b)}")
    
    # Test 5: Cross-user access (should fail)
    print("\n" + "="*60)
    print("🚫 Test 5: Cross-User Access Prevention")
    print("="*60)
    
    # User A trying to access User B's strategy
    result = get_strategy(user_a, strategy_b1)
    if result is None:
        print("✅ User A correctly cannot access User B's strategy")
    else:
        print("❌ SECURITY ISSUE: User A can access User B's strategy!")
    
    # User B trying to access User A's strategy
    result = get_strategy(user_b, strategy_a1)
    if result is None:
        print("✅ User B correctly cannot access User A's strategy")
    else:
        print("❌ SECURITY ISSUE: User B can access User A's strategy!")
    
    # Test 6: Own strategy access (should succeed)
    print("\n" + "="*60)
    print("✅ Test 6: Own Strategy Access")
    print("="*60)
    
    result = get_strategy(user_a, strategy_a1)
    if result is not None:
        print("✅ User A can access their own strategy")
    else:
        print("❌ User A cannot access their own strategy!")
    
    # Test 7: Cross-user modification (should fail)
    print("\n" + "="*60)
    print("🚫 Test 7: Cross-User Modification Prevention")
    print("="*60)
    
    # User A trying to update User B's strategy
    result = update_strategy(user_a, strategy_b1, "Hacked Strategy")
    if not result:
        print("✅ User A correctly cannot update User B's strategy")
    else:
        print("❌ SECURITY ISSUE: User A can update User B's strategy!")
    
    # Test 8: Own strategy modification (should succeed)
    print("\n" + "="*60)
    print("✏️  Test 8: Own Strategy Modification")
    print("="*60)
    
    result = update_strategy(user_a, strategy_a1, "User A Updated Strategy")
    if result:
        print("✅ User A can update their own strategy")
    else:
        print("❌ User A cannot update their own strategy!")
    
    # Test 9: Cross-user deletion (should fail)
    print("\n" + "="*60)
    print("🚫 Test 9: Cross-User Deletion Prevention")
    print("="*60)
    
    # User B trying to delete User A's strategy
    result = delete_strategy(user_b, strategy_a2)
    if not result:
        print("✅ User B correctly cannot delete User A's strategy")
    else:
        print("❌ SECURITY ISSUE: User B can delete User A's strategy!")
    
    # Test 10: Own strategy deletion (should succeed)
    print("\n" + "="*60)
    print("🗑️  Test 10: Own Strategy Deletion")
    print("="*60)
    
    result = delete_strategy(user_a, strategy_a2)
    if result:
        print("✅ User A can delete their own strategy")
    else:
        print("❌ User A cannot delete their own strategy!")
    
    # Final summary
    print("\n" + "="*60)
    print("📊 TEST SUITE COMPLETE")
    print("="*60)
    print("\n✨ All ownership access control tests completed!")
    print("Review the output above to verify all security checks passed.")
    print("\nExpected results:")
    print("  ✅ Unauthenticated access: REJECTED")
    print("  ✅ User isolation: Each user sees only their own data")
    print("  🚫 Cross-user access: FORBIDDEN")
    print("  ✅ Own data access: ALLOWED")
    print("  🚫 Cross-user modification: FORBIDDEN")
    print("  ✅ Own data modification: ALLOWED")


if __name__ == "__main__":
    try:
        run_ownership_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server")
        print("Please ensure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
