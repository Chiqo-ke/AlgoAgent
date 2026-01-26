# AI Agent Conversation Memory - Setup Guide

## Overview

Your AlgoAgent now has **conversation memory** and context awareness! This upgrade adds:

- ✅ **Persistent conversation history** stored in SQLite database
- ✅ **LangChain integration** for advanced memory management
- ✅ **Context-aware responses** - the AI remembers previous messages
- ✅ **Multiple concurrent sessions** - handle many conversations at once
- ✅ **Strategy-linked chats** - associate conversations with specific strategies

## What Changed

### New Models
- `StrategyChat` - Stores chat sessions
- `StrategyChatMessage` - Stores individual messages

### New Modules
- `conversation_manager.py` - LangChain + Django integration
- Enhanced `gemini_strategy_integrator.py` - Now supports conversation context

### New API Endpoints
- `POST /api/strategies/chat/chat/` - Send message and get AI response
- `GET /api/strategies/chat/` - List all chat sessions
- `GET /api/strategies/chat/{id}/messages/` - Get session messages
- `POST /api/strategies/chat/{id}/summarize/` - Get AI summary
- `POST /api/strategies/chat/{id}/clear/` - Clear conversation
- `POST /api/strategies/chat/{id}/deactivate/` - Deactivate session

## Setup Instructions

### Step 1: Install Dependencies

Navigate to the AlgoAgent directory and install the required packages:

```powershell
cd AlgoAgent
pip install -r strategy_requirements.txt
```

This will install:
- `langchain>=0.1.0`
- `langchain-google-genai>=0.0.5`
- `langchain-community>=0.0.10`

### Step 2: Create Database Migrations

Generate and apply the database migrations for the new models:

```powershell
python manage.py makemigrations strategy_api
python manage.py migrate
```

Expected output:
```
Migrations for 'strategy_api':
  strategy_api\migrations\0003_strategychat_strategychatmessage.py
    - Create model StrategyChat
    - Create model StrategyChatMessage
    - Add index strategy_api_strategychat_session_id
    - Add index strategy_api_strategychat_user_id_updated_at
    - Add index strategy_api_strategychatmessage_session_id_created_at
```

### Step 3: Configure Gemini API Key

Make sure your `.env` file has a valid Gemini API key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

### Step 4: Start the Django Server

```powershell
python manage.py runserver
```

## Usage Examples

### Example 1: Simple Conversation

**Request:** (POST to `/api/strategies/chat/chat/`)
```json
{
  "message": "I want to create a momentum trading strategy",
  "use_context": true
}
```

**Response:**
```json
{
  "session_id": "chat_abc123def456",
  "message": "Great! A momentum trading strategy focuses on...",
  "message_count": 1,
  "context_used": true
}
```

**Follow-up Request:** (with session_id to maintain context)
```json
{
  "message": "What indicators should I use?",
  "session_id": "chat_abc123def456",
  "use_context": true
}
```

**Response:**
```json
{
  "session_id": "chat_abc123def456",
  "message": "For the momentum strategy we discussed, I recommend...",
  "message_count": 3,
  "context_used": true
}
```

Notice how the AI references "the momentum strategy we discussed" - it remembers!

### Example 2: Link Chat to Strategy

```json
{
  "message": "How can I improve this strategy?",
  "session_id": "chat_abc123def456",
  "strategy_id": 42,
  "use_context": true
}
```

The AI will now have access to the strategy details and conversation history.

### Example 3: Get Conversation History

**Request:** (GET to `/api/strategies/chat/{session_id}/messages/`)

**Response:**
```json
[
  {
    "id": 1,
    "role": "user",
    "content": "I want to create a momentum trading strategy",
    "created_at": "2025-10-29T10:30:00Z"
  },
  {
    "id": 2,
    "role": "assistant",
    "content": "Great! A momentum trading strategy focuses on...",
    "created_at": "2025-10-29T10:30:05Z"
  },
  {
    "id": 3,
    "role": "user",
    "content": "What indicators should I use?",
    "created_at": "2025-10-29T10:31:00Z"
  }
]
```

### Example 4: Generate Conversation Summary

**Request:** (POST to `/api/strategies/chat/{session_id}/summarize/`)

**Response:**
```json
{
  "session_id": "chat_abc123def456",
  "summary": "User discussed creating a momentum trading strategy using RSI and moving averages. Decided on daily timeframe with 14-period RSI...",
  "message_count": 8
}
```

## Testing the Implementation

Run the comprehensive test script:

```powershell
python test_conversation_memory.py
```

This will:
1. Start a multi-turn conversation
2. Test context retention across messages
3. Create multiple concurrent sessions
4. Demonstrate strategy validation with memory

## Integration with Existing Code

### In Strategy Validation

The AI validation endpoints now optionally track conversations:

```python
# When calling validate_strategy_with_ai
{
  "strategy_text": "Buy when RSI < 30...",
  "use_gemini": true,
  "session_id": "chat_abc123",  # Optional: link to conversation
}
```

### In Python Code

```python
from Strategy.conversation_manager import ConversationManager
from Strategy.gemini_strategy_integrator import GeminiStrategyIntegrator

# Create or retrieve a conversation
conv_manager = ConversationManager(session_id="chat_abc123", user=request.user)

# Initialize AI with conversation context
ai = GeminiStrategyIntegrator(
    session_id=conv_manager.session_id,
    user=request.user
)

# Chat with context
response = ai.chat("How can I improve my strategy?")

# The AI remembers previous messages!
```

## Database Schema

### StrategyChat Table
- `session_id` - Unique session identifier
- `user` - Foreign key to User
- `strategy` - Optional link to Strategy
- `title` - Session title
- `is_active` - Active status
- `context_summary` - AI-generated summary
- `message_count` - Total messages
- `model_name` - AI model used
- `temperature` / `max_tokens` - AI settings
- Timestamps: `created_at`, `updated_at`, `last_message_at`

### StrategyChatMessage Table
- `session` - Foreign key to StrategyChat
- `role` - 'user', 'assistant', or 'system'
- `content` - Message text
- `tokens_used` - Optional token count
- `metadata` - JSON field for extra data
- `function_call` - JSON for function calls
- `created_at` - Timestamp

## Architecture

```
┌─────────────────┐
│   User Request  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  StrategyChatViewSet    │  (API Endpoint)
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  ConversationManager    │  (LangChain Integration)
│  - DjangoSQLiteChatHistory
│  - Memory Management    │
└────────┬────────────────┘
         │
         ├──────────────────┐
         ▼                  ▼
┌──────────────┐   ┌────────────────────┐
│  SQLite DB   │   │ GeminiIntegrator   │
│  (Django)    │   │ (AI Responses)     │
│              │   │                    │
│ StrategyChat │   │ - Context-aware    │
│ ChatMessage  │   │ - Chat method      │
└──────────────┘   └────────────────────┘
```

## Benefits

1. **Contextual Conversations** - AI remembers what was discussed
2. **Persistent Storage** - All conversations saved in database
3. **Multiple Sessions** - Handle many conversations simultaneously
4. **Strategy Integration** - Link chats to specific strategies
5. **Scalable** - LangChain provides advanced memory management
6. **Traceable** - Full conversation history for audit/debugging

## Troubleshooting

### Migration Issues
If you see "ChatSession already exists" error:
- The conflict was with `auth_api.ChatSession`
- We renamed to `StrategyChat` to avoid conflicts
- Run: `python manage.py makemigrations strategy_api --name add_strategy_chat`

### Import Errors
If you see LangChain import errors:
- Ensure packages are installed: `pip install -r strategy_requirements.txt`
- Check Python environment is activated

### API Not Responding
- Check Django server is running: `python manage.py runserver`
- Verify URL: `http://localhost:8000/api/strategies/chat/chat/`
- Check GEMINI_API_KEY in `.env` file

## Next Steps

1. **Run migrations** to create the database tables
2. **Test the API** using the test script or Postman
3. **Integrate** with your frontend application
4. **Monitor** conversation quality and adjust as needed

## API Documentation

Full API documentation available at:
- Swagger UI: `http://localhost:8000/swagger/`
- Chat endpoints: `http://localhost:8000/api/strategies/chat/`

---

**Congratulations!** Your AI agent now has memory and can maintain context across conversations! 🎉
