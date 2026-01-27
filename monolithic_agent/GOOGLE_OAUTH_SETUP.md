# Google OAuth Setup Guide for AlgoAgent

This guide will help you set up Google OAuth authentication for your AlgoAgent application.

## Prerequisites

- A Google Cloud account
- Access to Google Cloud Console
- Your Django backend running on `http://localhost:8000` or your production URL

## Step 1: Create Google OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create or Select a Project**
   - Click on the project dropdown at the top
   - Create a new project or select an existing one

3. **Enable Google+ API**
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen first:
     - User Type: External (for public apps) or Internal (for workspace-only)
     - App name: "AlgoAgent" or your app name
     - User support email: Your email
     - Developer contact: Your email
     - Save and continue through the scopes (use default)
     - Add test users if using External with testing status

5. **Configure OAuth Client**
   - Application type: "Web application"
   - Name: "AlgoAgent Web Client"
   - Authorized JavaScript origins:
     ```
     http://localhost:5173
     http://127.0.0.1:5173
     https://your-production-domain.com
     ```
   - Authorized redirect URIs:
     ```
     http://localhost:5173/auth/callback
     http://127.0.0.1:5173/auth/callback
     https://your-production-domain.com/auth/callback
     ```
   - Click "Create"

6. **Save Your Credentials**
   - You'll see your Client ID and Client Secret
   - **IMPORTANT**: Save these securely - you'll need them next

## Step 2: Configure Backend Environment

1. **Update your `.env` file** in `AlgoAgent/monolithic_agent/`:

   ```bash
   # Google OAuth Configuration
   GOOGLE_OAUTH_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
   ```

2. **Install Required Packages**:

   ```bash
   cd AlgoAgent/monolithic_agent
   pip install django-allauth requests
   ```

   Or use the updated requirements.txt:

   ```bash
   pip install -r requirements.txt
   ```

## Step 3: Run Database Migrations

The Google OAuth setup requires django-allauth tables:

```bash
python manage.py migrate
```

## Step 4: Create a Site Object (One-time setup)

Django allauth requires a Site object:

```bash
python manage.py shell
```

Then run:

```python
from django.contrib.sites.models import Site

# Update or create the default site
site = Site.objects.get_or_create(id=1)[0]
site.domain = 'localhost:8000'  # or your production domain
site.name = 'AlgoAgent'
site.save()

exit()
```

## Step 5: Test the Integration

1. **Start your Django backend**:
   ```bash
   python manage.py runserver
   ```

2. **Start your frontend** (in the Algo directory):
   ```bash
   npm run dev
   ```

3. **Test the Login Flow**:
   - Navigate to `http://localhost:5173/login`
   - Click "Continue with Google"
   - You should be redirected to Google's consent screen
   - After authorizing, you'll be redirected back and logged in

## API Endpoints Created

- **`GET /api/auth/google/`** - Initiates Google OAuth flow
  - Query params: `redirect_uri` (required)
  - Redirects to Google consent screen

- **`POST /api/auth/google/callback/`** - Handles OAuth callback
  - Body: `{ "code": "...", "redirect_uri": "..." }`
  - Returns: `{ "access": "...", "refresh": "...", "user": {...} }`

## How It Works

1. User clicks "Continue with Google" on frontend
2. Frontend redirects to `/api/auth/google/?redirect_uri=http://localhost:5173/auth/callback`
3. Backend redirects to Google OAuth consent screen
4. User authorizes the app
5. Google redirects to frontend callback URL with authorization code
6. Frontend sends code to `/api/auth/google/callback/`
7. Backend exchanges code for Google access token
8. Backend gets user info from Google
9. Backend creates/retrieves Django user
10. Backend generates JWT tokens
11. Frontend stores tokens and redirects to dashboard

## Troubleshooting

### "Redirect URI mismatch" Error
- Ensure the redirect URI in Google Console exactly matches the one sent by your app
- Check for trailing slashes - they matter!
- Make sure you've added both `http://localhost:5173/auth/callback` and `http://127.0.0.1:5173/auth/callback`

### "Google OAuth not configured" Error
- Check that `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` are set in `.env`
- Restart your Django server after updating `.env`

### "Site matching query does not exist" Error
- Run the Site creation script in Step 4

### CORS Errors
- Ensure your frontend URL is in `CORS_ALLOWED_ORIGINS` in `settings.py`

## Security Notes

⚠️ **Important Security Practices**:

1. **Never commit your `.env` file** - it contains sensitive credentials
2. **Use environment variables** in production (don't hardcode credentials)
3. **Use HTTPS in production** - OAuth requires secure connections
4. **Restrict your OAuth redirect URIs** - only add trusted domains
5. **Regularly rotate your client secret** if compromised
6. **Set up proper OAuth consent screen** before going public

## Production Deployment

When deploying to production:

1. Update authorized origins and redirect URIs in Google Console
2. Use your production domain URLs
3. Set `DEBUG=False` in Django settings
4. Use environment variables (not `.env` file) for credentials
5. Consider using Google Cloud Secret Manager or similar for credentials

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Django Allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google Cloud Console](https://console.cloud.google.com/)
