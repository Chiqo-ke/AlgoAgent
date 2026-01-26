"""
Request Router - Centralized API Key Rotation & Model Management
================================================================

Handles automatic key rotation and failover for Gemini API calls.
Provides a unified interface for all AI model interactions.

Version: 1.0.0
"""

import logging
import time
from typing import Dict, Any, Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    import google.generativeai as genai

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from .key_rotation import get_key_manager, KeyRotationError

logger = logging.getLogger(__name__)


class RequestRouter:
    """
    Centralized router for AI model requests with automatic key rotation.
    
    Features:
    - Automatic API key rotation on failure
    - Retry mechanism with exponential backoff
    - Model failover (e.g., flash -> pro)
    - Request tracking and logging
    """
    
    def __init__(self, max_retries: int = 3, initial_backoff: float = 1.0):
        """
        Initialize RequestRouter
        
        Args:
            max_retries: Maximum number of retry attempts per key
            initial_backoff: Initial backoff delay in seconds
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        
        self.key_manager = get_key_manager()
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.request_count = 0
        self.failure_count = 0
        
        logger.info(f"RequestRouter initialized (max_retries={max_retries})")
    
    def get_generative_model(self, model_name: str = 'gemini-2.0-flash'):
        """
        Get a configured Gemini model with automatic key selection.
        
        Args:
            model_name: Model name to use
            
        Returns:
            Configured GenerativeModel instance
            
        Raises:
            KeyRotationError: If no API keys are available
        """
        # Select best available key
        key_info = self.key_manager.select_key(model_preference=model_name)
        
        if not key_info:
            raise KeyRotationError("No API keys available for model generation")
        
        # Configure API with selected key
        genai.configure(api_key=key_info['secret'])
        
        # Create and return model
        model = genai.GenerativeModel(model_name)
        logger.debug(f"Created model '{model_name}' using key: {key_info['id']}")
        
        return model
    
    def execute_with_retry(
        self, 
        model_name: str,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
        retry_on_safety_filter: bool = True
    ) -> str:
        """
        Execute a prompt with automatic retry and key rotation.
        
        Args:
            model_name: Model to use (e.g., 'gemini-2.0-flash')
            prompt: The prompt to send
            temperature: Generation temperature (0.0-1.0)
            max_output_tokens: Maximum tokens in response
            retry_on_safety_filter: Whether to retry if safety filter blocks
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If all retries exhausted
        """
        self.request_count += 1
        last_error = None
        backoff = self.initial_backoff
        
        for attempt in range(self.max_retries):
            try:
                # Get model with current best key
                key_info = self.key_manager.select_key(model_preference=model_name)
                
                if not key_info:
                    raise KeyRotationError("No API keys available")
                
                # Configure and create model
                genai.configure(api_key=key_info['secret'])
                model = genai.GenerativeModel(model_name)
                
                logger.info(f"Request {self.request_count}, attempt {attempt + 1}/{self.max_retries} using key: {key_info['key_id']}")
                
                # Execute request
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_output_tokens
                    )
                )
                
                # Check for safety filter blocking
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    if hasattr(response.prompt_feedback, 'block_reason'):
                        error_msg = f"Safety filter blocked: {response.prompt_feedback.block_reason}"
                        logger.warning(error_msg)
                        
                        if not retry_on_safety_filter:
                            raise ValueError(error_msg)
                        
                        # Mark key as failed and try next one
                        self.key_manager.mark_key_failed(
                            key_info['key_id'],
                            error_type='safety_filter'
                        )
                        last_error = error_msg
                        continue
                
                # Success - mark key as successful
                self.key_manager.mark_key_success(key_info['key_id'])
                
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                
                # Mark current key as failed
                if key_info:
                    self.key_manager.mark_key_failed(
                        key_info['key_id'],
                        error_type=type(e).__name__
                    )
                
                last_error = e
                self.failure_count += 1
                
                # Check if we should retry
                if attempt < self.max_retries - 1:
                    # Wait with exponential backoff
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    # Final attempt failed
                    logger.error(f"All {self.max_retries} attempts failed")
                    raise Exception(f"Request failed after {self.max_retries} attempts: {error_msg}")
        
        # Should never reach here, but just in case
        raise Exception(f"Request failed: {last_error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get router statistics.
        
        Returns:
            Dictionary with request stats
        """
        return {
            'total_requests': self.request_count,
            'total_failures': self.failure_count,
            'success_rate': (self.request_count - self.failure_count) / self.request_count if self.request_count > 0 else 0,
            'key_manager_health': self.key_manager.get_health_status() if hasattr(self.key_manager, 'get_health_status') else {}
        }


# Global singleton instance
_router_instance: Optional[RequestRouter] = None


def get_request_router() -> RequestRouter:
    """
    Get the global RequestRouter instance (singleton pattern).
    
    Returns:
        RequestRouter instance
    """
    global _router_instance
    
    if _router_instance is None:
        _router_instance = RequestRouter()
    
    return _router_instance


# Convenience alias
request_router = get_request_router()
