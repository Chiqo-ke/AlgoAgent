# Key Rotation Integration Guide

This guide explains how to set up and use the API key rotation system in the monolithic agent.

## Overview

The key rotation system enables:
- **Load distribution** across multiple API keys
- **Automatic failover** when a key hits rate limits
- **Health tracking** with cooldown for problematic keys
- **Flexible secret storage** (environment variables, Vault, AWS, Azure)
- **Rate limiting** with RPM/TPM tracking

## Quick Start

### 1. Simple Setup (Single Key)

For development, use a single API key:

```bash
export GEMINI_API_KEY=your-api-key-here
```

The system will automatically use this key for all requests. **No configuration needed.**

### 2. Advanced Setup (Multi-Key Rotation)

For production, enable key rotation with multiple keys:

#### Step 1: Create keys.json

Copy the example file and add your keys:

```bash
cp keys_example.json keys.json
```

Edit `keys.json` to include your actual keys and their metadata:

```json
{
  "keys": [
    {
      "key_id": "flash_01",
      "model_name": "gemini-2.5-flash",
      "provider": "gemini",
      "rpm": 60,
      "tpm": 1000000,
      "rpd": 500,
      "active": true,
      "tags": {"region": "us-east", "workload": "light", "tier": "standard"},
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    },
    {
      "key_id": "flash_02",
      "model_name": "gemini-2.5-flash",
      "provider": "gemini",
      "rpm": 60,
      "tpm": 1000000,
      "rpd": 500,
      "active": true,
      "tags": {"region": "us-west", "workload": "light", "tier": "standard"},
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

#### Step 2: Configure Environment Variables

Add to your `.env` file:

```bash
# Enable key rotation
ENABLE_KEY_ROTATION=true

# Choose secret storage (env, vault, aws, azure)
SECRET_STORE_TYPE=env

# Provide keys (format: GEMINI_KEY_{key_id})
GEMINI_KEY_flash_01=your-api-key-1
GEMINI_KEY_flash_02=your-api-key-2

# Optional: Redis for rate limiting
REDIS_URL=redis://localhost:6379/0
```

#### Step 3: Set Up Redis (Optional)

For atomic rate limiting, install and run Redis:

```bash
# On macOS with Homebrew
brew install redis
brew services start redis

# On Windows with WSL
wsl
sudo apt-get install redis-server
sudo service redis-server start

# On Docker
docker run -d -p 6379:6379 redis:latest
```

#### Step 4: Use in Your Code

```python
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

# Automatically uses key rotation if enabled
generator = GeminiStrategyGenerator()

# Or explicitly enable/disable
generator = GeminiStrategyGenerator(use_key_rotation=True)

# Generate strategy (will automatically select best key)
code = generator.generate_strategy("Buy when RSI < 30, sell when RSI > 70")
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_KEY_ROTATION` | `false` | Enable multi-key rotation |
| `SECRET_STORE_TYPE` | `env` | Secret storage backend (env, vault, aws, azure) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `VAULT_ADDR` | - | HashiCorp Vault address (if using vault) |
| `VAULT_TOKEN` | - | Vault authentication token |
| `VAULT_SECRET_PATH` | `secret/algoagent` | Path to secrets in Vault |
| `AWS_REGION` | `us-east-1` | AWS region for Secrets Manager |
| `AWS_SECRET_PREFIX` | `algoagent/` | Prefix for secret names |
| `AZURE_VAULT_URL` | - | Azure Key Vault URL |

### Secret Storage Types

#### Environment Variables (Development)

Simplest option - secrets in `.env` file:

```bash
ENABLE_KEY_ROTATION=true
SECRET_STORE_TYPE=env
GEMINI_KEY_flash_01=sk-...
GEMINI_KEY_flash_02=sk-...
```

#### HashiCorp Vault (Production)

Secure, centralized secret management:

```bash
ENABLE_KEY_ROTATION=true
SECRET_STORE_TYPE=vault
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=s.xxxxxxxx
VAULT_SECRET_PATH=secret/algoagent
```

Store secrets in Vault:
```bash
vault kv put secret/algoagent/flash_01 value=sk-...
vault kv put secret/algoagent/flash_02 value=sk-...
```

#### AWS Secrets Manager (Production)

Cloud-native secrets management:

```bash
ENABLE_KEY_ROTATION=true
SECRET_STORE_TYPE=aws
AWS_REGION=us-east-1
AWS_SECRET_PREFIX=algoagent/
```

Create secrets:
```bash
aws secretsmanager create-secret --name algoagent/flash_01 --secret-string sk-...
aws secretsmanager create-secret --name algoagent/flash_02 --secret-string sk-...
```

#### Azure Key Vault (Production)

Azure's key management service:

```bash
ENABLE_KEY_ROTATION=true
SECRET_STORE_TYPE=azure
AZURE_VAULT_URL=https://your-vault.vault.azure.net/
```

Add secrets:
```bash
az keyvault secret set --vault-name your-vault --name flash_01 --value sk-...
az keyvault secret set --vault-name your-vault --name flash_02 --value sk-...
```

## Key Selection Algorithm

When generating a strategy, the system selects the best available key using:

1. **Filter by model**: If a model preference is specified
2. **Check cooldown**: Skip keys that are cooling down due to errors
3. **Check capacity**: Verify RPM/TPM limits (if Redis enabled)
4. **Load distribution**: Randomly shuffle to distribute load
5. **Fallback**: Try next key if selected one fails

## Health Tracking

Keys are automatically monitored for health:

```python
from Backtest.key_rotation import get_key_manager

manager = get_key_manager()

# Get health status of all keys
health = manager.get_health_status()

for key_id, status in health.items():
    print(f"{key_id}:")
    print(f"  Model: {status['model']}")
    print(f"  Active: {status['active']}")
    print(f"  Last Used: {status['last_used']}")
    print(f"  Success Count: {status['success_count']}")
    print(f"  Error Count: {status['error_count']}")
    print(f"  In Cooldown: {status['in_cooldown']}")
```

## Error Handling and Failover

If a key fails:

1. **Error is reported** to the key manager
2. **Cooldown is applied** (exponential backoff: 30s → 60s → 120s → ...)
3. **Next key is tried** automatically
4. **Request succeeds** with alternate key or fails if all keys exhausted

Example:

```python
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

try:
    generator = GeminiStrategyGenerator(use_key_rotation=True)
    code = generator.generate_strategy("...")
except Exception as e:
    print(f"Generation failed: {e}")
    # Check health status
    health = generator.key_manager.get_health_status()
    print("Key Status:")
    print(health)
```

## Rate Limiting

When Redis is available, the system tracks:

- **RPM (Requests Per Minute)**: Prevents exceeding API quota
- **TPM (Tokens Per Minute)**: Manages token consumption

Configure limits in `keys.json`:

```json
{
  "key_id": "flash_01",
  "rpm": 60,           // 60 requests per minute
  "tpm": 1000000,      // 1 million tokens per minute
  "rpd": 500           // 500 requests per day (optional)
}
```

## Migration Guide

### From Single Key to Multi-Key

1. **Keep existing setup working**: Single `GEMINI_API_KEY` still works
2. **Create keys.json**: Define your multiple keys
3. **Set environment variables**: Add keys with `GEMINI_KEY_{key_id}` format
4. **Enable rotation**: Set `ENABLE_KEY_ROTATION=true`
5. **Test**: Run your strategies and verify key rotation works

No code changes needed! The system automatically detects and uses the configuration.

### Rollback

If key rotation causes issues, simply:

1. Set `ENABLE_KEY_ROTATION=false` or remove from `.env`
2. Keep `GEMINI_API_KEY` set
3. System will use single key mode

## Troubleshooting

### "No API keys available for selection"

- Verify `ENABLE_KEY_ROTATION=true` in `.env`
- Check `keys.json` exists and has valid key entries
- Ensure environment variables have corresponding secrets (e.g., `GEMINI_KEY_flash_01`)

### Keys staying in cooldown

- Check error logs to see what's failing
- Verify API keys are valid and not rate limited at API provider
- Increase rate limits in `keys.json` if you know the API allows it
- Add more keys to distribute load

### Redis connection fails

- Ensure Redis is running: `redis-cli ping` should return PONG
- Check `REDIS_URL` is correct
- If Redis fails, system automatically disables rate limiting (fails open)
- Set `REDIS_URL=""` to explicitly disable Redis

### Secret not found

- Verify secret storage type matches configuration
- For environment: Check `GEMINI_KEY_{key_id}` variables are set
- For Vault: Run `vault kv get secret/algoagent/{key_id}`
- For AWS: Check `aws secretsmanager get-secret-value --secret-id algoagent/{key_id}`
- For Azure: Check `az keyvault secret show --name {key_id}`

## Examples

### Example 1: Generate strategy with auto key rotation

```python
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

# Automatically uses key rotation if ENABLE_KEY_ROTATION=true
generator = GeminiStrategyGenerator()

code = generator.generate_strategy(
    description="RSI-based strategy: Buy when RSI < 30, sell when RSI > 70"
)
```

### Example 2: Check key health and select manually

```python
from Backtest.key_rotation import get_key_manager

manager = get_key_manager()

# Check health of all keys
health = manager.get_health_status()
healthy_keys = [k for k, v in health.items() if not v['in_cooldown']]

print(f"Healthy keys: {healthy_keys}")

# Select a key explicitly
key_info = manager.select_key(
    model_preference='gemini-2.5-flash',
    tokens_needed=1000
)

if key_info:
    print(f"Selected key: {key_info['key_id']}")
    print(f"Secret: {key_info['secret'][:10]}...")
```

### Example 3: Save and load key metadata

```python
from Backtest.key_rotation import get_key_manager

manager = get_key_manager()

# Add a new key programmatically
from Backtest.key_rotation import APIKeyMetadata

new_key = APIKeyMetadata(
    key_id='flash_03',
    model_name='gemini-2.5-flash',
    provider='gemini',
    rpm=60,
    tpm=1000000,
    tags={'region': 'eu-west'}
)

manager.keys['flash_03'] = new_key
manager.save_keys()
```

## Performance Tips

1. **Distribute load**: Create multiple keys and set up proper rate limits
2. **Monitor keys**: Regularly check health status
3. **Use Redis**: Enables atomic rate limiting for accurate tracking
4. **Cache metadata**: Key metadata is loaded once at startup
5. **Handle failures**: Implement retry logic with exponential backoff

## Security Best Practices

1. **Never commit secrets**: Keep API keys in `.env` or secure vault
2. **Rotate periodically**: Change keys every 90 days
3. **Use separate keys**: One key per service/environment
4. **Monitor usage**: Track requests and tokens
5. **Limit permissions**: If possible, restrict keys to specific APIs
6. **Use Vault/AWS/Azure**: For production deployments

## See Also

- `.env.example` - Environment configuration template
- `keys_example.json` - Key metadata example
- `Backtest/key_rotation.py` - Implementation details
- `Backtest/gemini_strategy_generator.py` - Integration with strategy generation
