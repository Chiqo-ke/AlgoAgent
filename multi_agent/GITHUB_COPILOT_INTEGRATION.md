# GitHub Copilot Integration - Multi-Agent System

## Overview

The multi-agent system now uses **GitHub Copilot API** (same as the monolithic system) instead of GitHub Models API. This provides access to enterprise-grade AI models through OAuth authentication.

## Key Differences: Copilot API vs Models API

| Feature | GitHub Copilot API | GitHub Models API |
|---------|-------------------|-------------------|
| **Endpoint** | `https://api.githubcopilot.com/chat/completions` | `https://models.inference.ai.azure.com` |
| **Authentication** | OAuth device flow (`read:user` scope) | Personal Access Token (`models` scope) |
| **OAuth Client ID** | `Ov23li8tweQw6odWQebz` (from OpenCode) | Not supported |
| **Models** | `claude-sonnet-4.5`, `gpt-5.2-codex`, `gpt-5.1-codex`, `claude-opus-4.5` | `gpt-4o`, `gpt-4o-mini`, `Phi-4`, `o1-mini` |
| **Rate Limits** | Higher (60 RPM, 200k TPM) | Lower (15 RPM, 150k TPM) |
| **Subscription** | Requires GitHub Copilot subscription | Free for limited use |

## Authentication Flow

### 1. Device Flow Setup

Run the authentication script:

```powershell
cd C:\Users\nyaga\Documents\AlgoAgent\multi_agent
C:/Users/nyaga/Documents/.venv/Scripts/python.exe scripts/github_device_auth.py
```

### 2. Follow Instructions

The script will:
1. Request a device code from GitHub
2. Display a verification URL (`https://github.com/login/device`)
3. Show you a user code (e.g., `ABCD-1234`)
4. Wait for you to authorize the app

### 3. Complete Authorization

1. Visit the verification URL
2. Enter the displayed code
3. Authorize "OpenCode GitHub OAuth App"
4. Return to the terminal

### 4. Token Storage

The token is automatically:
- Saved to [.env](AlgoAgent/multi_agent/.env) as `API_KEY_github-copilot-01`
- Tested against Copilot API
- Verified for correct scopes

## Configuration

### keys.json

Three GitHub Copilot keys are configured:

```json
{
  "key_id": "github-copilot-01",
  "provider": "github-copilot",
  "model_name": "claude-sonnet-4.5",
  "priority": 1
}
```

**Available models:**
- `claude-sonnet-4.5` (Best for code generation, priority 1)
- `gpt-5.2-codex` (GPT-5 Codex, priority 2)
- `gpt-5.1-codex` (GPT-5.1 Codex, priority 3)
- `claude-opus-4.5` (Claude Opus, available on request)

### .env

Token format:
```bash
API_KEY_github-copilot-01=ghu_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
API_KEY_github-copilot-02=ghu_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
API_KEY_github-copilot-03=ghu_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Implementation Details

### Provider Class: GitHubCopilotClient

Location: [llm/providers.py](AlgoAgent/multi_agent/llm/providers.py)

```python
class GitHubCopilotClient(ProviderClient):
    """
    GitHub Copilot API client.
    
    Endpoint: https://api.githubcopilot.com/chat/completions
    Auth: OAuth Bearer token
    """
```

**Key features:**
- Direct HTTP requests (requests library)
- Custom headers for Copilot API:
  - `X-Initiator: user`
  - `Openai-Intent: conversation-edits`
- Automatic rate limit handling
- OAuth token refresh support

### Request Format

```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "User-Agent": "AlgoAgent-MultiAgent/1.0",
    "X-Initiator": "user",
    "Openai-Intent": "conversation-edits"
}

payload = {
    "model": "claude-sonnet-4.5",
    "messages": [{"role": "user", "content": "..."}],
    "stream": False,
    "temperature": 0.7,
    "max_tokens": 8000
}
```

## Disabled Features

### OpenCode Providers

All OpenCode providers are now disabled:
- `opencode-claude-01` → Priority 10, `active: false`
- `opencode-gpt4o-01` → Priority 10, `active: false`
- `opencode-gemini-01` → Priority 10, `active: false`

**Reason:** Replaced by GitHub Copilot for direct API access.

### Gemini Key Rotation

Gemini-specific features like key rotation are bypassed when using Copilot.

## Testing

### Run Authentication Test

```powershell
cd C:\Users\nyaga\Documents\AlgoAgent\multi_agent
C:/Users/nyaga/Documents/.venv/Scripts/python.exe scripts/github_device_auth.py
```

### Manual Token Test

```python
import requests

response = requests.post(
    "https://api.githubcopilot.com/chat/completions",
    headers={
        "Authorization": f"Bearer {YOUR_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "AlgoAgent-MultiAgent/1.0",
        "X-Initiator": "user",
        "Openai-Intent": "conversation-edits"
    },
    json={
        "model": "claude-sonnet-4.5",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": False,
        "temperature": 0.5,
        "max_tokens": 100
    }
)

print(response.json())
```

## Troubleshooting

### "Invalid OAuth token"

**Cause:** Token expired or revoked.

**Solution:** Re-run authentication:
```powershell
python scripts/github_device_auth.py
```

### "No Copilot subscription"

**Cause:** Your GitHub account doesn't have Copilot access.

**Solution:** 
1. Subscribe at https://github.com/settings/copilot
2. Or use a different GitHub account with Copilot

### "Rate limit exceeded"

**Cause:** Too many requests.

**Solution:** System automatically retries with exponential backoff. Check [keys.json](AlgoAgent/multi_agent/keys.json) rate limits (60 RPM).

## Migration from Monolithic System

The multi-agent system now uses the **exact same authentication** as the monolithic system:

| Feature | Monolithic | Multi-Agent |
|---------|-----------|-------------|
| OAuth Client ID | `Ov23li8tweQw6odWQebz` | ✅ Same |
| Scope | `read:user` | ✅ Same |
| Endpoint | `api.githubcopilot.com` | ✅ Same |
| Models | `claude-sonnet-4.5` | ✅ Same |
| Auth Flow | Device flow | ✅ Same |

## References

- **Monolithic System Auth:** [algoagent_api/copilot_auth.py](AlgoAgent/monolithic_agent/algoagent_api/copilot_auth.py)
- **Monolithic System Generator:** [Backtest/copilot_strategy_generator.py](AlgoAgent/monolithic_agent/Backtest/copilot_strategy_generator.py)
- **Multi-Agent Provider:** [llm/providers.py](AlgoAgent/multi_agent/llm/providers.py)
- **OAuth Setup Script:** [scripts/github_device_auth.py](AlgoAgent/multi_agent/scripts/github_device_auth.py)

---

**Last Updated:** February 10, 2026  
**Status:** ✅ Functional - matching monolithic system implementation
