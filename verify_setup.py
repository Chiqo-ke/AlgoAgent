"""
Setup Verification Script
Checks if all components are properly configured
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
django.setup()

print("="*60)
print("  AlgoAgent Conversation Memory - Setup Verification")
print("="*60)

# Check 1: Models imported correctly
print("\n1. Checking models...")
try:
    from strategy_api.models import StrategyChat, StrategyChatMessage
    print("   ✓ StrategyChat model imported")
    print("   ✓ StrategyChatMessage model imported")
except ImportError as e:
    print(f"   ✗ Error importing models: {e}")
    sys.exit(1)

# Check 2: Check if tables exist in database
print("\n2. Checking database tables...")
try:
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    if 'strategy_api_strategychat' in tables:
        print("   ✓ strategy_api_strategychat table exists")
    else:
        print("   ✗ strategy_api_strategychat table NOT found")
        print("   → Run: python manage.py makemigrations strategy_api")
        print("   → Run: python manage.py migrate")
    
    if 'strategy_api_strategychatmessage' in tables:
        print("   ✓ strategy_api_strategychatmessage table exists")
    else:
        print("   ✗ strategy_api_strategychatmessage table NOT found")
        print("   → Run migrations first!")
        
except Exception as e:
    print(f"   ✗ Database error: {e}")

# Check 3: ViewSet imported correctly
print("\n3. Checking ViewSet...")
try:
    from strategy_api.views import StrategyChatViewSet
    print("   ✓ StrategyChatViewSet imported")
except ImportError as e:
    print(f"   ✗ Error importing ViewSet: {e}")

# Check 4: URLs configured
print("\n4. Checking URL configuration...")
try:
    from django.urls import get_resolver
    resolver = get_resolver()
    
    # Try to resolve the chat endpoint
    from django.urls import resolve
    try:
        match = resolve('/api/strategies/chat/')
        print("   ✓ /api/strategies/chat/ endpoint configured")
    except:
        print("   ✗ /api/strategies/chat/ endpoint NOT found")
        print("   → Check strategy_api/urls.py")
    
except Exception as e:
    print(f"   ✗ URL check error: {e}")

# Check 5: Dependencies installed
print("\n5. Checking dependencies...")
try:
    import langchain
    print(f"   ✓ langchain {langchain.__version__} installed")
except ImportError:
    print("   ✗ langchain NOT installed")
    print("   → Run: pip install langchain")

try:
    import langchain_google_genai
    print("   ✓ langchain-google-genai installed")
except ImportError:
    print("   ✗ langchain-google-genai NOT installed")
    print("   → Run: pip install langchain-google-genai")

try:
    import langchain_community
    print("   ✓ langchain-community installed")
except ImportError:
    print("   ✗ langchain-community NOT installed")
    print("   → Run: pip install langchain-community")

# Check 6: Conversation manager
print("\n6. Checking conversation manager...")
try:
    from Strategy.conversation_manager import ConversationManager
    print("   ✓ ConversationManager imported")
except ImportError as e:
    print(f"   ✗ Error importing ConversationManager: {e}")

# Check 7: Enhanced Gemini integrator
print("\n7. Checking Gemini integrator...")
try:
    from Strategy.gemini_strategy_integrator import GeminiStrategyIntegrator
    print("   ✓ GeminiStrategyIntegrator imported")
    
    # Check if it has the chat method
    if hasattr(GeminiStrategyIntegrator, 'chat'):
        print("   ✓ chat() method available")
    else:
        print("   ✗ chat() method NOT found")
        
except ImportError as e:
    print(f"   ✗ Error importing GeminiStrategyIntegrator: {e}")

# Summary
print("\n" + "="*60)
print("  Setup Verification Complete!")
print("="*60)

print("\nNext steps:")
print("1. If tables are missing: python manage.py makemigrations strategy_api")
print("2. Then: python manage.py migrate")
print("3. Install missing dependencies: pip install -r strategy_requirements.txt")
print("4. Start server: python manage.py runserver")
print("5. Test: python test_conversation_memory.py")
