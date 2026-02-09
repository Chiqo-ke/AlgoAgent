"""
Enhanced Base LLM Provider Interface

Combines existing architecture with multi-provider guide best practices.
Provides normalized response structures and consistent interfaces.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMUsage:
    """Normalized token usage tracking across all providers"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format"""
        return {
            'input': self.input_tokens,
            'output': self.output_tokens,
            'total': self.total_tokens
        }


@dataclass
class LLMResponse:
    """
    Normalized response structure across all providers.
    
    All providers return this consistent format for easier integration.
    """
    content: str
    usage: LLMUsage
    model: str
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to legacy dictionary format for backward compatibility"""
        result = {
            'content': self.content,
            'model': self.model,
            'tokens': self.usage.to_dict(),
            'finish_reason': self.finish_reason or 'stop'
        }
        if self.metadata:
            result['metadata'] = self.metadata
        return result


class LLMProviderBase(ABC):
    """
    Enhanced base class for all LLM providers.
    
    Provides consistent interface while maintaining backward compatibility
    with existing RequestRouter and KeyManager.
    """
    
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.provider_name = self._get_provider_name()
        self.kwargs = kwargs
    
    @abstractmethod
    def _get_provider_name(self) -> str:
        """Return provider identifier (e.g., 'anthropic', 'openai', 'gemini')"""
        pass
    
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response from LLM with normalized output.
        
        Args:
            messages: OpenAI-compatible message format
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            LLMResponse with normalized structure
        """
        pass
    
    def stream_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream response chunks from LLM.
        
        Yields:
            str: Text chunks as they're generated
        """
        # Default implementation for providers that don't support streaming
        response = self.generate(messages, temperature, max_tokens, **kwargs)
        yield response.content
    
    def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> LLMResponse:
        """
        Generate with function/tool calling support.
        
        Override in providers that support tools (Claude, GPT-4, Gemini 2.0, etc.)
        """
        raise NotImplementedError(
            f"{self.provider_name} does not support tool calling in this implementation"
        )
    
    def generate_with_vision(
        self,
        messages: List[Dict[str, str]],
        images: List[str],
        **kwargs
    ) -> LLMResponse:
        """
        Generate with image understanding.
        
        Override in providers that support vision (GPT-4V, Claude 3, Gemini)
        """
        raise NotImplementedError(
            f"{self.provider_name} does not support vision in this implementation"
        )
    
    @staticmethod
    def normalize_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Ensure messages follow OpenAI format.
        
        Standard format:
        [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
        """
        normalized = []
        for msg in messages:
            if "role" not in msg or "content" not in msg:
                raise ValueError(f"Invalid message format: {msg}")
            normalized.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return normalized


# Exception classes (compatible with existing code)
class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class RateLimitError(ProviderError):
    """Rate limit exceeded (429)"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """Authentication failed (401/403)"""
    pass


class ProviderUnavailableError(ProviderError):
    """Provider service unavailable (503)"""
    pass


class SafetyBlockError(ProviderError):
    """Raised when content is blocked by safety filters (Gemini)"""
    def __init__(self, message: str, safety_ratings: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.safety_ratings = safety_ratings
