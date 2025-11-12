"""
Test Authentication and AI Chat Flow
=====================================

Quick test script to verify the authentication system and AI chat agent.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
USERNAME = "algotrader"
PASSWORD = "Trading@2024"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(title):
    print(f"\n{BLUE}{'='*60}")
    print(f" {title}")
    print(f"{'='*60}{RESET}\n")


def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    print(f"{RED}✗ {message}{RESET}")


def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")


def test_login():
    """Test user login"""
    print_header("Testing Login")
    
    url = f"{BASE_URL}/api/auth/login/"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Login successful for user: {result['user']['username']}")
            print_info(f"Access token: {result['tokens']['access'][:50]}...")
            return result['tokens']['access'], result['tokens']['refresh']
        else:
            print_error(f"Login failed: {response.status_code}")
            print(response.text)
            return None, None
    except Exception as e:
        print_error(f"Login error: {str(e)}")
        return None, None


def test_current_user(access_token):
    """Test getting current user details"""
    print_header("Testing Current User Endpoint")
    
    url = f"{BASE_URL}/api/auth/user/me/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_success("Current user retrieved successfully")
            print_info(f"Username: {result['user']['username']}")
            print_info(f"Email: {result['user']['email']}")
            print_info(f"Risk Tolerance: {result['profile']['default_risk_tolerance']}")
            print_info(f"Preferred Symbols: {', '.join(result['profile']['preferred_symbols'])}")
            return True
        else:
            print_error(f"Failed to get current user: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_create_ai_context(access_token):
    """Test creating an AI context"""
    print_header("Testing AI Context Creation")
    
    url = f"{BASE_URL}/api/auth/ai-contexts/"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "session_name": "Test Momentum Strategy",
        "instructions": "I want to develop a momentum-based trading strategy for daily timeframes. Focus on stocks with strong trends and high relative strength.",
        "context_data": {
            "strategy_type": "momentum",
            "timeframe": "1d",
            "indicators": ["RSI", "MACD", "Moving Averages"]
        },
        "is_active": True
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            print_success(f"AI Context created: {result['session_name']}")
            print_info(f"Context ID: {result['id']}")
            return result['id']
        else:
            print_error(f"Failed to create AI context: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def test_ai_chat(access_token, ai_context_id=None):
    """Test AI chat interaction"""
    print_header("Testing AI Chat Agent")
    
    url = f"{BASE_URL}/api/auth/chat/"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "message": "Hi! I want to create a simple momentum trading strategy. What indicators would you recommend?",
        "title": "Test Strategy Session"
    }
    
    if ai_context_id:
        data["ai_context_id"] = ai_context_id
    
    try:
        print_info("Sending message to AI...")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_success("AI response received successfully")
            print_info(f"Session ID: {result['session_id']}")
            print_info(f"Title: {result['title']}")
            print(f"\n{GREEN}User Message:{RESET} {result['user_message']}")
            print(f"\n{BLUE}AI Response:{RESET} {result['ai_response'][:500]}...")
            return result['session_id']
        else:
            print_error(f"AI chat failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None


def test_continue_chat(access_token, session_id):
    """Test continuing a chat session"""
    print_header("Testing Continue Chat")
    
    url = f"{BASE_URL}/api/auth/chat/"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "session_id": session_id,
        "message": "Can you show me a simple example of how to implement RSI in a strategy?"
    }
    
    try:
        print_info("Sending follow-up message...")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_success("Follow-up response received")
            print(f"\n{GREEN}User Message:{RESET} {result['user_message']}")
            print(f"\n{BLUE}AI Response:{RESET} {result['ai_response'][:500]}...")
            return True
        else:
            print_error(f"Failed to continue chat: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_list_chat_sessions(access_token):
    """Test listing chat sessions"""
    print_header("Testing List Chat Sessions")
    
    url = f"{BASE_URL}/api/auth/chat-sessions/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            sessions = result.get('results', result) if isinstance(result, dict) else result
            print_success(f"Retrieved {len(sessions)} chat session(s)")
            for session in sessions[:3]:  # Show first 3
                print_info(f"- {session['title']} ({session['session_id'][:8]}...)")
            return True
        else:
            print_error(f"Failed to list sessions: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_health_check(access_token):
    """Test health check endpoint"""
    print_header("Testing Health Check")
    
    url = f"{BASE_URL}/api/auth/health/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Auth API Status: {result['status']}")
            print_info(f"User: {result['user']}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}")
    print(" AlgoAgent Authentication & AI Chat Test Suite")
    print(f"{'='*60}{RESET}")
    print(f"\nTesting against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test login
    access_token, refresh_token = test_login()
    if not access_token:
        print_error("\nTests aborted: Login failed")
        return
    
    # Test current user
    test_current_user(access_token)
    
    # Test AI context creation
    ai_context_id = test_create_ai_context(access_token)
    
    # Test AI chat
    session_id = test_ai_chat(access_token, ai_context_id)
    
    # Test continuing chat
    if session_id:
        test_continue_chat(access_token, session_id)
    
    # Test listing sessions
    test_list_chat_sessions(access_token)
    
    # Test health check
    test_health_check(access_token)
    
    print(f"\n{GREEN}{'='*60}")
    print(" All Tests Completed!")
    print(f"{'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
