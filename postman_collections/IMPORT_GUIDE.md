# 📬 How to Import AlgoAgent Postman Collections

## 🚀 Quick Start (AI Strategy Validation)

### ⚡ Just Want to Test AI Features?
Import the **Quick Start** collection:
1. Click **"Import"** in Postman
2. Select **`Quick_AI_Strategy_Validation.json`**
3. That's it! Ready to test AI validation endpoints

This mini-collection includes:
- ✅ Validate Strategy with AI
- ✅ Create Strategy with AI  
- ✅ Update Strategy with AI
- ✅ Health Check
- ✅ Example strategies (RSI, EMA, Bollinger)
- ✅ Auto-configured environment variables

---

## Full Import Guide

### Step 1: Open Postman
- Launch the Postman desktop application or web version

### Step 2: Import Collection & Environment

#### Option A: Import All at Once
1. Click **"Import"** button (top left)
2. Drag and drop ALL files from `AlgoAgent/postman_collections/`:
   - ✅ `Auth_API_Collection.json` ⭐ Authentication & AI Chat
   - ✅ `Data_API_Collection.json` - Market Data
   - ✅ `Strategy_API_Collection.json` - Strategy Management
   - ✅ `Strategy_AI_Validation_Collection.json` ⭐ AI Validation (Full)
   - ✅ `Quick_AI_Strategy_Validation.json` ⭐ AI Validation (Quick)
   - ✅ `Backtest_API_Collection.json` - Backtesting
   - ✅ `AlgoAgent_Environment.json` - Environment Variables

#### Option B: Import One by One
1. Click **"Import"**
2. Select **"Auth_API_Collection.json"** first
3. Repeat for other collections

#### Option C: Just AI Features (Recommended for Quick Testing)
1. Click **"Import"**
2. Select **`Quick_AI_Strategy_Validation.json`**
3. Done! Environment auto-configured

### Step 3: Set Active Environment
1. Click environment dropdown (top right)
2. Select **"AlgoAgent Development Environment"** (if imported)
3. Or use the built-in environment in Quick collection
4. Verify variables are loaded (click eye icon)

### Step 4: Test Authentication Flow

#### 4.1: Login to Get Tokens
1. Open **"Auth API"** collection
2. Go to **"Authentication"** folder
3. Run **"Login"** request
4. ✅ Tokens automatically saved to environment variables!

#### 4.2: Test Protected Endpoint
1. Go to **"User Profile"** folder
2. Run **"Get My Profile"**
3. Should return user details (uses auto-saved token)

#### 4.3: Test AI Chat
1. Create AI Context (optional):
   - Go to **"AI Context"** → **"Create AI Context"**
   - Run request
2. Start AI Chat:
   - Go to **"AI Chat Agent"** → **"Start New Chat"**
   - Run request
   - AI will respond with strategy guidance!

## 🎯 What's Included in Each Collection

### 1. Auth_API_Collection.json ⭐ NEW!
**15 Total Requests**
- 🔐 **Authentication** (5): Register, Login, Logout, Refresh Token, Get Current User
- 👤 **User Profile** (2): Get Profile, Update Profile  
- 🧠 **AI Context** (3): List, Create, Get Context
- 💬 **AI Chat Agent** (4): Start Chat, Continue Chat, List Sessions, Get Session Details
- ❤️ **Health Check** (1): Service status

### 2. Data_API_Collection.json
**21 Requests** - Market data, symbols, indicators

### 3. Strategy_API_Collection.json  
**29 Requests** - Strategy management, AI code generation

### 4. Backtest_API_Collection.json
**32 Requests** - Backtesting, performance analysis

### 5. AlgoAgent_Environment.json
**Pre-configured variables:**
- `baseUrl`: http://127.0.0.1:8000
- `default_username`: algotrader
- `default_password`: Trading@2024
- `access_token`: Auto-set after login
- `refresh_token`: Auto-set after login
- Plus all other API variables

## 🔄 Automatic Token Management

The Auth collection includes **auto-scripts** that:
1. ✅ Save access token after login
2. ✅ Save refresh token after login
3. ✅ Save user ID after login
4. ✅ Save AI context ID after creating context
5. ✅ Save session ID after starting chat

**You don't need to copy/paste tokens manually!**

## 📝 Test Sequence (Recommended)

### First Time Setup:
```
1. Login → Get tokens (auto-saved)
2. Get Current User → Verify authentication works
3. Get My Profile → See user preferences
4. Create AI Context → Set up strategy context
5. Start New Chat → Talk with AI about strategies
6. Continue Chat → Keep the conversation going
```

### Subsequent Sessions:
```
1. Login → Refresh your tokens
2. Continue Chat → Pick up where you left off
   OR
   Start New Chat → Begin new strategy session
```

## 🎨 Collection Features

### Authentication Folder
- **Login** - Auto-saves tokens to environment
- **Register** - Create new users
- **Refresh Token** - Auto-updates access token
- **Logout** - Blacklist tokens securely
- **Get Current User** - Verify who's logged in

### AI Chat Agent Folder
- **Start New Chat** - Begin AI conversation
  - Auto-saves `session_id`
  - Uses `ai_context_id` if provided
- **Continue Chat** - Multi-turn conversations
  - Uses saved `session_id`
  - Maintains conversation history
- **List Chat Sessions** - See all your sessions
- **Get Session Details** - Full conversation history

### AI Context Folder
- **Create AI Context** - Set up trading preferences
  - Auto-saves `ai_context_id`
  - Used in chat sessions for personalized responses
- **List AI Contexts** - View all your contexts
- **Get AI Context** - Details of specific context

## 🧪 Example: Complete Flow in Postman

1. **Import everything** (5 JSON files)
2. **Select environment** (AlgoAgent Development Environment)
3. **Run "Login"** request
   - Check: Tokens saved in environment (eye icon → see `access_token`)
4. **Run "Create AI Context"** with body:
   ```json
   {
     "session_name": "My First Strategy",
     "instructions": "Help me create a momentum strategy for daily trading",
     "is_active": true
   }
   ```
   - Check: `ai_context_id` saved
5. **Run "Start New Chat"** with body:
   ```json
   {
     "message": "What indicators should I use for momentum trading?",
     "ai_context_id": {{ai_context_id}},
     "title": "Momentum Strategy Development"
   }
   ```
   - Check: AI responds with strategy advice
   - Check: `session_id` saved
6. **Run "Continue Chat"** with body:
   ```json
   {
     "session_id": "{{session_id}}",
     "message": "Can you generate the Python code for this?"
   }
   ```
   - AI generates strategy code!

## 🔧 Troubleshooting

### "Could not get response" errors:
- ✅ Make sure Django server is running: `python manage.py runserver 8000`
- ✅ Check environment is selected (top right dropdown)
- ✅ Verify `baseUrl` is correct in environment

### "401 Unauthorized" errors:
- ✅ Run "Login" request first
- ✅ Check `access_token` is in environment (eye icon)
- ✅ Token might be expired (expires in 1 hour) - run "Refresh Token"

### "No module named 'rest_framework_simplejwt'" error:
- ✅ Activate virtual environment: `.\.venv\Scripts\Activate.ps1`
- ✅ Install packages: `pip install djangorestframework-simplejwt[crypto]`

### AI Chat not working:
- ✅ Check `.env` file has `GEMINI_API_KEY`
- ✅ Verify you're logged in (have valid access token)
- ✅ Check Django server logs for errors

## 📊 Environment Variables Reference

| Variable | Default Value | Auto-Set | Purpose |
|----------|---------------|----------|---------|
| `baseUrl` | http://127.0.0.1:8000 | No | API base URL |
| `authApiBase` | {{baseUrl}}/api/auth | No | Auth endpoints |
| `default_username` | algotrader | No | Default login |
| `default_password` | Trading@2024 | No | Default password |
| `access_token` | (empty) | ✅ Yes | JWT access token |
| `refresh_token` | (empty) | ✅ Yes | JWT refresh token |
| `user_id` | (empty) | ✅ Yes | Current user ID |
| `ai_context_id` | (empty) | ✅ Yes | Active AI context |
| `session_id` | (empty) | ✅ Yes | Active chat session |

## 🎓 Next Steps

After importing:
1. ✅ Test login with default user
2. ✅ Explore all folders in the collection
3. ✅ Create your own AI contexts
4. ✅ Start chatting with AI about strategies
5. ✅ Use other collections (Data, Strategy, Backtest)
6. ✅ Create your own custom requests

## 📚 Additional Resources

- **Full Auth Guide**: `AUTH_API_README.md`
- **Quick Reference**: `QUICK_START_AUTH.md`
- **Implementation Details**: `JWT_AUTH_IMPLEMENTATION_SUMMARY.md`
- **Main API Docs**: `DJANGO_API_README.md`
- **All Collections README**: `postman_collections/README.md`

---

**Ready to Import?** 
📁 Files are in: `AlgoAgent/postman_collections/`

Just drag and drop all 5 JSON files into Postman! 🚀
