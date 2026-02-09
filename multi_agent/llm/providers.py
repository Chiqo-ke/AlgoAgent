"""
Provider client abstractions for different LLM APIs.

Supports:
- Google Gemini
- OpenAI
- Anthropic Claude
- Azure OpenAI
- GitHub Models
- OpenCode (unified access to multiple providers)
"""
import os
import logging
from typing import Dict, Any, List, Optional, Generator
from abc import ABC, abstractmethod

# Import enhanced base classes
from .base_provider import (
    LLMProviderBase,
    LLMResponse,
    LLMUsage,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    ProviderUnavailableError,
    SafetyBlockError
)

logger = logging.getLogger(__name__)


class ProviderClient(ABC):
    """Abstract base class for provider clients."""
    
    @abstractmethod
    def chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request.
        
        Returns:
            {
                'content': str,
                'model': str,
                'tokens': {
                    'input': int,
                    'output': int,
                    'total': int
                },
                'finish_reason': str
            }
        """
        pass


class GeminiClient(ProviderClient):
    """Google Gemini API client."""
    
    def chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Send Gemini chat completion request."""
        try:
            import google.generativeai as genai
            from google.api_core import exceptions as google_exceptions
        except ImportError:
            raise ProviderError(
                "google-generativeai not installed (pip install google-generativeai)"
            )
        
        try:
            # Configure API key
            genai.configure(api_key=api_key)
            
            # Create model with safety settings bypassed
            generation_config = {
                'max_output_tokens': max_tokens,
                'temperature': temperature
            }
            
            # Bypass safety filters for code generation (TRIPLE REDUNDANCY)
            # Applied at: 1) Model init, 2) Chat session, 3) Message send
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
            # 1) Apply at model initialization
            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Convert messages to Gemini format
            history, last_message = self._convert_messages(messages)
            
            # 2) Start chat session (safety settings inherited from model)
            chat = model_instance.start_chat(
                history=history
            )
            
            # 3) Apply at message send (explicit override - CRITICAL for safety bypass)
            response = chat.send_message(
                last_message,
                safety_settings=safety_settings
            )
            
            # Validate response for safety blocks BEFORE accessing .text
            if not response.candidates:
                raise SafetyBlockError(
                    f"No candidates returned - likely safety block. Prompt feedback: {response.prompt_feedback}",
                    safety_ratings=None
                )
            
            candidate = response.candidates[0]
            
            # Check finish_reason (2 = SAFETY, 3 = RECITATION, 4 = OTHER)
            if candidate.finish_reason in [2, 3]:
                finish_reason_name = {
                    2: "SAFETY",
                    3: "RECITATION",
                    4: "OTHER"
                }.get(candidate.finish_reason, "UNKNOWN")
                
                safety_ratings = []
                if hasattr(candidate, 'safety_ratings'):
                    safety_ratings = [
                        {
                            'category': rating.category.name if hasattr(rating.category, 'name') else str(rating.category),
                            'probability': rating.probability.name if hasattr(rating.probability, 'name') else str(rating.probability)
                        }
                        for rating in candidate.safety_ratings
                    ]
                
                raise SafetyBlockError(
                    f"Content blocked by safety filter. Finish reason: {finish_reason_name}. "
                    f"Safety ratings: {safety_ratings}. Prompt feedback: {response.prompt_feedback}",
                    safety_ratings=safety_ratings
                )
            
            # Extract response (safe to access .text now)
            content = response.text
            
            # Get token counts if available
            tokens = {}
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                tokens = {
                    'input': getattr(usage, 'prompt_token_count', 0),
                    'output': getattr(usage, 'candidates_token_count', 0),
                    'total': getattr(usage, 'total_token_count', 0)
                }
            
            return {
                'content': content,
                'model': model,
                'tokens': tokens,
                'finish_reason': 'stop'
            }
            
        except google_exceptions.ResourceExhausted as e:
            # 429 rate limit
            retry_after = self._extract_retry_after(str(e))
            raise RateLimitError(str(e), retry_after=retry_after)
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise ProviderError(f"Gemini error: {str(e)}")
    
    def _convert_messages(self, messages: List[Dict[str, str]]):
        """Convert standard messages to Gemini format."""
        history = []
        
        for i, msg in enumerate(messages[:-1]):
            role = msg['role']
            content = msg['content']
            
            # Map roles
            if role == 'user':
                gemini_role = 'user'
            elif role in ['assistant', 'model']:
                gemini_role = 'model'
            elif role == 'system':
                # Gemini doesn't have system role - prepend to first user message
                continue
            else:
                gemini_role = 'user'
            
            history.append({
                'role': gemini_role,
                'parts': [content]
            })
        
        # Last message is sent separately
        last_message = messages[-1]['content']
        
        return history, last_message
    
    def _extract_retry_after(self, error_msg: str) -> Optional[int]:
        """Extract Retry-After from error message."""
        import re
        match = re.search(r'Retry after (\d+)', error_msg, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None


class OpenAIClient(ProviderClient):
    """OpenAI API client."""
    
    def chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Send OpenAI chat completion request."""
        try:
            from openai import OpenAI
            from openai import RateLimitError as OpenAIRateLimitError
        except ImportError:
            raise ProviderError("openai not installed (pip install openai)")
        
        try:
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            # Get token usage
            tokens = {
                'input': response.usage.prompt_tokens,
                'output': response.usage.completion_tokens,
                'total': response.usage.total_tokens
            }
            
            return {
                'content': content,
                'model': model,
                'tokens': tokens,
                'finish_reason': finish_reason
            }
            
        except OpenAIRateLimitError as e:
            # Extract retry-after from headers if available
            retry_after = None
            if hasattr(e, 'response') and e.response:
                retry_after = e.response.headers.get('Retry-After')
                if retry_after:
                    retry_after = int(retry_after)
            
            raise RateLimitError(str(e), retry_after=retry_after)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise ProviderError(f"OpenAI error: {str(e)}")


class AnthropicClient(ProviderClient):
    """Anthropic Claude API client."""
    
    def chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Send Anthropic chat completion request."""
        try:
            from anthropic import Anthropic
            from anthropic import RateLimitError as AnthropicRateLimitError
        except ImportError:
            raise ProviderError("anthropic not installed (pip install anthropic)")
        
        try:
            client = Anthropic(api_key=api_key)
            
            # Extract system message if present
            system_message = None
            filtered_messages = []
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    filtered_messages.append(msg)
            
            # Send request
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=filtered_messages
            )
            
            # Extract response
            content = response.content[0].text
            
            # Get token usage
            tokens = {
                'input': response.usage.input_tokens,
                'output': response.usage.output_tokens,
                'total': response.usage.input_tokens + response.usage.output_tokens
            }
            
            return {
                'content': content,
                'model': model,
                'tokens': tokens,
                'finish_reason': response.stop_reason
            }
            
        except AnthropicRateLimitError as e:
            retry_after = None
            if hasattr(e, 'response') and e.response:
                retry_after = e.response.headers.get('retry-after')
                if retry_after:
                    retry_after = int(retry_after)
            
            raise RateLimitError(str(e), retry_after=retry_after)
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise ProviderError(f"Anthropic error: {str(e)}")


class AzureOpenAIClient(ProviderClient):
    """Azure OpenAI API client."""
    
    def chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Send Azure OpenAI chat completion request."""
        try:
            from openai import AzureOpenAI
            from openai import RateLimitError as OpenAIRateLimitError
        except ImportError:
            raise ProviderError("openai not installed (pip install openai>=1.0.0)")
        
        try:
            # Get Azure-specific configuration from environment
            azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
            
            if not azure_endpoint:
                raise ProviderError(
                    "AZURE_OPENAI_ENDPOINT not configured in environment variables. "
                    "Set it to your Azure OpenAI resource endpoint (e.g., https://your-resource.openai.azure.com/)"
                )
            
            # Create Azure OpenAI client
            client = AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=azure_endpoint
            )
            
            # Send chat completion request
            response = client.chat.completions.create(
                model=model,  # This is the deployment name in Azure
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            # Get token usage
            tokens = {
                'input': response.usage.prompt_tokens,
                'output': response.usage.completion_tokens,
                'total': response.usage.total_tokens
            }
            
            return {
                'content': content,
                'model': model,
                'tokens': tokens,
                'finish_reason': finish_reason
            }
            
        except OpenAIRateLimitError as e:
            # Extract retry-after from headers if available
            retry_after = None
            if hasattr(e, 'response') and e.response:
                retry_after = e.response.headers.get('Retry-After')
                if retry_after:
                    retry_after = int(retry_after)
            
            raise RateLimitError(str(e), retry_after=retry_after)
            
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {e}")
            raise ProviderError(f"Azure OpenAI error: {str(e)}")


class GitHubModelsClient(ProviderClient):
    """
    GitHub Models API client.
    
    GitHub Models provides free AI models through an OpenAI-compatible API.
    Requires a GitHub Personal Access Token with 'models:read' permission.
    
    Endpoint: https://models.inference.ai.azure.com
    Models: gpt-4o, o1-mini, o1, mistral-large, phi-4, and more
    
    See: https://docs.github.com/en/github-models
    """
    
    def chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Send GitHub Models chat completion request."""
        try:
            from openai import OpenAI
            from openai import RateLimitError as OpenAIRateLimitError
        except ImportError:
            raise ProviderError("openai not installed (pip install openai>=1.0.0)")
        
        try:
            # GitHub Models endpoint (OpenAI-compatible)
            endpoint = "https://models.inference.ai.azure.com"
            
            # Create OpenAI client configured for GitHub Models
            client = OpenAI(
                api_key=api_key,  # GitHub Personal Access Token
                base_url=endpoint
            )
            
            # Send chat completion request
            response = client.chat.completions.create(
                model=model,  # e.g., "gpt-4o", "o1-mini", "mistral-large"
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            # Get token usage
            tokens = {
                'input': response.usage.prompt_tokens,
                'output': response.usage.completion_tokens,
                'total': response.usage.total_tokens
            }
            
            return {
                'content': content,
                'model': model,
                'tokens': tokens,
                'finish_reason': finish_reason
            }
            
        except OpenAIRateLimitError as e:
            # Extract retry-after from headers if available
            retry_after = None
            if hasattr(e, 'response') and e.response:
                retry_after = e.response.headers.get('Retry-After')
                if retry_after:
                    retry_after = int(retry_after)
            
            raise RateLimitError(str(e), retry_after=retry_after)
            
        except Exception as e:
            logger.error(f"GitHub Models API error: {e}")
            raise ProviderError(f"GitHub Models error: {str(e)}")


class OpenCodeClient(ProviderClient):
    """
    OpenCode.ai unified provider client.
    
    Provides access to multiple LLM providers (Claude, GPT-4, Gemini, Llama, etc.)
    through a single OpenAI-compatible API endpoint.
    
    Endpoint: https://opencode.ai/api/v1
    Get API key: https://opencode.ai
    
    Supported models:
    - claude-sonnet-4-20250514 (Anthropic Claude Sonnet 4)
    - gpt-4o, gpt-4o-mini (OpenAI)
    - gemini-2.0-flash-exp (Google Gemini)
    - llama-3.1-405b (Meta Llama)
    - mistral-large (Mistral AI)
    """
    
    def chat_completion(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Send OpenCode chat completion request."""
        try:
            from openai import OpenAI
            from openai import RateLimitError as OpenAIRateLimitError
        except ImportError:
            raise ProviderError("openai not installed (pip install openai>=1.0.0)")
        
        try:
            # OpenCode endpoint (OpenAI-compatible)
            endpoint = "https://opencode.ai/api/v1"
            
            # Create OpenAI client configured for OpenCode
            client = OpenAI(
                api_key=api_key,  # OpenCode API key
                base_url=endpoint
            )
            
            # Send chat completion request
            response = client.chat.completions.create(
                model=model,  # e.g., "claude-sonnet-4-20250514", "gpt-4o"
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            # Get token usage
            tokens = {
                'input': response.usage.prompt_tokens,
                'output': response.usage.completion_tokens,
                'total': response.usage.total_tokens
            }
            
            return {
                'content': content,
                'model': model,
                'tokens': tokens,
                'finish_reason': finish_reason
            }
            
        except OpenAIRateLimitError as e:
            # Extract retry-after from headers if available
            retry_after = None
            if hasattr(e, 'response') and e.response:
                retry_after = e.response.headers.get('Retry-After')
                if retry_after:
                    retry_after = int(retry_after)
            
            raise RateLimitError(str(e), retry_after=retry_after)
            
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                raise ProviderError(f"OpenCode authentication error: {str(e)}")
            logger.error(f"OpenCode API error: {e}")
            raise ProviderError(f"OpenCode error: {str(e)}")


# Provider registry
_PROVIDERS: Dict[str, ProviderClient] = {
    'gemini': GeminiClient(),
    'openai': OpenAIClient(),
    'anthropic': AnthropicClient(),
    'azure-openai': AzureOpenAIClient(),
    'github-models': GitHubModelsClient(),
    'opencode': OpenCodeClient()
}


def get_provider_client(provider: str) -> ProviderClient:
    """
    Get provider client by name.
    
    Args:
        provider: Provider name ('gemini', 'openai', 'anthropic')
        
    Returns:
        ProviderClient instance
        
    Raises:
        ProviderError: If provider not found
    """
    client = _PROVIDERS.get(provider.lower())
    if not client:
        raise ProviderError(f"Unknown provider: {provider}")
    return client


def register_provider(name: str, client: ProviderClient):
    """Register a custom provider client."""
    _PROVIDERS[name.lower()] = client
    logger.info(f"Registered provider: {name}")


class GeminiProvider:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        
        # Configure safety settings to be more permissive for code generation
        safety_settings = {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE"
        }
        
        self.model = genai.GenerativeModel(
            model_name,
            safety_settings=safety_settings
        )
        self.model_name = model_name

    def chat_completion(self, messages: List[Dict], **kwargs) -> str:
        """Generate chat completion for the given messages."""
        response = self.model.chat(messages, **kwargs)
        return response.generations[0].text.strip()
