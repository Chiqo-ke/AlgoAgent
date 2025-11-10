# 🚀 AlgoAgent Authentication - Quick Reference

## Default User Credentials
```
Username: algotrader
Password: Trading@2024
Email:    algotrader@example.com
```

## Quick Start (3 Steps)

### 1. Start Server
```bash
cd AlgoAgent
python manage.py runserver 8000
```

### 2. Login (Get Tokens)
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"algotrader","password":"Trading@2024"}'
```

### 3. Chat with AI
```bash
curl -X POST http://127.0.0.1:8000/api/auth/chat/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Help me create a momentum trading strategy"}'
```

## Essential Endpoints

| Action | Endpoint | Method | Auth? |
|--------|----------|--------|-------|
| Login | `/api/auth/login/` | POST | No |
| Register | `/api/auth/register/` | POST | No |
| Get Profile | `/api/auth/profiles/me/` | GET | Yes |
| AI Chat | `/api/auth/chat/` | POST | Yes |
| List Sessions | `/api/auth/chat-sessions/` | GET | Yes |
| Create Context | `/api/auth/ai-contexts/` | POST | Yes |

## Auth Header Format
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Token Lifetimes
- **Access Token**: 1 hour
- **Refresh Token**: 7 days

## User Flow
1. Login → Get tokens
2. Set AI context (optional)
3. Start chat with AI
4. Gemini AI responds with strategy guidance
5. Continue conversation
6. AI generates strategy code

## Files to Check
- 📖 `AUTH_API_README.md` - Full documentation
- 📬 `postman_collections/Auth_API_Collection.json` - Postman tests
- 🧪 `test_auth_flow.py` - Test script
- 📝 `JWT_AUTH_IMPLEMENTATION_SUMMARY.md` - Implementation details

## Testing
```bash
# Run test script
python test_auth_flow.py

# Or import Postman collection
# File: postman_collections/Auth_API_Collection.json
```

## Common Tasks

### Create New User
```bash
python manage.py create_default_user \
  --username newuser \
  --password SecurePass123! \
  --email newuser@example.com
```

### Access Django Admin
```bash
# Create superuser first
python manage.py createsuperuser

# Then visit: http://127.0.0.1:8000/admin/
```

### View API Root
```
http://127.0.0.1:8000/api/
```

## Example: Complete Chat Session

```python
import requests

# 1. Login
response = requests.post('http://127.0.0.1:8000/api/auth/login/', json={
    'username': 'algotrader',
    'password': 'Trading@2024'
})
token = response.json()['tokens']['access']

# 2. Chat with AI
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('http://127.0.0.1:8000/api/auth/chat/', 
    headers=headers,
    json={'message': 'Create a momentum strategy'}
)
session_id = response.json()['session_id']
print(response.json()['ai_response'])

# 3. Continue conversation
response = requests.post('http://127.0.0.1:8000/api/auth/chat/',
    headers=headers,
    json={
        'session_id': session_id,
        'message': 'Generate the code'
    }
)
print(response.json()['ai_response'])
```

## Need Help?
- 📖 Read `AUTH_API_README.md` for detailed examples
- 🔍 Check Django server logs for errors
- 🧪 Use `test_auth_flow.py` to verify setup
- 📬 Import Postman collection for interactive testing

---
**Server Running?** Check: http://127.0.0.1:8000/api/
