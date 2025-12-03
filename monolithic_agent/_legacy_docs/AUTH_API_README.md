# AlgoAgent Authentication & AI Chat System

## 🎯 Overview

The AlgoAgent API now includes a complete authentication system with JWT tokens, user profiles, AI context management, and an AI-powered chat agent for strategy development using Gemini AI.

## 🔑 Features

### Authentication
- **JWT Token-based Authentication**: Secure access with access and refresh tokens
- **User Registration & Login**: Create accounts and authenticate
- **Token Refresh**: Automatically refresh expired access tokens
- **Token Blacklisting**: Secure logout with token invalidation
- **Default User**: Pre-configured user for immediate testing

### User Profiles
- Extended user profiles with trading preferences
- Risk tolerance settings (Conservative, Moderate, Aggressive)
- Preferred trading timeframes and symbols
- Trading goals and strategy preferences
- Custom risk parameters

### AI Context Management
- Store user instructions for AI interactions
- Multiple contexts for different trading strategies
- Structured context data for better AI responses
- Session-based context activation

### AI Chat Agent
- Interactive chat with Gemini AI for strategy development
- Context-aware conversations using user preferences
- Conversation history tracking
- Strategy code generation assistance
- Multi-turn conversations with memory

## 🚀 Quick Start

### 1. Default User Credentials

A default user has been created for immediate testing:

```
Username: algotrader
Password: Trading@2024
Email:    algotrader@example.com
```

### 2. Start the Server

```bash
cd AlgoAgent
python manage.py runserver 8000
```

The API will be available at: `http://127.0.0.1:8000`

### 3. Login to Get Tokens

**Request:**
```bash
POST http://127.0.0.1:8000/api/auth/login/
Content-Type: application/json

{
    "username": "algotrader",
    "password": "Trading@2024"
}
```

**Response:**
```json
{
    "user": {
        "id": 1,
        "username": "algotrader",
        "email": "algotrader@example.com",
        "first_name": "Algo",
        "last_name": "Trader"
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    },
    "message": "Login successful"
}
```

### 4. Use the Access Token

Include the access token in all subsequent requests:

```bash
Authorization: Bearer <access_token>
```

## 📡 API Endpoints

### Authentication Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/auth/register/` | POST | No | Register new user |
| `/api/auth/login/` | POST | No | Login and get tokens |
| `/api/auth/logout/` | POST | Yes | Logout and blacklist token |
| `/api/auth/token/refresh/` | POST | No | Refresh access token |
| `/api/auth/user/me/` | GET | Yes | Get current user details |

### User Profile Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/auth/profiles/` | GET | Yes | List user profiles |
| `/api/auth/profiles/me/` | GET | Yes | Get my profile |
| `/api/auth/profiles/update_me/` | PATCH | Yes | Update my profile |

### AI Context Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/auth/ai-contexts/` | GET | Yes | List AI contexts |
| `/api/auth/ai-contexts/` | POST | Yes | Create AI context |
| `/api/auth/ai-contexts/{id}/` | GET | Yes | Get AI context |
| `/api/auth/ai-contexts/{id}/` | PATCH | Yes | Update AI context |
| `/api/auth/ai-contexts/{id}/activate/` | POST | Yes | Activate context |
| `/api/auth/ai-contexts/{id}/deactivate/` | POST | Yes | Deactivate context |

### AI Chat Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/auth/chat/` | POST | Yes | Chat with AI agent |
| `/api/auth/chat-sessions/` | GET | Yes | List chat sessions |
| `/api/auth/chat-sessions/{id}/` | GET | Yes | Get session details |
| `/api/auth/chat-sessions/{id}/end_session/` | POST | Yes | End chat session |

## 💬 Complete User Flow Example

### Step 1: Login

```bash
POST /api/auth/login/
{
    "username": "algotrader",
    "password": "Trading@2024"
}
```

Save the `access_token` and `refresh_token` from the response.

### Step 2: Create AI Context (Optional)

```bash
POST /api/auth/ai-contexts/
Authorization: Bearer <access_token>

{
    "session_name": "Momentum Strategy Development",
    "instructions": "I want to develop a momentum-based trading strategy that works on daily timeframes. Focus on strong trending stocks with high relative strength. The strategy should include proper risk management with stop-losses and position sizing.",
    "context_data": {
        "strategy_type": "momentum",
        "timeframe": "1d",
        "indicators": ["RSI", "MACD", "Moving Averages"]
    },
    "is_active": true
}
```

Save the `id` from the response as `ai_context_id`.

### Step 3: Start AI Chat Session

```bash
POST /api/auth/chat/
Authorization: Bearer <access_token>

{
    "message": "Hi! I want to create a momentum trading strategy. Can you help me get started?",
    "ai_context_id": 1,
    "title": "Momentum Strategy Development"
}
```

**Response:**
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Momentum Strategy Development",
    "user_message": "Hi! I want to create a momentum trading strategy. Can you help me get started?",
    "ai_response": "Hello! I'd be happy to help you create a momentum trading strategy...",
    "tokens_used": 150
}
```

Save the `session_id` for continuing the conversation.

### Step 4: Continue the Conversation

```bash
POST /api/auth/chat/
Authorization: Bearer <access_token>

{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What indicators should I use for detecting momentum?"
}
```

### Step 5: Ask AI to Generate Strategy Code

```bash
POST /api/auth/chat/
Authorization: Bearer <access_token>

{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Can you generate the Python code for this momentum strategy?"
}
```

The AI will generate strategy code based on your conversation history and context.

### Step 6: View Chat History

```bash
GET /api/auth/chat-sessions/<session_id>/
Authorization: Bearer <access_token>
```

This returns the full conversation history with all messages.

## 🔐 JWT Token Management

### Access Token
- **Lifetime**: 1 hour
- **Purpose**: Authenticate API requests
- **Usage**: Include in `Authorization: Bearer <token>` header

### Refresh Token
- **Lifetime**: 7 days
- **Purpose**: Obtain new access tokens
- **Auto-rotation**: New refresh token issued on each refresh

### Token Refresh Flow

When your access token expires (after 1 hour), use the refresh token:

```bash
POST /api/auth/token/refresh/
{
    "refresh": "<refresh_token>"
}
```

**Response:**
```json
{
    "access": "<new_access_token>",
    "refresh": "<new_refresh_token>"
}
```

Update your stored tokens and continue using the API.

## 👤 User Profile Configuration

### Update Trading Preferences

```bash
PATCH /api/auth/profiles/update_me/
Authorization: Bearer <access_token>

{
    "default_risk_tolerance": "moderate",
    "default_timeframe": "1d",
    "preferred_symbols": ["AAPL", "GOOGL", "MSFT"],
    "trading_goals": "Build consistent income through algorithmic trading",
    "strategy_preferences": "Momentum and trend-following strategies",
    "risk_parameters": {
        "max_position_size": 0.1,
        "max_drawdown": 0.15,
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.05
    }
}
```

These preferences will be used as context for AI conversations.

## 🤖 AI Chat Agent Capabilities

The AI chat agent can help you with:

1. **Strategy Development**: Discuss trading ideas and approaches
2. **Code Generation**: Generate Python strategy code
3. **Indicator Selection**: Recommend technical indicators
4. **Risk Management**: Suggest risk management approaches
5. **Backtesting Advice**: Guide on testing strategies
6. **Strategy Optimization**: Improve existing strategies

### Context-Aware Responses

The AI uses:
- Your AI context instructions
- Your user profile preferences
- Conversation history
- Trading goals and risk tolerance

This ensures personalized and relevant strategy recommendations.

## 📝 Creating Additional Users

### Via API (Registration)

```bash
POST /api/auth/register/
{
    "username": "newtrader",
    "email": "newtrader@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "New",
    "last_name": "Trader"
}
```

### Via Management Command

```bash
python manage.py create_default_user --username customuser --password CustomPass123! --email custom@example.com
```

## 🧪 Testing with Postman

A complete Postman collection is available at:
```
AlgoAgent/postman_collections/Auth_API_Collection.json
```

**Import Steps:**
1. Open Postman
2. Click "Import"
3. Select the `Auth_API_Collection.json` file
4. The collection includes all authentication, profile, and chat endpoints

**Environment Variables:**
The collection uses these variables:
- `base_url`: http://127.0.0.1:8000
- `access_token`: Auto-set after login
- `refresh_token`: Auto-set after login
- `ai_context_id`: Auto-set after creating context
- `session_id`: Auto-set after starting chat

## 🔒 Security Best Practices

1. **Change Default User Password**: Update the default user's password in production
2. **Use HTTPS**: Always use HTTPS in production
3. **Token Storage**: Store tokens securely (HTTPOnly cookies recommended)
4. **Token Expiration**: Implement automatic token refresh in your client
5. **Environment Variables**: Store `SECRET_KEY` in environment variables

## 🐛 Troubleshooting

### "Invalid credentials" Error
- Verify username and password are correct
- Check that the user exists in the database

### "Token is invalid or expired"
- Access token expires after 1 hour
- Use the refresh token to get a new access token
- If refresh token is also expired, login again

### "Authentication credentials were not provided"
- Include `Authorization: Bearer <token>` header
- Verify the token is not expired

### AI Chat Not Working
- Ensure `GEMINI_API_KEY` is set in `.env` file
- Check that Gemini API is accessible
- Verify the AI context exists and is active

## 📚 Related Documentation

- **Django API README**: `DJANGO_API_README.md`
- **Postman Collections**: `postman_collections/README.md`
- **Strategy API**: Check strategy_api documentation
- **Backtest API**: Check backtest_api documentation

## 🎓 Next Steps

1. **Explore the API**: Use Postman to test all endpoints
2. **Create Custom Contexts**: Set up AI contexts for different strategy types
3. **Chat with AI**: Start developing your trading strategies
4. **Integrate with Frontend**: Build a UI using the React app in `Algo/`
5. **Protect Endpoints**: Update other API endpoints to require authentication

## ⚙️ Configuration

### JWT Settings (in `settings.py`)

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    ...
}
```

### CORS Settings

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    ...
]
```

Update these to match your frontend application URLs.

---

**Need Help?** Check the API at `http://127.0.0.1:8000/api/` for a complete list of available endpoints.
