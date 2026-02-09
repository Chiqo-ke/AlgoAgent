# GitHub Models Setup - Quick Guide

## ⚠️ Important: Device Flow Limitation

The OAuth device flow **cannot access the `models` scope** required for GitHub Models API. You must use a Personal Access Token (PAT) instead.

## Setup Steps (5 minutes)

### 1. Create GitHub Personal Access Token

1. **Visit**: https://github.com/settings/tokens/new
2. **Token name**: `AlgoAgent LLM Access`
3. **Expiration**: Choose your preference (90 days recommended)
4. **Select scopes**:
   - ✅ **`models`** (under "Resource permissions")
5. **Click**: "Generate token"
6. **Copy the token** (starts with `github_pat_`)

### 2. Add Token to .env

Open `AlgoAgent/multi_agent/.env` and add:

```bash
API_KEY_github-models-01=github_pat_YOUR_TOKEN_HERE
```

### 3. Verify Configuration

Your `keys.json` is already configured:
```json
{
  "key_id": "github-models-01",
  "provider": "github-models",
  "model_name": "gpt-4o-mini",
  "active": true
}
```

### 4. Test It

```bash
cd AlgoAgent/multi_agent
python -c "from llm.request_router import RequestRouter; r = RequestRouter(); print(r.send_one_shot(prompt='Say hello!', model_preference='gpt-4o-mini'))"
```

## ✅ Redis is Running

Redis container is already started and ready.

## Available Models

- **gpt-4o-mini** - Fast, efficient (recommended)
- **gpt-4o** - Full capabilities 
- **Phi-4** - Lightweight tasks

All models have:
- **15 RPM** (requests per minute)
- **150 RPD** (requests per day)
- **150K TPM** (tokens per minute)

## Troubleshooting

### Token Verification Failed
- Make sure you selected the **`models`** scope (not `read:org`)
- The token must start with `github_pat_`

### Redis Connection Error
```bash
# Check if running:
docker ps

# Start if needed:
docker start redis-llm

# Or create new:
docker run -d --name redis-llm -p 6379:6379 redis:latest
```

### No Keys Available
- Ensure `API_KEY_github-models-01` exists in `.env`
- Verify `keys.json` has `"active": true` for the key

## Next Steps

Once setup is complete, yourworkflows will use GitHub Models (Copilot) automatically with key rotation and rate limiting.
