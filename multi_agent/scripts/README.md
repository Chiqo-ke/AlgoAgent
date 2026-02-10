# GitHub Device Flow Authentication

Easy authentication for GitHub Models using device flow.

## Quick Start

```bash
python scripts/github_device_auth.py
```

Follow the prompts:
1. 🌐 Visit: https://github.com/login/device
2. 📝 Enter the displayed code
3. ✅ Click "Authorize"
4. 🎉 Token automatically saved!

## What It Does

The script:
1. Requests a device code from GitHub
2. Displays a user code and verification URL
3. Waits for you to authorize via browser
4. Polls GitHub for the access token
5. Saves token to `.env` file
6. Verifies token works with GitHub Models API

## Features

- ✅ **No manual token creation** - device flow handles everything
- ✅ **Automatic verification** - tests token after saving
- ✅ **Smart polling** - handles rate limits and timeouts
- ✅ **Multiple tokens** - run multiple times for key rotation
- ✅ **Error handling** - clear error messages and retry guidance

## Usage

### Basic Authentication

```bash
python scripts/github_device_auth.py
```

When prompted, enter a key ID (or press Enter for default `github-models-01`).

### Key Rotation

For higher throughput, authenticate multiple times:

```bash
# First token
python scripts/github_device_auth.py
# Enter: github-models-01

# Second token (same GitHub account is fine)
python scripts/github_device_auth.py
# Enter: github-models-02

# Third token
python scripts/github_device_auth.py
# Enter: github-models-03
```

Then configure all keys in `keys.json`.

## How Device Flow Works

```
┌──────────┐                 ┌────────┐                 ┌─────────┐
│  Script  │                 │ GitHub │                 │   You   │
└────┬─────┘                 └───┬────┘                 └────┬────┘
     │                           │                           │
     │ 1. Request device code    │                           │
     │──────────────────────────>│                           │
     │                           │                           │
     │ 2. Return device code     │                           │
     │   & user code (ABC-123)   │                           │
     │<──────────────────────────│                           │
     │                           │                           │
     │ 3. Display code           │                           │
     │──────────────────────────────────────────────────────>│
     │   "Visit github.com/login/device"                     │
     │   "Enter code: ABC-123"                               │
     │                           │                           │
     │                           │ 4. Visit URL, enter code  │
     │                           │<──────────────────────────│
     │                           │                           │
     │                           │ 5. Authorize app          │
     │                           │<──────────────────────────│
     │                           │                           │
     │ 6. Poll for token         │                           │
     │──────────────────────────>│                           │
     │                           │                           │
     │ 7. Return access token    │                           │
     │<──────────────────────────│                           │
     │                           │                           │
     │ 8. Save to .env           │                           │
     │ 9. Verify token           │                           │
     │                           │                           │
```

## Configuration

### Environment Variables

The script automatically manages these in `.env`:

```bash
API_KEY_github-models-01=ghu_xxxxxxxxxxxxxxxxxxxx
API_KEY_github-models-02=ghu_xxxxxxxxxxxxxxxxxxxx
API_KEY_github-models-03=ghu_xxxxxxxxxxxxxxxxxxxx
```

### Keys Configuration

Add corresponding entries to `keys.json`:

```json
{
  "keys": [
    {
      "key_id": "github-models-01",
      "model_name": "gpt-4o-mini",
      "provider": "github-models",
      "rpm": 15,
      "tpm": 150000,
      "rpd": 150,
      "active": true,
      "tags": {
        "workload": "medium",
        "priority": 1
      }
    }
  ]
}
```

## Troubleshooting

### Code Expired

**Error:** "Device code expired. Please try again."

**Solution:** Codes expire after 15 minutes. Run the script again and complete authorization faster.

### Authorization Denied

**Error:** "Authorization denied by user."

**Solution:** You clicked "Cancel" on GitHub. Run the script again and click "Authorize".

### Slow Down

**Warning:** "Slowing down polling rate..."

**Explanation:** GitHub rate-limited the polling. The script automatically adjusts. Just wait.

### Token Verification Failed

**Warning:** "Token saved but verification failed"

**Possible causes:**
- GitHub Models API is down (check https://www.githubstatus.com/)
- Rate limits hit immediately (wait and try a test request later)
- Network issues

**Solution:** Token is still saved. Try testing manually:

```python
from llm.router import RequestRouter
router = RequestRouter()
response = router.send_one_shot(
    prompt="test", 
    model_preference="gpt-4o-mini"
)
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
pip install requests
```

## Technical Details

### OAuth Client ID

The script uses GitHub's public OAuth client ID for device flow:
```python
GITHUB_CLIENT_ID = "Iv1.b507a08c87ecfe98"
```

This is a public value and safe to commit to version control.

### Scopes

Required scope: `models`

This gives access to GitHub Models API without exposing other permissions.

### Token Format

- **Device flow tokens:** Start with `ghu_`
- **PATs:** Start with `github_pat_` or `ghp_`

Both work with GitHub Models API.

### Rate Limits

Device flow polling:
- Default interval: 5 seconds
- Adjusts automatically if GitHub requests slowdown
- Timeout: 15 minutes (code expiration)

## Security

✅ **No credentials stored in code** - uses standard OAuth flow  
✅ **Tokens saved to .env** - which should be in `.gitignore`  
✅ **Minimal permissions** - only `models` scope  
✅ **Token verification** - ensures token works before saving  

## Alternative: Manual PAT Creation

If device flow doesn't work (e.g., no browser access), create a PAT manually:

1. Go to https://github.com/settings/tokens
2. Create token with `models` permission
3. Add to `.env`:
   ```bash
   API_KEY_github-models-01=github_pat_YOUR_TOKEN
   ```

## Support

For issues:
1. Check error message carefully
2. Verify `.env` file format
3. Test token manually with GitHub Models API
4. Check GitHub status: https://www.githubstatus.com/

## See Also

- [GITHUB_MODELS_QUICKSTART.md](../GITHUB_MODELS_QUICKSTART.md) - Full setup guide
- [GITHUB_MODELS_MIGRATION.md](../GITHUB_MODELS_MIGRATION.md) - Migration from Gemini
- [GitHub Device Flow Docs](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow)
