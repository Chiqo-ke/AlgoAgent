# Google OAuth API Testing Guide

Quick reference for testing the Google OAuth endpoints.

## Endpoints

### 1. Initiate Google OAuth (Redirect)

**GET** `/api/auth/google/`

**Query Parameters:**
- `redirect_uri` (required) - The frontend callback URL

**Example:**
```
GET http://localhost:8000/api/auth/google/?redirect_uri=http://localhost:5173/auth/callback
```

**Response:**
Redirects to Google OAuth consent screen

---

### 2. Handle OAuth Callback

**POST** `/api/auth/google/callback/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "code": "4/0AfJohXlxxx...",
  "redirect_uri": "http://localhost:5173/auth/callback"
}
```

**Success Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "john_doe_abc12345",
    "email": "[email protected]",
    "first_name": "John",
    "last_name": "Doe"
  },
  "message": "Login successful"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "code and redirect_uri are required"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "error": "Google OAuth not configured"
}
```

---

## Testing with Postman/Insomnia

### Test Flow

1. **Manual Browser Test:**
   - Open: `http://localhost:8000/api/auth/google/?redirect_uri=http://localhost:5173/auth/callback`
   - You'll be redirected to Google
   - After authorizing, check the URL for the `code` parameter
   - Copy the code

2. **Test Callback:**
   ```http
   POST http://localhost:8000/api/auth/google/callback/
   Content-Type: application/json

   {
     "code": "PASTE_CODE_HERE",
     "redirect_uri": "http://localhost:5173/auth/callback"
   }
   ```

3. **Use the Access Token:**
   ```http
   GET http://localhost:8000/api/auth/user/me/
   Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
   ```

---

## Testing with cURL

### Initiate OAuth (Browser will open)
```bash
# This will redirect, so use a browser instead
curl -L "http://localhost:8000/api/auth/google/?redirect_uri=http://localhost:5173/auth/callback"
```

### Test Callback
```bash
curl -X POST http://localhost:8000/api/auth/google/callback/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "YOUR_CODE_HERE",
    "redirect_uri": "http://localhost:5173/auth/callback"
  }'
```

### Verify Token
```bash
curl http://localhost:8000/api/auth/user/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Full Frontend Flow

The complete flow as implemented in the frontend:

1. **User clicks "Continue with Google"**
   ```javascript
   const googleAuthUrl = `${API_ENDPOINTS.auth.googleAuth}?redirect_uri=${encodeURIComponent(window.location.origin + '/auth/callback')}`;
   window.location.href = googleAuthUrl;
   ```

2. **Backend redirects to Google**
   - User sees Google consent screen
   - User authorizes the app

3. **Google redirects to frontend callback**
   - URL: `http://localhost:5173/auth/callback?code=ABC123...`

4. **Frontend exchanges code for tokens**
   ```javascript
   const response = await fetch('http://localhost:8000/api/auth/google/callback/', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       code: urlParams.get('code'),
       redirect_uri: window.location.origin + '/auth/callback'
     })
   });
   
   const data = await response.json();
   localStorage.setItem('access_token', data.access);
   localStorage.setItem('refresh_token', data.refresh);
   ```

5. **User is logged in**
   - Navigate to dashboard

---

## Common Issues

### Code Already Used
- OAuth codes are single-use only
- If you get "invalid_grant", get a new code by starting the flow again

### Invalid Redirect URI
- Ensure the `redirect_uri` in the callback exactly matches what was used in the initial request
- Must match one of the authorized redirect URIs in Google Console

### Token Expired
- Access tokens expire after 1 hour (configurable in settings.py)
- Use the refresh token to get a new access token:
  ```http
  POST http://localhost:8000/api/auth/token/refresh/
  Content-Type: application/json

  {
    "refresh": "YOUR_REFRESH_TOKEN"
  }
  ```

---

## Environment Variables Required

Make sure these are set in `.env`:

```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
```

---

## User Data Handling

When a user logs in with Google:

- **New User**: Creates Django user with:
  - Email from Google
  - Username: `{email_prefix}_{google_id_prefix}`
  - No password (OAuth users can't use password login)
  - UserProfile with Google avatar

- **Existing User**: Logs in existing user
  - Updates last_active timestamp
  - Updates avatar if not set

---

## Security Notes

✅ **What's Secure:**
- Tokens are JWT signed with Django SECRET_KEY
- Google OAuth uses PKCE flow
- Passwords are never transmitted for OAuth users
- Short-lived access tokens (1 hour)

⚠️ **Production Recommendations:**
- Use HTTPS for all OAuth flows
- Store credentials in environment variables or secret manager
- Implement rate limiting
- Add logging for security events
- Regularly rotate Django SECRET_KEY
