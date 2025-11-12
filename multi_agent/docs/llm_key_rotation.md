# LLM Key Rotation and Multi-Key Management

## Overview

This system provides intelligent API key management with:
- **Multi-key rotation** - Multiple API keys per model with automatic failover
- **RPM/TPM enforcement** - Redis-backed atomic rate limiting
- **Conversation persistence** - Independent conversation state across key rotations
- **Health monitoring** - Automatic cooldown for rate-limited keys
- **Security** - Secrets stored in external vaults, never in code or artifacts

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│   (Orchestrator, Coder Agent, Debugger Agent, etc.)    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   RequestRouter                          │
│  - Token estimation                                      │
│  - Conversation management                               │
│  - Retry logic with backoff                             │
└────────────┬────────────────────────────┬────────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌───────────────────────────┐
│     KeyManager         │   │   ConversationStore       │
│ - Key selection        │   │ - History management      │
│ - Health tracking      │   │ - Redis-backed           │
│ - Cooldown mgmt       │   │ - Cross-key persistence   │
└────────┬───────────────┘   └───────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                Redis Rate Limiter                        │
│ - Atomic RPM/TPM reservations (Lua scripts)             │
│ - Per-key windowed counters                             │
│ - Cooldown tracking                                     │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
cd multi_agent
pip install -r requirements_llm.txt
```

### 2. Configure Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or use existing Redis
export REDIS_URL="redis://localhost:6379/0"
```

### 3. Configure Secret Storage

**Option A: Environment Variables (Development)**
```bash
export SECRET_STORE_TYPE=env
export API_KEY_GEMINI_FLASH_01=AIza...your-key...
export API_KEY_GEMINI_PRO_01=AIza...your-key...
```

**Option B: HashiCorp Vault (Production)**
```bash
export SECRET_STORE_TYPE=vault
export VAULT_ADDR=https://vault.example.com
export VAULT_TOKEN=your-token
export VAULT_SECRET_PATH=secret/llm

# Store secrets in Vault
vault kv put secret/llm/gemini-flash-01 api_key=AIza...
vault kv put secret/llm/gemini-pro-01 api_key=AIza...
```

**Option C: AWS Secrets Manager**
```bash
export SECRET_STORE_TYPE=aws
export AWS_REGION=us-east-1
export AWS_SECRET_PREFIX=llm/

# Store secrets in AWS
aws secretsmanager create-secret \
  --name llm/gemini-flash-01 \
  --secret-string '{"api_key":"AIza..."}'
```

### 4. Add API Keys

Create `keys.json`:

```json
{
  "keys": [
    {
      "key_id": "gemini-flash-01",
      "model_name": "gemini-2.5-flash",
      "provider": "gemini",
      "rpm": 10,
      "tpm": 250000,
      "rpd": 1500,
      "active": true,
      "tags": {"tier": "free", "pool": "flash"}
    },
    {
      "key_id": "gemini-flash-02",
      "model_name": "gemini-2.5-flash",
      "provider": "gemini",
      "rpm": 10,
      "tpm": 250000,
      "active": true,
      "tags": {"tier": "free", "pool": "flash"}
    },
    {
      "key_id": "gemini-pro-01",
      "model_name": "gemini-2.5-pro",
      "provider": "gemini",
      "rpm": 5,
      "tpm": 100000,
      "rpd": 50,
      "active": true,
      "tags": {"tier": "free", "pool": "pro"}
    }
  ]
}
```

### 5. Initialize and Test

```python
from pathlib import Path
from keys.manager import get_key_manager
from llm.router import get_request_router

# Initialize
key_store_path = Path("keys.json")
key_manager = get_key_manager(key_store_path=key_store_path)
router = get_request_router(key_manager=key_manager)

# Health check
health = router.health_check()
print(f"System healthy: {health['healthy']}")

# Send test message
response = router.send_one_shot(
    prompt="Hello! Can you confirm you received this message?",
    model_preference="gemini-2.5-flash"
)

print(f"Response: {response['content']}")
print(f"Model: {response['model']}")
print(f"Tokens: {response['tokens']}")
```

## Usage in Agents

### Orchestrator Example

```python
from llm.router import get_request_router

router = get_request_router()

# Start conversation
conv_id = f"orchestrator_{workflow_id}"

# Send task planning request
response = router.send_chat(
    conv_id=conv_id,
    prompt=f"Plan tasks for: {user_request}",
    model_preference="gemini-2.5-pro",  # Use Pro for planning
    expected_completion_tokens=2048,
    system_prompt="You are an expert task planner..."
)

if response['success']:
    task_plan = response['content']
    # Process task plan...
else:
    logger.error(f"Planning failed: {response['error']}")
```

### Coder Agent Example

```python
from llm.router import get_request_router

router = get_request_router()

# Generate code
response = router.send_one_shot(
    prompt=f"Generate Python strategy code:\n{contract}",
    model_preference="gemini-2.5-pro",  # Use Pro for code
    expected_completion_tokens=4096,
    temperature=0.3,  # Lower temp for code
    system_prompt="You are an expert Python developer..."
)

if response['success']:
    code = response['content']
    # Save code...
else:
    if response.get('error_type') == 'rate_limited':
        # Queue for retry
        queue_for_retry(contract)
    else:
        # Handle error
        logger.error(f"Code generation failed: {response['error']}")
```

### Debugger Agent Example

```python
from llm.router import get_request_router

router = get_request_router()

# Analyze failure with conversation context
conv_id = f"debug_{task_id}"

response = router.send_chat(
    conv_id=conv_id,
    prompt=f"Analyze this test failure:\n{traceback}",
    model_preference="gemini-2.5-flash",  # Flash is good for analysis
    expected_completion_tokens=1024
)

# Continue conversation
if response['success']:
    follow_up = router.send_chat(
        conv_id=conv_id,
        prompt="What's the root cause?",
        model_preference="gemini-2.5-flash"
    )
```

## Key Management Operations

### Add New Key

```python
from keys.models import APIKey
from keys.manager import get_key_manager

key = APIKey(
    key_id="gemini-flash-03",
    model_name="gemini-2.5-flash",
    provider="gemini",
    rpm=10,
    tpm=250000,
    active=True
)

manager = get_key_manager()
manager.add_key(key)
```

### Check Key Status

```python
from keys.manager import get_key_manager

manager = get_key_manager()

# Single key
status = manager.get_key_status("gemini-flash-01")
print(f"Key: {status['key_id']}")
print(f"In cooldown: {status['in_cooldown']}")
print(f"RPM usage: {status['rpm_usage']}")
print(f"TPM usage: {status['tpm_usage']}")

# All keys
all_statuses = manager.get_all_key_statuses()
for status in all_statuses:
    print(f"{status['key_id']}: {status['in_cooldown']}")
```

### Manual Cooldown Management

```python
from keys.manager import get_key_manager

manager = get_key_manager()

# Set cooldown
manager.mark_key_unhealthy(
    "gemini-flash-01",
    cooldown_seconds=300,
    reason="Manual maintenance"
)

# Clear cooldown
from keys.redis_client import get_redis_limiter
redis_limiter = get_redis_limiter()
redis_limiter.clear_cooldown("gemini-flash-01")
```

### Remove Key

```python
from keys.manager import get_key_manager

manager = get_key_manager()
manager.remove_key("gemini-flash-01")

# Or mark inactive in JSON
# Edit keys.json and set "active": false
manager.reload_keys()
```

## Monitoring and Observability

### Health Checks

```python
from llm.router import get_request_router

router = get_request_router()
health = router.health_check()

if not health['healthy']:
    print("System unhealthy:")
    print(f"  Key manager: {health['key_manager']}")
    print(f"  Conv store: {health['conversation_store']}")
```

### Key Usage Metrics

```python
from keys.redis_client import get_redis_limiter

redis_limiter = get_redis_limiter()

# RPM usage
rpm_usage = redis_limiter.get_rpm_usage("gemini-flash-01")
print(f"RPM: {rpm_usage['count']} / {key.rpm}")

# TPM usage
tpm_usage = redis_limiter.get_tpm_usage("gemini-flash-01")
print(f"TPM: {tpm_usage['used']} / {key.tpm}")
```

### Conversation Metrics

```python
from conversation.store import get_conversation_store

store = get_conversation_store()

# Get conversation metadata
meta = store.get_metadata(conv_id)
print(f"Messages: {meta['message_count']}")
print(f"Total tokens: {meta['total_tokens']}")
print(f"Last model: {meta.get('last_model')}")
```

## Troubleshooting

### All Keys Rate Limited

**Symptom:** `AllKeysExhaustedError: No keys with available capacity`

**Solutions:**
1. Add more API keys
2. Increase RPM/TPM limits (if using paid tier)
3. Implement request queuing with backoff
4. Check for cooldowns: `manager.get_all_key_statuses()`

### Conversation Not Persisting

**Symptom:** Messages lost between requests

**Check:**
1. Redis connectivity: `store.health_check()`
2. Conversation ID consistency
3. TTL not expired (default 24 hours)

### Secrets Not Loading

**Symptom:** `SecretStoreError: Cannot retrieve secret`

**Check:**
1. `SECRET_STORE_TYPE` environment variable
2. Vault/AWS credentials configured
3. Secret path correct
4. Test: `python -c "from keys.secret_store import test_secret_access; print(test_secret_access('your-key-id'))"`

### Redis Connection Errors

**Symptom:** `RedisError` or rate limits not enforcing

**Solutions:**
1. Check Redis is running: `redis-cli ping`
2. Verify `REDIS_URL` environment variable
3. Check network connectivity
4. System fails open (allows requests) if Redis down

## Security Best Practices

1. **Never commit secrets**
   - Use secret manager (Vault, AWS, Azure)
   - Run secret scanner before commits
   - Add `.env` to `.gitignore`

2. **Scan artifacts**
   ```bash
   python tools/secret_scanner.py artifacts/ --fail-on-found
   ```

3. **Rotate keys regularly**
   - Deactivate old keys
   - Add new keys
   - Monitor for unauthorized usage

4. **Least privilege access**
   - Vault/AWS policies with minimal permissions
   - Separate keys for dev/staging/prod
   - Audit secret access logs

5. **Rate limit users**
   ```python
   from middleware.rate_limit import get_rate_limiter
   
   limiter = get_rate_limiter()
   limiter.check_rate_limit(user_id="user123")
   ```

## Performance Tuning

### Token Estimation

For better TPM reservations, use actual token counts:

```python
from llm.token_utils import count_actual_tokens

# More accurate estimation
actual_tokens = count_actual_tokens(text, model="gemini-2.5-flash")
```

### Conversation Truncation

Manage context window and costs:

```python
router.truncate_conversation(conv_id, keep_last_n=20)
```

### Key Pool Sizing

**Formula:** `keys_needed = (peak_rpm / key_rpm) * 1.5`

Example: 100 req/min peak, 10 rpm/key → need 15 keys

## Testing

Run tests:

```bash
# Unit tests
pytest tests/test_key_manager.py
pytest tests/test_router.py
pytest tests/test_conv_store.py

# Integration tests
pytest tests/integration/test_routing_flow.py

# Secret scanner
pytest tests/test_secret_scanner.py
```

## Support and Troubleshooting

For issues:
1. Check logs: `tail -f logs/llm_router.log`
2. Health check: `python -m llm.router --health-check`
3. Redis status: `redis-cli INFO stats`
4. Review this documentation

## Appendix: Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `SECRET_STORE_TYPE` | Secret storage backend | `env` |
| `VAULT_ADDR` | Vault server URL | - |
| `VAULT_TOKEN` | Vault authentication token | - |
| `AWS_REGION` | AWS region for Secrets Manager | `us-east-1` |
| `USER_RPM_DEFAULT` | Per-user rate limit (RPM) | `10` |
| `GLOBAL_RPM_MAX` | Global rate limit (RPM) | `1000` |
| `CONVERSATION_TTL_SECONDS` | Conversation expiry | `86400` (24h) |
| `LLM_MULTI_KEY_ROUTER_ENABLED` | Feature flag | `false` |

## Appendix: Redis Key Schema

| Key Pattern | Description | TTL |
|-------------|-------------|-----|
| `rpm:<key_id>` | RPM counter (minute window) | 2 min |
| `tpm:<key_id>` | TPM counter (minute window) | 2 min |
| `key:cooldown:<key_id>` | Cooldown flag | Variable |
| `conv:messages:<conv_id>` | Message list | 24h |
| `conv:meta:<conv_id>` | Conversation metadata | 24h |
| `rl:user:<user_id>` | User rate limit bucket | 1h |
| `rl:global` | Global rate limit bucket | 1h |
