# Configuration Reference

**Last Updated:** March 10, 2026
**See also:** [Architecture](architecture/ARCHITECTURE.md) | [Data Models](DATA_MODELS.md) | [AI Pipeline](AI_PIPELINE.md)

---

## Project Layout

```
AlgoAgent/
    .env                          <-- your local secrets (gitignored)
    .env.example                  <-- template, committed to repo
    monolithic_agent/
        algoagent_api/
            settings.py           <-- all Django settings
        manage.py
        db.sqlite3                <-- dev database (gitignored)
        logs/
            django.log            <-- rotating, max 10 MB × 3 files
            frontend_errors.log   <-- rotating, max 5 MB × 5 files
```

---

## Environment Variables

Place these in `AlgoAgent/.env` (one directory above `monolithic_agent/`). Settings are loaded at startup via `python-dotenv`.

### Required

| Variable | Example | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `django-insecure-...` | Django's signing key — use a random 50-char string in production |
| `GEMINI_API_KEY` | `AIzaSy...` | Google Gemini API key for strategy generation |
| `GOOGLE_OAUTH_CLIENT_ID` | `123-abc.apps.googleusercontent.com` | Google Cloud Console OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | `GOCSPX-...` | Google Cloud Console OAuth secret |

### Optional / Overrides

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | See settings.py | Comma-separated host list |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Redis URL for Celery task queue |
| `LLM_BACKEND` | `copilot` | LLM backend: `copilot` or `gemini` |
| `GITHUB_COPILOT_CLIENT_ID` | (empty) | Optional custom OAuth client ID for GitHub Copilot |
| `GITHUB_TOKEN` | (empty) | Pre-authenticated GitHub token for headless deployments |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL when key rotation is enabled |
| `REDIS_TIMEOUT` | `5` | Redis connection timeout in seconds |
| `ENABLE_KEY_ROTATION` | `false` | Enable multi-key Gemini rotation (requires Redis) |
| `SECRET_STORE_TYPE` | `env` | Where multi-keys are stored: `env`, `vault`, `aws`, `azure` |

### Multi-Key Gemini (advanced, `ENABLE_KEY_ROTATION=true`)

| Variable | Description |
|----------|-------------|
| `GEMINI_KEY_flash_01` | First Flash-tier Gemini key |
| `GEMINI_KEY_flash_02` | Second Flash-tier Gemini key |
| `GEMINI_KEY_pro_01` | First Pro-tier Gemini key |

Key IDs must match entries in the key registry. See `.env.example` for the full pattern.

---

## Django Settings

Settings file: `monolithic_agent/algoagent_api/settings.py`

### Core

| Setting | Dev value | Production note |
|---------|-----------|-----------------|
| `DEBUG` | `True` | Must be `False` |
| `SECRET_KEY` | Hard-coded insecure key | Generate a new key |
| `ALLOWED_HOSTS` | `localhost`, `127.0.0.1`, `chiqoke254.pythonanywhere.com`, `*.algoai.biz`, VPS IP | Add your domain |
| `DEFAULT_AUTO_FIELD` | `BigAutoField` | |
| `TIME_ZONE` | `UTC` | |
| `SITE_ID` | `1` | Required by `django-allauth` |

---

### CORS

| Setting | Value |
|---------|-------|
| `CORS_ALLOW_CREDENTIALS` | `True` |
| `CORS_ALLOW_METHODS` | `DELETE, GET, OPTIONS, PATCH, POST, PUT` |
| `CORS_ALLOW_HEADERS` | Standard headers + `x-api-key` |

**`CORS_ALLOWED_ORIGINS`** (full list):

```
http://localhost:3000
http://127.0.0.1:3000
http://localhost:8080
http://127.0.0.1:8080
http://localhost:8081          # standard local frontend
http://127.0.0.1:8081
http://localhost:5173          # Vite default
http://127.0.0.1:5173
http://localhost:5174          # Vite fallback
http://127.0.0.1:5174
https://algo-rho.vercel.app    # Vercel production
https://www.algoai.biz
https://algoai.biz
https://api.algoai.biz
http://chiqoke254.pythonanywhere.com
https://ps283t0p-8000.uks1.devtunnels.ms
```

To add a new origin add it to `CORS_ALLOWED_ORIGINS` in `settings.py` and to `CSRF_TRUSTED_ORIGINS` if it serves HTTPS.

---

### JWT (`SIMPLE_JWT`)

| Setting | Value | Description |
|---------|-------|-------------|
| `ACCESS_TOKEN_LIFETIME` | `1 hour` | Tokens expire after 1 hour |
| `REFRESH_TOKEN_LIFETIME` | `7 days` | Refresh tokens last 7 days |
| `ROTATE_REFRESH_TOKENS` | `True` | Each refresh call returns a new refresh token |
| `BLACKLIST_AFTER_ROTATION` | `True` | Old refresh token is invalidated |
| `UPDATE_LAST_LOGIN` | `True` | Updates `User.last_login` on token refresh |
| `ALGORITHM` | `HS256` | |
| `ISSUER` | `algoagent-api` | JWT `iss` claim |
| `AUTH_HEADER_TYPES` | `Bearer` | Use `Authorization: Bearer <token>` |

---

### Database

**Development (default):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Production (PostgreSQL):** comment out the SQLite block and uncomment:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'algoagent_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

### Celery

| Setting | Value | Description |
|---------|-------|-------------|
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Overrideable via env var |
| `CELERY_RESULT_BACKEND` | `django-db` | Results stored in `django_celery_results` table |
| `CELERY_TASK_SERIALIZER` | `json` | |
| `CELERY_RESULT_SERIALIZER` | `json` | |
| `CELERY_ACCEPT_CONTENT` | `['json']` | |
| `CELERY_TASK_TRACK_STARTED` | `True` | Enables `STARTED` state for progress polling |
| `CELERY_TASK_TIME_LIMIT` | `1800` | Hard kill at 30 minutes |
| `CELERY_TASK_SOFT_TIME_LIMIT` | `1500` | `SoftTimeLimitExceeded` raised at 25 minutes |

---

### Django Channels

**Development (no Redis):**
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
```

**Production (Redis):**
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    }
}
```

Also uncomment `'daphne'` and `'channels'` in `INSTALLED_APPS` and switch `runserver` to Daphne for production:
```bash
daphne -b 0.0.0.0 -p 8000 algoagent_api.asgi:application
```

---

### Google OAuth

| Setting | Value |
|---------|-------|
| `SITE_ID` | `1` |
| `SOCIALACCOUNT_AUTO_SIGNUP` | `True` — creates a user account on first OAuth login |
| `ACCOUNT_EMAIL_VERIFICATION` | `none` |
| `ACCOUNT_LOGIN_METHODS` | `{'username'}` |
| OAuth scopes | `profile`, `email` |
| Client ID source | `os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')` |
| Client secret source | `os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')` |

To set up Google OAuth:
1. Create a project in Google Cloud Console
2. Create an OAuth 2.0 Client ID (Web application)
3. Add redirect URI: `https://yourdomain.com/accounts/google/login/callback/`
4. Set `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` in `.env`
5. Add a `SocialApp` record in Django admin (or via `manage.py` shell) pointing to the `google` provider

---

### REST Framework

| Setting | Value |
|---------|-------|
| Default authentication | `JWTAuthentication`, `SessionAuthentication` |
| Default permission | `AllowAny` (individual views override with `IsAuthenticated`) |
| Pagination | `PageNumberPagination`, `PAGE_SIZE=50` |
| Renderers | JSON, Browsable API |

---

### Logging

| Logger | Handlers | Level |
|--------|----------|-------|
| `frontend` | console, `logs/frontend_errors.log` | DEBUG |
| `django` | console, `logs/django.log` | WARNING |
| `django.request` | console, `logs/django.log` | ERROR |

Log files rotate automatically:
- `logs/frontend_errors.log` — max 5 MB, 5 backups
- `logs/django.log` — max 10 MB, 3 backups

---

## Local Development Startup

### Prerequisites

- Python 3.11+
- Redis running on `localhost:6379`
- `.env` file populated (copy from `.env.example`)

### First-time setup

```powershell
# From AlgoAgent/monolithic_agent/
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

### Running all services

**Terminal 1 — Django (HTTP):**
```powershell
cd AlgoAgent/monolithic_agent
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 — Celery worker:**
```powershell
cd AlgoAgent/monolithic_agent
celery -A algoagent_api worker --loglevel=info
```

**Terminal 3 — Daphne (WebSocket, optional in dev):**
```powershell
cd AlgoAgent/monolithic_agent
daphne -b 0.0.0.0 -p 8001 algoagent_api.asgi:application
```

**Terminal 4 — Redis (if not running as a service):**
```powershell
redis-server
```

### Verify services

```powershell
# Django health check
Invoke-RestMethod http://localhost:8000/api/auth/health/

# Strategy API health
Invoke-RestMethod http://localhost:8000/api/strategies/health/

# Celery (check workers are registered)
celery -A algoagent_api inspect active
```

---

## Production Deployment Notes

| Concern | Action |
|---------|--------|
| `DEBUG=False` | Set in `.env` |
| `SECRET_KEY` | Generate and store securely |
| Static files | Run `python manage.py collectstatic` |
| Database | Switch to PostgreSQL (see above) |
| HTTPS | Terminate at nginx; set `SECURE_PROXY_SSL_HEADER` (already configured) |
| Channel layer | Switch to `channels_redis` (see above) |
| ALLOWED_HOSTS | Add your production domain |
| CORS | Add your production frontend origin |

Current production backend: `chiqoke254.pythonanywhere.com`
Current production frontend: `algo-rho.vercel.app` / `*.algoai.biz`
