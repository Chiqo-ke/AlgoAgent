# Quick Start: Conversation Memory

## Installation (2 minutes)

```powershell
# 1. Install packages
cd AlgoAgent
pip install langchain langchain-google-genai langchain-community

# 2. Create migrations
python manage.py makemigrations strategy_api
python manage.py migrate

# 3. Start server
python manage.py runserver
```

## Basic Usage

### Python API

```python
from Strategy.conversation_manager import ConversationManager
from Strategy.gemini_strategy_integrator import GeminiStrategyIntegrator

# Start a conversation
conv = ConversationManager(user=request.user)
ai = GeminiStrategyIntegrator(session_id=conv.session_id, user=request.user)

# Chat with memory
response1 = ai.chat("I want to create a momentum strategy")
response2 = ai.chat("What timeframe should I use?")  # AI remembers context!

# Get history
history = conv.get_conversation_history()

# Summarize
summary = ai.summarize_conversation()
```

### REST API

```bash
# Send first message (creates new session)
curl -X POST http://localhost:8000/api/strategies/chat/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to create a momentum strategy"}'

# Response includes session_id
# {"session_id": "chat_abc123", "message": "...", "message_count": 1}

# Send follow-up (with session_id)
curl -X POST http://localhost:8000/api/strategies/chat/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What indicators should I use?",
    "session_id": "chat_abc123"
  }'

# Get conversation history
curl http://localhost:8000/api/strategies/chat/chat_abc123/messages/

# List all sessions
curl http://localhost:8000/api/strategies/chat/
```

## Test It

```powershell
python test_conversation_memory.py
```

## Key Features

✅ **Memory** - AI remembers previous messages  
✅ **Persistent** - Conversations saved in SQLite  
✅ **Multi-session** - Handle multiple conversations  
✅ **Strategy-linked** - Associate chats with strategies  
✅ **LangChain** - Advanced memory management  

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/strategies/chat/chat/` | Send message |
| GET | `/api/strategies/chat/` | List sessions |
| GET | `/api/strategies/chat/{id}/messages/` | Get messages |
| POST | `/api/strategies/chat/{id}/summarize/` | Summarize |
| POST | `/api/strategies/chat/{id}/clear/` | Clear history |

## Example Conversation

```json
// Message 1
POST /api/strategies/chat/chat/
{
  "message": "Create a RSI strategy"
}

// Response
{
  "session_id": "chat_xyz",
  "message": "I'll help you create an RSI strategy...",
  "message_count": 1
}

// Message 2 (AI remembers context!)
POST /api/strategies/chat/chat/
{
  "message": "What about exit rules?",
  "session_id": "chat_xyz"
}

// Response references previous discussion
{
  "session_id": "chat_xyz",
  "message": "For the RSI strategy we're building...",
  "message_count": 3
}
```

That's it! Your AI agent now has memory! 🧠
