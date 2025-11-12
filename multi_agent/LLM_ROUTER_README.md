# Multi-Key LLM Router System

## 🎯 Overview

A production-ready **multi-key routing and rate limiting system** for LLM APIs, designed for the AlgoAgent multi-agent architecture. Features intelligent key selection, atomic RPM/TPM enforcement, conversation persistence, and automatic failover.

## ✨ Features

### Core Capabilities
- **🔄 Multi-Key Rotation** - Automatic load distribution across multiple API keys
- **⚡ Atomic Rate Limiting** - Redis-backed RPM/TPM enforcement using Lua scripts
- **💾 Conversation Persistence** - Stateful conversations independent of key rotation
- **🛡️ Security** - Secrets stored in external vaults (Vault, AWS, Azure)
- **🔍 Secret Scanning** - Automatic detection of leaked credentials in artifacts
- **📊 Observability** - Prometheus metrics and health monitoring
- **🚦 User Rate Limiting** - Token bucket algorithm for per-user and global limits

### Supported Providers
- ✅ Google Gemini (gemini-2.5-flash, gemini-2.5-pro)
- ✅ OpenAI (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
- ✅ Anthropic Claude (claude-3-opus, claude-3-sonnet)
- 🔌 Extensible for custom providers

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd multi_agent
pip install -r requirements_llm.txt
```

### 2. Start Redis

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. Configure Keys

```bash
# Copy example configuration
cp keys_example.json keys.json
cp .env.example .env

# Edit keys.json with your key metadata (RPM/TPM limits)
# Store actual secrets in environment or vault
export SECRET_STORE_TYPE=env
export API_KEY_GEMINI_FLASH_01=your-api-key-here
```

### 4. Test the System

```python
from llm.router import get_request_router

router = get_request_router()

# Health check
health = router.health_check()
print(f"Healthy: {health['healthy']}")

# Send request
response = router.send_one_shot(
    prompt="Hello! Confirm you're working.",
    model_preference="gemini-2.5-flash"
)
print(response['content'])
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Application Layer (Agents)                  │
│  Orchestrator │ Coder │ Debugger │ Tester │ Planner    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 RequestRouter                            │
│  • Token estimation                                      │
│  • Conversation management                               │
│  • Retry logic with exponential backoff                 │
│  • Error handling and metrics                           │
└────────┬────────────────────────────┬───────────────────┘
         │                            │
         ▼                            ▼
┌────────────────────┐   ┌───────────────────────────────┐
│   KeyManager       │   │    ConversationStore          │
│ • Key selection    │   │  • Redis-backed history       │
│ • Health tracking  │   │  • Cross-key persistence      │
│ • Cooldown mgmt    │   │  • Message truncation         │
└──────┬─────────────┘   └───────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│            Redis Rate Limiter                            │
│  • Atomic RPM/TPM reservations (Lua scripts)            │
│  • Per-key windowed counters                            │
│  • Cooldown tracking                                    │
│  • User rate limiting (token bucket)                    │
└─────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Responsibility | Storage |
|-----------|---------------|---------|
| **RequestRouter** | Orchestrates LLM calls, manages retries | Stateless |
| **KeyManager** | Selects optimal key, tracks health | In-memory cache + Redis |
| **ConversationStore** | Persists conversation history | Redis lists/hashes |
| **RedisRateLimiter** | Atomic RPM/TPM enforcement | Redis |
| **SecretStore** | Fetches API keys from vault | External (Vault/AWS/Azure) |
| **RateLimiter** | Per-user and global rate limits | Redis |

## 📦 Installation

### Requirements

- Python 3.9+
- Redis 5.0+
- Secret manager (Vault, AWS Secrets Manager, or Azure Key Vault)

### Install Python Dependencies

```bash
pip install -r requirements_llm.txt
```

### Optional Dependencies

```bash
# For OpenAI
pip install openai

# For Anthropic
pip install anthropic

# For HashiCorp Vault
pip install hvac

# For AWS Secrets Manager
pip install boto3

# For Azure Key Vault
pip install azure-keyvault-secrets azure-identity

# For accurate token counting
pip install tiktoken google-generativeai
```

## ⚙️ Configuration

### Environment Variables

Create `.env` from `.env.example`:

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Secret Storage
SECRET_STORE_TYPE=env  # Options: env, vault, aws, azure

# Rate Limits
USER_RPM_DEFAULT=10
USER_BURST_DEFAULT=20
GLOBAL_RPM_MAX=1000
GLOBAL_BURST_MAX=2000

# Feature Flags
LLM_MULTI_KEY_ROUTER_ENABLED=true
```

### API Key Configuration

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
      "tags": {"tier": "free"}
    }
  ]
}
```

### Secret Storage Options

**Development (Environment Variables):**
```bash
export API_KEY_GEMINI_FLASH_01=AIza...
```

**Production (HashiCorp Vault):**
```bash
export SECRET_STORE_TYPE=vault
export VAULT_ADDR=https://vault.example.com
export VAULT_TOKEN=your-token

vault kv put secret/llm/gemini-flash-01 api_key=AIza...
```

**AWS Secrets Manager:**
```bash
export SECRET_STORE_TYPE=aws
aws secretsmanager create-secret \
  --name llm/gemini-flash-01 \
  --secret-string '{"api_key":"AIza..."}'
```

## 💡 Usage Examples

### Basic Request

```python
from llm.router import get_request_router

router = get_request_router()

response = router.send_one_shot(
    prompt="Explain async/await in Python",
    model_preference="gemini-2.5-flash"
)

print(response['content'])
```

### Conversation Management

```python
conv_id = "user_123_session"

# First message
router.send_chat(
    conv_id=conv_id,
    prompt="What is dependency injection?",
    system_prompt="You are a software architecture expert."
)

# Follow-up (uses history)
response = router.send_chat(
    conv_id=conv_id,
    prompt="Give me a Python example"
)
```

### Code Generation (Pro Model)

```python
response = router.send_one_shot(
    prompt="Generate a FastAPI CRUD endpoint for User model",
    model_preference="gemini-2.5-pro",
    expected_completion_tokens=2048,
    temperature=0.3
)
```

### Error Handling

```python
response = router.send_one_shot(prompt="Hello")

if response['success']:
    print(response['content'])
else:
    if response.get('error_type') == 'rate_limited':
        # Queue for retry
        print(f"Rate limited, retry after cooldown")
    else:
        print(f"Error: {response['error']}")
```

## 📚 API Reference

### RequestRouter

```python
router = get_request_router()

# One-shot request
response = router.send_one_shot(
    prompt: str,
    model_preference: Optional[str] = None,
    system_prompt: Optional[str] = None,
    expected_completion_tokens: int = 512,
    max_output_tokens: int = 2048,
    temperature: float = 0.7
) -> Dict[str, Any]

# Conversation request
response = router.send_chat(
    conv_id: str,
    prompt: str,
    user_id: Optional[str] = None,
    model_preference: Optional[str] = None,
    expected_completion_tokens: int = 512,
    max_output_tokens: int = 2048,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]

# Health check
health = router.health_check() -> Dict[str, Any]
```

### KeyManager

```python
from keys.manager import get_key_manager

manager = get_key_manager()

# Get key status
status = manager.get_key_status(key_id: str)

# Get all statuses
statuses = manager.get_all_key_statuses()

# Mark unhealthy
manager.mark_key_unhealthy(
    key_id: str,
    cooldown_seconds: int,
    reason: str
)

# Health check
health = manager.health_check()
```

### ConversationStore

```python
from conversation.store import get_conversation_store

store = get_conversation_store()

# Create conversation
store.create_conversation(conv_id: str, metadata: Dict)

# Get history
messages = store.get_history(conv_id: str, limit: int = None)

# Truncate
store.truncate_history(conv_id: str, keep_last_n: int = 20)

# Get metadata
meta = store.get_metadata(conv_id: str)
```

## 🧪 Testing

### Run Unit Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_key_manager.py -v
pytest tests/test_router.py -v

# With coverage
pytest tests/ --cov=keys --cov=llm --cov=conversation --cov-report=html
```

### Secret Scanner

```bash
# Scan directory
python tools/secret_scanner.py artifacts/ --fail-on-found

# Scan single file
python tools/secret_scanner.py test.log --output report.json
```

### Integration Tests

```bash
# Full routing flow
pytest tests/integration/test_routing_flow.py -v

# Concurrent access
pytest tests/integration/test_concurrent_requests.py -v
```

## 🚢 Deployment

### Production Checklist

- [ ] Redis cluster configured with persistence
- [ ] Secrets in external vault (not environment variables)
- [ ] Monitoring enabled (Prometheus + Grafana)
- [ ] Log aggregation configured
- [ ] Rate limits tuned for expected load
- [ ] Multiple keys per model for redundancy
- [ ] Feature flag `LLM_MULTI_KEY_ROUTER_ENABLED` set to `true`
- [ ] Secret scanner integrated into CI/CD
- [ ] Health check endpoint exposed

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements_llm.txt .
RUN pip install -r requirements_llm.txt

COPY . .

ENV REDIS_URL=redis://redis:6379/0
ENV SECRET_STORE_TYPE=vault

CMD ["python", "-m", "orchestrator_service.orchestrator"]
```

### Health Check Endpoint

```python
from flask import Flask, jsonify
from llm.router import get_request_router

app = Flask(__name__)

@app.route('/health')
def health():
    router = get_request_router()
    health_status = router.health_check()
    
    status_code = 200 if health_status['healthy'] else 503
    return jsonify(health_status), status_code
```

## 🔧 Troubleshooting

### Common Issues

**❌ All Keys Exhausted**
```
Solution: Add more keys or increase RPM/TPM limits
Check: manager.get_all_key_statuses()
```

**❌ Redis Connection Failed**
```
Solution: Verify Redis is running and REDIS_URL is correct
Check: redis-cli ping
```

**❌ Secrets Not Loading**
```
Solution: Check SECRET_STORE_TYPE and vault credentials
Test: python -c "from keys.secret_store import test_secret_access; print(test_secret_access('key-id'))"
```

**❌ High Latency**
```
Solution: Check Redis latency and key distribution
Monitor: Redis INFO stats, key_manager health
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Monitoring

### Metrics

Export to Prometheus:
- `key_rpm_used{key_id}`
- `key_tpm_used{key_id}`
- `key_cooldown{key_id}`
- `request_router_attempts_total`
- `request_router_rate_limited_total`

### Grafana Dashboard

See `docs/grafana_dashboard.json` for pre-built dashboard.

## 📖 Documentation

- [Full Documentation](docs/llm_key_rotation.md)
- [Architecture Specification](ARCHITECTURE.md)
- [API Integration Guide](docs/api_integration.md)
- [Security Best Practices](docs/security.md)

## 🤝 Contributing

1. Run tests: `pytest tests/ -v`
2. Run secret scanner: `python tools/secret_scanner.py .`
3. Check types: `mypy keys/ llm/ conversation/`
4. Format code: `black keys/ llm/ conversation/`

## 📄 License

See LICENSE file.

## 🆘 Support

For issues:
1. Check [Troubleshooting](#troubleshooting)
2. Review logs: `tail -f logs/llm_router.log`
3. Health check: `python -m llm.router --health-check`
4. Open GitHub issue with debug info

---

**Built for AlgoAgent Multi-Agent System** | [GitHub](https://github.com/Chiqo-ke/AlgoAgent)
