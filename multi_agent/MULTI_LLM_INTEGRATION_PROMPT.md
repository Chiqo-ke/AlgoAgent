# Multi-LLM Provider Integration Guide

## Objective
Build a flexible abstraction layer that allows seamless switching between multiple LLM providers (Anthropic Claude, Google Gemini, OpenAI, GitHub Models, etc.) without changing application code.

## Architecture Pattern

### 1. Provider Abstraction Layer
Create a unified interface that all providers implement:

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class LLMProvider(ABC):
    """Base class for all LLM providers"""
    
    @abstractmethod
    def generate(self, 
                 messages: List[Dict[str, str]], 
                 temperature: float = 0.7,
                 max_tokens: Optional[int] = None,
                 **kwargs) -> Dict[str, Any]:
        """Generate response from the LLM"""
        pass
    
    @abstractmethod
    def stream_generate(self, 
                       messages: List[Dict[str, str]], 
                       **kwargs):
        """Stream response from the LLM"""
        pass
```

### 2. Provider Implementations

#### Anthropic Provider
```python
from anthropic import Anthropic

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
    
    def generate(self, messages, temperature=0.7, max_tokens=4096, **kwargs):
        response = self.client.messages.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return {
            "content": response.content[0].text,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            "model": response.model
        }
    
    def stream_generate(self, messages, **kwargs):
        with self.client.messages.stream(
            model=self.model,
            messages=messages,
            **kwargs
        ) as stream:
            for text in stream.text_stream:
                yield text
```

**Docs**: [Anthropic API Reference](https://docs.anthropic.com/en/api/messages)

#### Google Gemini Provider
```python
import google.generativeai as genai

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    def generate(self, messages, temperature=0.7, max_tokens=8192, **kwargs):
        # Convert messages to Gemini format
        gemini_messages = self._convert_messages(messages)
        
        response = self.model.generate_content(
            gemini_messages,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                **kwargs
            }
        )
        return {
            "content": response.text,
            "usage": {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count
            },
            "model": self.model.model_name
        }
    
    def _convert_messages(self, messages):
        """Convert standard message format to Gemini format"""
        # Gemini uses 'user' and 'model' roles
        converted = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            converted.append({"role": role, "parts": [msg["content"]]})
        return converted
    
    def stream_generate(self, messages, **kwargs):
        gemini_messages = self._convert_messages(messages)
        response = self.model.generate_content(
            gemini_messages,
            stream=True,
            **kwargs
        )
        for chunk in response:
            yield chunk.text
```

**Docs**: [Google Gemini API Docs](https://ai.google.dev/gemini-api/docs)

#### OpenAI/Azure OpenAI Provider
```python
from openai import OpenAI

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: Optional[str] = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    def generate(self, messages, temperature=0.7, max_tokens=4096, **kwargs):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return {
            "content": response.choices[0].message.content,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            },
            "model": response.model
        }
    
    def stream_generate(self, messages, **kwargs):
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

**Docs**: [OpenAI API Reference](https://platform.openai.com/docs/api-reference/chat)

#### GitHub Models Provider
```python
class GitHubModelsProvider(LLMProvider):
    """
    Uses GitHub Models marketplace (compatible with OpenAI SDK)
    Supports: GPT-4o, Claude, Llama, Mistral, Phi, etc.
    """
    def __init__(self, token: str, model: str = "gpt-4o"):
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=token  # GitHub Personal Access Token
        )
        self.model = model
    
    def generate(self, messages, temperature=0.7, max_tokens=4096, **kwargs):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return {
            "content": response.choices[0].message.content,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            },
            "model": response.model
        }
    
    def stream_generate(self, messages, **kwargs):
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

**Docs**: [GitHub Models Documentation](https://docs.github.com/en/github-models)

### 3. Provider Factory

```python
from typing import Optional
from enum import Enum

class ProviderType(Enum):
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENAI = "openai"
    GITHUB = "github"
    AZURE = "azure"

class LLMFactory:
    """Factory to create LLM provider instances"""
    
    @staticmethod
    def create_provider(
        provider_type: str,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create and return appropriate provider instance
        
        Args:
            provider_type: Type of provider (anthropic, gemini, openai, github)
            api_key: API key for the provider
            model: Model name (optional, uses defaults)
            **kwargs: Additional provider-specific config
        """
        provider_map = {
            ProviderType.ANTHROPIC.value: (AnthropicProvider, "claude-3-5-sonnet-20241022"),
            ProviderType.GEMINI.value: (GeminiProvider, "gemini-2.0-flash-exp"),
            ProviderType.OPENAI.value: (OpenAIProvider, "gpt-4o"),
            ProviderType.GITHUB.value: (GitHubModelsProvider, "gpt-4o"),
        }
        
        if provider_type not in provider_map:
            raise ValueError(f"Unknown provider: {provider_type}")
        
        provider_class, default_model = provider_map[provider_type]
        model = model or default_model
        
        return provider_class(api_key=api_key, model=model, **kwargs)
```

### 4. Configuration Management

```python
# config.py or settings.py
import os
from typing import Optional

class LLMConfig:
    """Configuration for LLM providers"""
    
    # Primary provider (which one to use by default)
    DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "github")
    DEFAULT_MODEL = os.getenv("LLM_MODEL", None)
    
    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    # Model defaults per provider
    MODELS = {
        "anthropic": "claude-3-5-sonnet-20241022",
        "gemini": "gemini-2.0-flash-exp",
        "openai": "gpt-4o",
        "github": "gpt-4o"
    }
    
    @classmethod
    def get_api_key(cls, provider: str) -> Optional[str]:
        """Get API key for specified provider"""
        key_map = {
            "anthropic": cls.ANTHROPIC_API_KEY,
            "gemini": cls.GEMINI_API_KEY,
            "openai": cls.OPENAI_API_KEY,
            "github": cls.GITHUB_TOKEN,
        }
        return key_map.get(provider)
```

### 5. Usage Example

```python
# Simple usage
from llm_factory import LLMFactory
from config import LLMConfig

# Create provider from config
provider = LLMFactory.create_provider(
    provider_type=LLMConfig.DEFAULT_PROVIDER,
    api_key=LLMConfig.get_api_key(LLMConfig.DEFAULT_PROVIDER),
    model=LLMConfig.DEFAULT_MODEL
)

# Use the provider
messages = [
    {"role": "user", "content": "Explain quantum computing in simple terms"}
]

response = provider.generate(messages, temperature=0.7)
print(response["content"])

# Streaming
for chunk in provider.stream_generate(messages):
    print(chunk, end="", flush=True)
```

### 6. Environment Configuration

```bash
# .env file
LLM_PROVIDER=github          # anthropic, gemini, openai, github
LLM_MODEL=gpt-4o            # Override default model

# API Keys (only needed ones need to be set)
ANTHROPIC_API_KEY=sk-ant-xxx
GEMINI_API_KEY=xxx
OPENAI_API_KEY=sk-xxx
GITHUB_TOKEN=ghp_xxx
```

## Implementation Steps

1. **Install SDKs** - Only install what you need:
```bash
pip install anthropic              # For Claude
pip install google-generativeai    # For Gemini
pip install openai                 # For OpenAI/GitHub Models
```

2. **Create base abstraction** (`llm_provider.py`)
   - Define `LLMProvider` abstract base class
   - Standardize method signatures

3. **Implement providers** (separate files or same file)
   - Create concrete classes for each provider
   - Implement message format conversions
   - Handle provider-specific quirks

4. **Build factory** (`llm_factory.py`)
   - Create provider registry
   - Implement `create_provider()` method
   - Add error handling

5. **Configure environment**
   - Create config class or use environment variables
   - Set default provider and models
   - Store API keys securely

6. **Integrate into application**
   - Replace direct API calls with provider interface
   - Use factory to instantiate providers
   - Add provider switching logic

## Best Practices

### 1. Message Format Normalization
Always use OpenAI-compatible message format as your standard:
```python
[
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "How are you?"}
]
```

### 2. Error Handling
```python
class ProviderError(Exception):
    """Base exception for provider errors"""
    pass

class RateLimitError(ProviderError):
    """Rate limit exceeded"""
    pass

class AuthenticationError(ProviderError):
    """Authentication failed"""
    pass

# In provider implementation
def generate(self, messages, **kwargs):
    try:
        response = self.client.messages.create(...)
        return self._format_response(response)
    except Exception as e:
        raise ProviderError(f"Generation failed: {str(e)}") from e
```

### 3. Response Normalization
Always return consistent response structure:
```python
{
    "content": "The actual text response",
    "usage": {
        "input_tokens": 100,
        "output_tokens": 50
    },
    "model": "claude-3-5-sonnet-20241022",
    "finish_reason": "end_turn"  # optional
}
```

### 4. Provider Fallback
```python
class MultiProviderLLM:
    """LLM with automatic fallback to alternative providers"""
    
    def __init__(self, providers: List[LLMProvider]):
        self.providers = providers
    
    def generate(self, messages, **kwargs):
        last_error = None
        
        for provider in self.providers:
            try:
                return provider.generate(messages, **kwargs)
            except Exception as e:
                last_error = e
                continue
        
        raise ProviderError(f"All providers failed. Last error: {last_error}")
```

### 5. Cost Tracking
```python
class CostTracker:
    """Track token usage and estimated costs"""
    
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},  # per 1k tokens
        "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free tier
        "gpt-4o": {"input": 0.0025, "output": 0.01},
    }
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        if model not in self.PRICING:
            return 0.0
        
        pricing = self.PRICING[model]
        cost = (input_tokens / 1000 * pricing["input"] + 
                output_tokens / 1000 * pricing["output"])
        return cost
```

## Documentation References

- **Anthropic Claude**: https://docs.anthropic.com/en/api/messages
- **Google Gemini**: https://ai.google.dev/gemini-api/docs
- **OpenAI**: https://platform.openai.com/docs/api-reference/chat
- **GitHub Models**: https://docs.github.com/en/github-models
- **Azure OpenAI**: https://learn.microsoft.com/en-us/azure/ai-services/openai/

## Advanced Features

### Tool/Function Calling Support
```python
@abstractmethod
def generate_with_tools(self, 
                       messages: List[Dict], 
                       tools: List[Dict],
                       **kwargs) -> Dict[str, Any]:
    """Generate with function calling support"""
    pass
```

### Vision Support
```python
@abstractmethod
def generate_with_vision(self,
                        messages: List[Dict],
                        images: List[str],  # URLs or base64
                        **kwargs) -> Dict[str, Any]:
    """Generate with image understanding"""
    pass
```

### Caching (Anthropic-specific)
```python
# For Anthropic's prompt caching
def generate(self, messages, use_cache=False, **kwargs):
    extra_headers = {}
    if use_cache:
        extra_headers["anthropic-beta"] = "prompt-caching-2024-07-31"
    
    response = self.client.messages.create(
        model=self.model,
        messages=messages,
        extra_headers=extra_headers,
        **kwargs
    )
```

## Testing Your Integration

```python
def test_all_providers():
    """Test that all providers work correctly"""
    providers = ["anthropic", "gemini", "openai", "github"]
    messages = [{"role": "user", "content": "Say 'Hello World'"}]
    
    for provider_type in providers:
        api_key = LLMConfig.get_api_key(provider_type)
        if not api_key:
            print(f"Skipping {provider_type} (no API key)")
            continue
        
        provider = LLMFactory.create_provider(provider_type, api_key)
        response = provider.generate(messages, max_tokens=50)
        
        assert "content" in response
        assert response["content"]
        print(f"✓ {provider_type}: {response['content'][:50]}")
```

---

## Summary

This integration pattern provides:
- ✅ **Provider agnostic** - Switch providers without code changes
- ✅ **Consistent interface** - Same methods across all providers
- ✅ **Easy configuration** - Environment-based provider selection
- ✅ **Extensible** - Add new providers by implementing interface
- ✅ **Production ready** - Error handling, fallbacks, cost tracking

Adapt this pattern to your specific framework (Django, FastAPI, Flask, etc.) by integrating the factory and configuration into your application's initialization and dependency injection system.
